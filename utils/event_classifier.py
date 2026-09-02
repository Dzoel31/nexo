import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, Literal, Optional
import aiohttp
from pydantic import BaseModel, Field
from sqlalchemy import select

from db.models import ScheduledEvent
from db.session import async_session

logger = logging.getLogger("event_classifier")

LLAMA_SERVER_URL = os.environ.get(
    "LLAMA_SERVER_URL", "http://localhost:8080/v1/chat/completions"
)

EventClassificationLabel = Literal[
    "PUBLIC_EVENT",
    "INTERNAL_MEETING",
    "TRAINING_WORKSHOP",
    "LOGISTICS",
    "LOGISTICS_OPS",
    "DEADLINE",
    "CASUAL_BONDING",
    "WEEKLY_MEETING",
]


class EventClassificationResult(BaseModel):
    label: EventClassificationLabel = Field(
        default="INTERNAL_MEETING",
        description="Category label for the event",
    )
    is_discord_event: bool = Field(
        default=True,
        description="Whether a Discord Scheduled Event should be created",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score (1.0 for fast-path regex, 0.0-1.0 for SLM)",
    )
    source: Literal["db_cache", "fast_path_regex", "slm_fallback", "safe_fallback"] = (
        Field(
            default="fast_path_regex",
            description="Which stage produced the classification",
        )
    )


# ---------------------------------------------------------------------------
# FAST-PATH REGEX PATTERNS (Prioritas 1)
# ---------------------------------------------------------------------------
FAST_PATH_RULES: list[tuple[re.Pattern, EventClassificationLabel, bool]] = [
    # 1. Non-Discord Events (is_discord_event = False)
    (
        re.compile(
            r"\b(TODO|BUY|BELI|BELANJA|LOGISTIK|MAINTENANCE|PERBAIKAN|LAB|INVENTARIS|PENGADAAN)\b",
            re.IGNORECASE,
        ),
        "LOGISTICS_OPS",
        False,
    ),
    (
        re.compile(
            r"\b(DL|DEADLINE|SUBMIT|KUMPULKAN|PENGUMPULAN|BATAS|TENGGAT|DUE DATE)\b",
            re.IGNORECASE,
        ),
        "DEADLINE",
        False,
    ),
    # 2. Discord Events (is_discord_event = True)
    (
        re.compile(
            r"\b(RAPAT|MEETING|SYNC|EVAL|PLENO|COORD|KOORDINASI)\b",
            re.IGNORECASE,
        ),
        "INTERNAL_MEETING",
        True,
    ),
    (
        re.compile(
            r"\b(WORKSHOP|TRAINING|HANDS-ON|BEDAH|TUTORIAL|BOOTCAMP|KULIAH UMUM)\b",
            re.IGNORECASE,
        ),
        "TRAINING_WORKSHOP",
        True,
    ),
    (
        re.compile(
            r"\b(WEBINAR|SEMINAR|OPEN-REC|EXPO|INFO-SESSION|LOMBA|COMPETITION)\b",
            re.IGNORECASE,
        ),
        "PUBLIC_EVENT",
        True,
    ),
    (
        re.compile(
            r"\b(BONDING|SANTAI|NONGKRONG|MAKAN|GATHERING|PLAY|GAME)\b",
            re.IGNORECASE,
        ),
        "CASUAL_BONDING",
        True,
    ),
]


class EventClassifier:
    """
    Hybrid Event Classifier combining:
    1. Database Cache (0 ms)
    2. Fast-Path Regex (0 ms, 0 tokens)
    3. SLM Router Fallback (Gemma 4 via llama-server with 120s timeout)
    4. Deterministic Safe Fallback
    """

    def __init__(self, llama_url: str = LLAMA_SERVER_URL):
        self.llama_url = llama_url

    async def classify_event(
        self,
        summary: str,
        description: Optional[str] = None,
        gcal_id: Optional[str] = None,
    ) -> EventClassificationResult:
        """
        Main classification pipeline for calendar agendas.
        """
        # -------------------------------------------------------------
        # Tahap 1: Database Cache Check (Zero Cost)
        # -------------------------------------------------------------
        if gcal_id:
            try:
                async with async_session() as session:
                    res = await session.execute(
                        select(ScheduledEvent).where(
                            ScheduledEvent.gcal_event_id == gcal_id
                        )
                    )
                    db_ev = res.scalar_one_or_none()
                    if db_ev and db_ev.classification_label:
                        logger.debug(
                            f"[Classifier:CacheHit] {summary} -> {db_ev.classification_label}"
                        )
                        return EventClassificationResult(
                            label=db_ev.classification_label,  # type: ignore
                            is_discord_event=db_ev.is_discord_event,
                            confidence=1.0,
                            source="db_cache",
                        )
            except Exception as db_err:
                logger.warning(
                    f"[Classifier:CacheError] Gagal membaca DB cache untuk gcal_id={gcal_id}: {db_err}"
                )

        # -------------------------------------------------------------
        # Tahap 2: Fast-Path Regex (Prioritas 1)
        # -------------------------------------------------------------
        fast_result = self._match_fast_path(summary)
        if fast_result:
            logger.info(
                f"[Classifier:FastPath] '{summary}' -> {fast_result.label} (is_discord_event={fast_result.is_discord_event})"
            )
            return fast_result

        # -------------------------------------------------------------
        # Tahap 3: SLM Router Fallback (Prioritas 2 - Gemma 4 Inference)
        # -------------------------------------------------------------
        logger.info(
            f"[Classifier:SLMFallback] Memanggil llama-server untuk klasifikasi ambigu: '{summary}'"
        )
        return await self._classify_via_slm(summary, description)

    def _match_fast_path(self, summary: str) -> Optional[EventClassificationResult]:
        """Matches summary string against fast-path prefix regex patterns."""
        cleaned_text = re.sub(r"[\[\]\(\)\{\}:_-]", " ", summary).strip()

        for pattern, label, is_discord in FAST_PATH_RULES:
            if pattern.search(cleaned_text):
                return EventClassificationResult(
                    label=label,
                    is_discord_event=is_discord,
                    confidence=1.0,
                    source="fast_path_regex",
                )
        return None

    async def _classify_via_slm(
        self, summary: str, description: Optional[str] = None
    ) -> EventClassificationResult:
        """
        Sends an isolated 1-shot structured classification request to llama-server.
        Timeout is set to 120s to prevent hanging on high CPU load.
        """
        system_prompt = (
            "Kamu adalah router klasifikasi agenda KSM AIoT. Tugasmu mengklasifikasikan event dan menentukan apakah perlu dibuatkan Discord Scheduled Event.\n\n"
            "Kategori yang tersedia (PILIH SALAH SATU):\n"
            "- PUBLIC_EVENT: Acara terbuka, webinar, expo, lomba, open recruitment.\n"
            "- INTERNAL_MEETING: Rapat pengurus, evaluasi, pleno, koordinasi tim.\n"
            "- TRAINING_WORKSHOP: Pelatihan, workshop teknis, hands-on IoT/AI, bedah riset.\n"
            "- LOGISTICS_OPS: Pembelian alat/komponen, logistik, belanja lab, inventaris, perbaikan alat.\n"
            "- DEADLINE: Batas waktu pengumpulan berkas, submission laporan, LPJ, tugas.\n"
            "- CASUAL_BONDING: Nongkrong, makan bersama, main game, gathering santai.\n\n"
            "Aturan is_discord_event:\n"
            "- TRUE: HANYA jika membutuhkan kehadiran/pertemuan orang secara real-time (rapat, webinar, workshop, bonding).\n"
            "- FALSE: Tugas mandiri, belanja fisik, logistik lab, maintenance, atau deadline pengumpulan berkas.\n\n"
            "Kembalikan JSON valid saja dengan format persis:\n"
            '{"label": "KATEGORI", "is_discord_event": true/false}'
        )

        user_content = f"Nama Agenda: {summary}"
        if description and description.strip():
            user_content += f"\nDeskripsi: {description[:200]}"

        payload: Dict[str, Any] = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Nama Agenda: Rapat Koordinasi Divisi AI",
                },
                {
                    "role": "assistant",
                    "content": '{"label": "INTERNAL_MEETING", "is_discord_event": true}',
                },
                {
                    "role": "user",
                    "content": "Nama Agenda: Beli kabel jumper & ESP32 di Glodok",
                },
                {
                    "role": "assistant",
                    "content": '{"label": "LOGISTICS_OPS", "is_discord_event": false}',
                },
                {
                    "role": "user",
                    "content": "Nama Agenda: Batas Pengumpulan Proposal Riset",
                },
                {
                    "role": "assistant",
                    "content": '{"label": "DEADLINE", "is_discord_event": false}',
                },
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "max_tokens": 80,
            "response_format": {"type": "json_object"},
        }

        try:
            # Menggunakan ClientTimeout(total=120.0) sesuai rekomendasi keamanan CPU
            timeout = aiohttp.ClientTimeout(total=120.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.llama_url, json=payload) as response:
                    if response.status != 200:
                        raw_body = await response.text()
                        logger.warning(
                            f"[Classifier:SLMError] llama-server HTTP {response.status}: {raw_body}"
                        )
                        return self._safe_fallback(summary)

                    data = await response.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

                    # Ekstrak JSON block dari content
                    json_str = self._extract_json(content)
                    parsed = json.loads(json_str)

                    label_val = str(parsed.get("label", "INTERNAL_MEETING")).upper()
                    if label_val not in [
                        "PUBLIC_EVENT",
                        "INTERNAL_MEETING",
                        "TRAINING_WORKSHOP",
                        "LOGISTICS_OPS",
                        "DEADLINE",
                        "CASUAL_BONDING",
                    ]:
                        label_val = "INTERNAL_MEETING"

                    is_discord = bool(parsed.get("is_discord_event", False))

                    logger.info(
                        f"[Classifier:SLMSuccess] '{summary}' -> {label_val} (is_discord_event={is_discord})"
                    )
                    return EventClassificationResult(
                        label=label_val,  # type: ignore
                        is_discord_event=is_discord,
                        confidence=0.85,
                        source="slm_fallback",
                    )
        except asyncio.TimeoutError:
            logger.warning(
                f"[Classifier:Timeout] Inferensi LLM melebihi 120s untuk '{summary}'. Menggunakan fallback aman."
            )
            return self._safe_fallback(summary)
        except Exception as e:
            logger.warning(
                f"[Classifier:Exception] Gagal memproses SLM classification untuk '{summary}': {e}"
            )
            return self._safe_fallback(summary)

    def _extract_json(self, text: str) -> str:
        """Extracts JSON object string enclosed in markdown fences or curly braces."""
        text = text.strip()
        if "```json" in text:
            match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                return match.group(1)
        if "```" in text:
            match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                return match.group(1)
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    def _safe_fallback(self, summary: str) -> EventClassificationResult:
        """Deterministic safe fallback when SLM inference fails or times out."""
        logger.info(
            f"[Classifier:SafeFallback] Menerapkan default aman untuk '{summary}'"
        )
        return EventClassificationResult(
            label="INTERNAL_MEETING",
            is_discord_event=False,
            confidence=0.5,
            source="safe_fallback",
        )


# Singleton classifier instance
default_event_classifier = EventClassifier()
