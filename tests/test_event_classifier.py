from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.event_classifier import EventClassifier


@pytest.mark.asyncio
async def test_fast_path_logistics_non_event():
    classifier = EventClassifier()

    test_cases = [
        "TODO: Beli kabel jumper dan sensor DHT22",
        "[LOGISTIK] Pembelian resin 3D print",
        "Maintenance server lab IoT",
        "Inventaris alat lab",
    ]
    for case in test_cases:
        res = await classifier.classify_event(case)
        assert res.label == "LOGISTICS_OPS"
        assert res.is_discord_event is False
        assert res.source == "fast_path_regex"


@pytest.mark.asyncio
async def test_fast_path_deadline_non_event():
    classifier = EventClassifier()

    test_cases = [
        "[DL] Pengumpulan Laporan Akhir Proker",
        "Deadline Submit Proposal PKM",
        "Batas Pengumpulan Berkas Beasiswa",
    ]
    for case in test_cases:
        res = await classifier.classify_event(case)
        assert res.label == "DEADLINE"
        assert res.is_discord_event is False
        assert res.source == "fast_path_regex"


@pytest.mark.asyncio
async def test_fast_path_discord_events():
    classifier = EventClassifier()

    cases = [
        ("Rapat Pleno Pengurus KSM", "INTERNAL_MEETING", True),
        ("Workshop IoT Hands-on ESP32", "TRAINING_WORKSHOP", True),
        ("Webinar Nasional AI & Robotics", "PUBLIC_EVENT", True),
        ("Nongkrong Santai Bareng Anggota Baru", "CASUAL_BONDING", True),
    ]
    for text, expected_label, expected_is_event in cases:
        res = await classifier.classify_event(text)
        assert res.label == expected_label
        assert res.is_discord_event is expected_is_event
        assert res.source == "fast_path_regex"


@pytest.mark.asyncio
async def test_slm_fallback_success():
    classifier = EventClassifier()
    ambiguous_title = "Diskusi Roadmap Q3 di Discord"

    mock_response = MagicMock()
    mock_response.choices[
        0
    ].message.content = '{"label": "INTERNAL_MEETING", "is_discord_event": true}'

    with patch.object(
        classifier.ai_client.chat.completions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        res = await classifier.classify_event(ambiguous_title)
        assert res.label == "INTERNAL_MEETING"
        assert res.is_discord_event is True
        assert res.source == "slm_fallback"


@pytest.mark.asyncio
async def test_slm_fallback_timeout_safe_fallback():
    classifier = EventClassifier()
    ambiguous_title = "Agenda Tanpa Nama Jelas"

    with patch.object(
        classifier.ai_client.chat.completions,
        "create",
        new_callable=AsyncMock,
        side_effect=TimeoutError(),
    ):
        res = await classifier.classify_event(ambiguous_title)
        assert res.label == "INTERNAL_MEETING"
        assert res.is_discord_event is False
        assert res.source == "safe_fallback"
