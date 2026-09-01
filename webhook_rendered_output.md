# 📋 Hasil Render Template Webhook Discord (Modernized UX: Embed + Action Buttons)
Dokumen ini menampilkan hasil render dari seluruh payload asli GitHub (`data/payloads/`) dengan **normalisasi whitespace** dan penambahan **Discord Action Link Buttons**.

---
## 🔹 Event: `release` (GitHub Release Event)
- **File Sumber Payload:** `data/payloads/release.json`
- **Template Jinja:** `templates/release_message.j2`
- **Total Payload Diterima:** 3

### 📦 Entri #1

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Release Notification**
Repo: **ksm-aiot-upnvj/nexo** | Release: `1.10.0`
```

**Embed Card:**
- **Title:** [📦 Release 1.10.0 (nexo)](https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0)
- **Border Color:** `3066993`
- **Author:** KSM-AIoT
- **Description (Compact Markdown Body):**

## v1.10.0 (2026-09-01)

### Bug Fixes

- **gateway**: Filter duplicate cd triggers and unescape jinja templates ([`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db))
- **orchestrator**: Prevent worker silent death and isolate tool execution errors ([`36ab76d`](https://github.com/ksm-aiot-upnvj/nexo/commit/36ab76df34cd507d3c9344730a5e9255f54c367e))

### Features

- **agent**: Add end_discord_poll tool, integrate db memory, and compact tool menu ([`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7))
- **conversation**: Implement 24-hour sliding TTL context expiration and graceful error handling ([`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac))

- **db**: Implement async postgresql persistence, alembic migrations, and token compaction ([`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5))
- **events**: Enforce WIB timezone, role mention footers, and broadcast AllowedMentions ([`4e1223d`](https://github.com/ksm-aiot-upnvj/nexo/commit/4e1223de32a255db4bfd99af9e74bc7eff17b198))

- **events**: Implement persistent discord event lifecycle, auto-reminder scheduler, and auto-management ([`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2))
- **tokens**: Implement true LRU token cache, usage analytics, UX feedback, and auto-migration entrypoint ([`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1))

### Performance Improvements

- **agent**: Sanitize tool schema and reduce context token footprint ([`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56))

---

**Detailed Changes**: [1.9.0...1.10.0](https://github.com/ksm-aiot-upnvj/nexo/compare/1.9.0...1.10.0)

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Version` | `1.10.0` | `True` |
| `Status` | ✅ Released | `True` |
| `Author` | KSM-AIoT | `True` |
| `Prerelease` | No | `True` |
| `Published At` | 2026-09-01T06:45:20Z | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[📦 View Release]` (https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Release Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Release: `1.10.0`",
  "embeds": [
    {
      "title": "📦 Release 1.10.0 (nexo)",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0",
      "description": "## v1.10.0 (2026-09-01)\n\n### Bug Fixes\n\n- **gateway**: Filter duplicate cd triggers and unescape jinja templates ([`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db))\n- **orchestrator**: Prevent worker silent death and isolate tool execution errors ([`36ab76d`](https://github.com/ksm-aiot-upnvj/nexo/commit/36ab76df34cd507d3c9344730a5e9255f54c367e))\n\n### Features\n\n- **agent**: Add end_discord_poll tool, integrate db memory, and compact tool menu ([`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7))\n- **conversation**: Implement 24-hour sliding TTL context expiration and graceful error handling ([`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac))\n\n- **db**: Implement async postgresql persistence, alembic migrations, and token compaction ([`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5))\n- **events**: Enforce WIB timezone, role mention footers, and broadcast AllowedMentions ([`4e1223d`](https://github.com/ksm-aiot-upnvj/nexo/commit/4e1223de32a255db4bfd99af9e74bc7eff17b198))\n\n- **events**: Implement persistent discord event lifecycle, auto-reminder scheduler, and auto-management ([`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2))\n- **tokens**: Implement true LRU token cache, usage analytics, UX feedback, and auto-migration entrypoint ([`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1))\n\n### Performance Improvements\n\n- **agent**: Sanitize tool schema and reduce context token footprint ([`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56))\n\n---\n\n**Detailed Changes**: [1.9.0...1.10.0](https://github.com/ksm-aiot-upnvj/nexo/compare/1.9.0...1.10.0)",
      "color": 3066993,
      "author": {
        "name": "KSM-AIoT",
        "icon_url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Version",
          "value": "`1.10.0`",
          "inline": true
        },
        {
          "name": "Status",
          "value": "✅ Released",
          "inline": true
        },
        {
          "name": "Author",
          "value": "KSM-AIoT",
          "inline": true
        },
        {
          "name": "Prerelease",
          "value": "No",
          "inline": true
        },
        {
          "name": "Published At",
          "value": "2026-09-01T06:45:20Z",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T06:45:20Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "View Release",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0",
          "emoji": {
            "name": "📦"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #2

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Release Notification**
Repo: **ksm-aiot-upnvj/nexo** | Release: `1.10.0`
```

**Embed Card:**
- **Title:** [📦 Release 1.10.0 (nexo)](https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0)
- **Border Color:** `3066993`
- **Author:** KSM-AIoT
- **Description (Compact Markdown Body):**

## v1.10.0 (2026-09-01)

### Bug Fixes

- **gateway**: Filter duplicate cd triggers and unescape jinja templates ([`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db))
- **orchestrator**: Prevent worker silent death and isolate tool execution errors ([`36ab76d`](https://github.com/ksm-aiot-upnvj/nexo/commit/36ab76df34cd507d3c9344730a5e9255f54c367e))

### Features

- **agent**: Add end_discord_poll tool, integrate db memory, and compact tool menu ([`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7))
- **conversation**: Implement 24-hour sliding TTL context expiration and graceful error handling ([`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac))

- **db**: Implement async postgresql persistence, alembic migrations, and token compaction ([`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5))
- **events**: Enforce WIB timezone, role mention footers, and broadcast AllowedMentions ([`4e1223d`](https://github.com/ksm-aiot-upnvj/nexo/commit/4e1223de32a255db4bfd99af9e74bc7eff17b198))

- **events**: Implement persistent discord event lifecycle, auto-reminder scheduler, and auto-management ([`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2))
- **tokens**: Implement true LRU token cache, usage analytics, UX feedback, and auto-migration entrypoint ([`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1))

### Performance Improvements

- **agent**: Sanitize tool schema and reduce context token footprint ([`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56))

---

**Detailed Changes**: [1.9.0...1.10.0](https://github.com/ksm-aiot-upnvj/nexo/compare/1.9.0...1.10.0)

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Version` | `1.10.0` | `True` |
| `Status` | ✅ Released | `True` |
| `Author` | KSM-AIoT | `True` |
| `Prerelease` | No | `True` |
| `Published At` | 2026-09-01T06:45:20Z | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[📦 View Release]` (https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Release Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Release: `1.10.0`",
  "embeds": [
    {
      "title": "📦 Release 1.10.0 (nexo)",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0",
      "description": "## v1.10.0 (2026-09-01)\n\n### Bug Fixes\n\n- **gateway**: Filter duplicate cd triggers and unescape jinja templates ([`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db))\n- **orchestrator**: Prevent worker silent death and isolate tool execution errors ([`36ab76d`](https://github.com/ksm-aiot-upnvj/nexo/commit/36ab76df34cd507d3c9344730a5e9255f54c367e))\n\n### Features\n\n- **agent**: Add end_discord_poll tool, integrate db memory, and compact tool menu ([`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7))\n- **conversation**: Implement 24-hour sliding TTL context expiration and graceful error handling ([`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac))\n\n- **db**: Implement async postgresql persistence, alembic migrations, and token compaction ([`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5))\n- **events**: Enforce WIB timezone, role mention footers, and broadcast AllowedMentions ([`4e1223d`](https://github.com/ksm-aiot-upnvj/nexo/commit/4e1223de32a255db4bfd99af9e74bc7eff17b198))\n\n- **events**: Implement persistent discord event lifecycle, auto-reminder scheduler, and auto-management ([`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2))\n- **tokens**: Implement true LRU token cache, usage analytics, UX feedback, and auto-migration entrypoint ([`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1))\n\n### Performance Improvements\n\n- **agent**: Sanitize tool schema and reduce context token footprint ([`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56))\n\n---\n\n**Detailed Changes**: [1.9.0...1.10.0](https://github.com/ksm-aiot-upnvj/nexo/compare/1.9.0...1.10.0)",
      "color": 3066993,
      "author": {
        "name": "KSM-AIoT",
        "icon_url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Version",
          "value": "`1.10.0`",
          "inline": true
        },
        {
          "name": "Status",
          "value": "✅ Released",
          "inline": true
        },
        {
          "name": "Author",
          "value": "KSM-AIoT",
          "inline": true
        },
        {
          "name": "Prerelease",
          "value": "No",
          "inline": true
        },
        {
          "name": "Published At",
          "value": "2026-09-01T06:45:20Z",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T06:45:20Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "View Release",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0",
          "emoji": {
            "name": "📦"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #3

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Release Notification**
Repo: **ksm-aiot-upnvj/nexo** | Release: `1.10.0`
```

**Embed Card:**
- **Title:** [📦 Release 1.10.0 (nexo)](https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0)
- **Border Color:** `3066993`
- **Author:** KSM-AIoT
- **Description (Compact Markdown Body):**

## v1.10.0 (2026-09-01)

### Bug Fixes

- **gateway**: Filter duplicate cd triggers and unescape jinja templates ([`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db))
- **orchestrator**: Prevent worker silent death and isolate tool execution errors ([`36ab76d`](https://github.com/ksm-aiot-upnvj/nexo/commit/36ab76df34cd507d3c9344730a5e9255f54c367e))

### Features

- **agent**: Add end_discord_poll tool, integrate db memory, and compact tool menu ([`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7))
- **conversation**: Implement 24-hour sliding TTL context expiration and graceful error handling ([`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac))

- **db**: Implement async postgresql persistence, alembic migrations, and token compaction ([`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5))
- **events**: Enforce WIB timezone, role mention footers, and broadcast AllowedMentions ([`4e1223d`](https://github.com/ksm-aiot-upnvj/nexo/commit/4e1223de32a255db4bfd99af9e74bc7eff17b198))

- **events**: Implement persistent discord event lifecycle, auto-reminder scheduler, and auto-management ([`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2))
- **tokens**: Implement true LRU token cache, usage analytics, UX feedback, and auto-migration entrypoint ([`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1))

### Performance Improvements

- **agent**: Sanitize tool schema and reduce context token footprint ([`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56))

---

**Detailed Changes**: [1.9.0...1.10.0](https://github.com/ksm-aiot-upnvj/nexo/compare/1.9.0...1.10.0)

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Version` | `1.10.0` | `True` |
| `Status` | ✅ Released | `True` |
| `Author` | KSM-AIoT | `True` |
| `Prerelease` | No | `True` |
| `Published At` | 2026-09-01T06:45:20Z | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[📦 View Release]` (https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Release Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Release: `1.10.0`",
  "embeds": [
    {
      "title": "📦 Release 1.10.0 (nexo)",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0",
      "description": "## v1.10.0 (2026-09-01)\n\n### Bug Fixes\n\n- **gateway**: Filter duplicate cd triggers and unescape jinja templates ([`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db))\n- **orchestrator**: Prevent worker silent death and isolate tool execution errors ([`36ab76d`](https://github.com/ksm-aiot-upnvj/nexo/commit/36ab76df34cd507d3c9344730a5e9255f54c367e))\n\n### Features\n\n- **agent**: Add end_discord_poll tool, integrate db memory, and compact tool menu ([`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7))\n- **conversation**: Implement 24-hour sliding TTL context expiration and graceful error handling ([`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac))\n\n- **db**: Implement async postgresql persistence, alembic migrations, and token compaction ([`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5))\n- **events**: Enforce WIB timezone, role mention footers, and broadcast AllowedMentions ([`4e1223d`](https://github.com/ksm-aiot-upnvj/nexo/commit/4e1223de32a255db4bfd99af9e74bc7eff17b198))\n\n- **events**: Implement persistent discord event lifecycle, auto-reminder scheduler, and auto-management ([`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2))\n- **tokens**: Implement true LRU token cache, usage analytics, UX feedback, and auto-migration entrypoint ([`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1))\n\n### Performance Improvements\n\n- **agent**: Sanitize tool schema and reduce context token footprint ([`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56))\n\n---\n\n**Detailed Changes**: [1.9.0...1.10.0](https://github.com/ksm-aiot-upnvj/nexo/compare/1.9.0...1.10.0)",
      "color": 3066993,
      "author": {
        "name": "KSM-AIoT",
        "icon_url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Version",
          "value": "`1.10.0`",
          "inline": true
        },
        {
          "name": "Status",
          "value": "✅ Released",
          "inline": true
        },
        {
          "name": "Author",
          "value": "KSM-AIoT",
          "inline": true
        },
        {
          "name": "Prerelease",
          "value": "No",
          "inline": true
        },
        {
          "name": "Published At",
          "value": "2026-09-01T06:45:20Z",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T06:45:20Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "View Release",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.10.0",
          "emoji": {
            "name": "📦"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

## 🔹 Event: `push` (GitHub Push Event)
- **File Sumber Payload:** `data/payloads/push.json`
- **Template Jinja:** `templates/push_message.j2`
- **Total Payload Diterima:** 5

### 📦 Entri #1

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Push Notification**
Repo: **ksm-aiot-upnvj/nexo** | Branch: `refs/tags/1.10.0`
```

**Embed Card:**
- **Title:** [🚀 New push to ksm-aiot-upnvj/nexo](https://github.com/ksm-aiot-upnvj/nexo/compare/1.10.0)
- **Border Color:** `3066993`
- **Author:** github-actions[bot]
- **Description (Compact Markdown Body):**

**Update Reference (Tag/Merge):**
• [`095dd62`](https://github.com/ksm-aiot-upnvj/nexo/commit/095dd62e88ea787b0516b76fae7f3d8dfb02e93d) - chore(release): bump to 1.10.0

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Branch / Ref` | `refs/tags/1.10.0` | `True` |
| `Total Commits` | 0 | `True` |
| `Pusher` | github-actions[bot] | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[🔍 Compare Commit (Diff)]` (https://github.com/ksm-aiot-upnvj/nexo/compare/1.10.0) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Push Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Branch: `refs/tags/1.10.0`",
  "embeds": [
    {
      "title": "🚀 New push to ksm-aiot-upnvj/nexo",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/1.10.0",
      "description": "**Update Reference (Tag/Merge):**\n• [`095dd62`](https://github.com/ksm-aiot-upnvj/nexo/commit/095dd62e88ea787b0516b76fae7f3d8dfb02e93d) - chore(release): bump to 1.10.0",
      "color": 3066993,
      "author": {
        "name": "github-actions[bot]",
        "icon_url": "https://avatars.githubusercontent.com/in/15368?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Branch / Ref",
          "value": "`refs/tags/1.10.0`",
          "inline": true
        },
        {
          "name": "Total Commits",
          "value": "0",
          "inline": true
        },
        {
          "name": "Pusher",
          "value": "github-actions[bot]",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/in/15368?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T06:45:17Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "Compare Commit (Diff)",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/1.10.0",
          "emoji": {
            "name": "🔍"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #2

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Push Notification**
Repo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`
```

**Embed Card:**
- **Title:** [🚀 New push to ksm-aiot-upnvj/nexo](https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273)
- **Border Color:** `3447003`
- **Author:** Dzoel31
- **Description (Compact Markdown Body):**

**Dzoel31** pushed **14** new commit(s):
• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*
• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*
• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*
• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*
• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*
• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*
• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*
• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*
• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*
• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*

... and 4 other commit(s).

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Branch / Ref` | `refs/heads/main` | `True` |
| `Total Commits` | 14 | `True` |
| `Pusher` | Dzoel31 | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[🔍 Compare Commit (Diff)]` (https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Push Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`",
  "embeds": [
    {
      "title": "🚀 New push to ksm-aiot-upnvj/nexo",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
      "description": "**Dzoel31** pushed **14** new commit(s):\n• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*\n• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*\n• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*\n• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*\n• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*\n• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*\n• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*\n• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*\n• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*\n• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*\n\n... and 4 other commit(s).",
      "color": 3447003,
      "author": {
        "name": "Dzoel31",
        "icon_url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Branch / Ref",
          "value": "`refs/heads/main`",
          "inline": true
        },
        {
          "name": "Total Commits",
          "value": "14",
          "inline": true
        },
        {
          "name": "Pusher",
          "value": "Dzoel31",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T13:44:06+07:00"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "Compare Commit (Diff)",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
          "emoji": {
            "name": "🔍"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #3

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Push Notification**
Repo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`
```

**Embed Card:**
- **Title:** [🚀 New push to ksm-aiot-upnvj/nexo](https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273)
- **Border Color:** `3447003`
- **Author:** Dzoel31
- **Description (Compact Markdown Body):**

**Dzoel31** pushed **14** new commit(s):
• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*
• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*
• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*
• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*
• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*
• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*
• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*
• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*
• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*
• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*

... and 4 other commit(s).

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Branch / Ref` | `refs/heads/main` | `True` |
| `Total Commits` | 14 | `True` |
| `Pusher` | Dzoel31 | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[🔍 Compare Commit (Diff)]` (https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Push Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`",
  "embeds": [
    {
      "title": "🚀 New push to ksm-aiot-upnvj/nexo",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
      "description": "**Dzoel31** pushed **14** new commit(s):\n• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*\n• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*\n• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*\n• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*\n• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*\n• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*\n• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*\n• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*\n• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*\n• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*\n\n... and 4 other commit(s).",
      "color": 3447003,
      "author": {
        "name": "Dzoel31",
        "icon_url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Branch / Ref",
          "value": "`refs/heads/main`",
          "inline": true
        },
        {
          "name": "Total Commits",
          "value": "14",
          "inline": true
        },
        {
          "name": "Pusher",
          "value": "Dzoel31",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T13:44:06+07:00"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "Compare Commit (Diff)",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
          "emoji": {
            "name": "🔍"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #4

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Push Notification**
Repo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`
```

**Embed Card:**
- **Title:** [🚀 New push to ksm-aiot-upnvj/nexo](https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273)
- **Border Color:** `3447003`
- **Author:** Dzoel31
- **Description (Compact Markdown Body):**

**Dzoel31** pushed **14** new commit(s):
• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*
• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*
• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*
• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*
• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*
• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*
• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*
• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*
• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*
• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*

... and 4 other commit(s).

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Branch / Ref` | `refs/heads/main` | `True` |
| `Total Commits` | 14 | `True` |
| `Pusher` | Dzoel31 | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[🔍 Compare Commit (Diff)]` (https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Push Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`",
  "embeds": [
    {
      "title": "🚀 New push to ksm-aiot-upnvj/nexo",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
      "description": "**Dzoel31** pushed **14** new commit(s):\n• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*\n• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*\n• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*\n• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*\n• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*\n• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*\n• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*\n• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*\n• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*\n• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*\n\n... and 4 other commit(s).",
      "color": 3447003,
      "author": {
        "name": "Dzoel31",
        "icon_url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Branch / Ref",
          "value": "`refs/heads/main`",
          "inline": true
        },
        {
          "name": "Total Commits",
          "value": "14",
          "inline": true
        },
        {
          "name": "Pusher",
          "value": "Dzoel31",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T13:44:06+07:00"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "Compare Commit (Diff)",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
          "emoji": {
            "name": "🔍"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #5

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Push Notification**
Repo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`
```

**Embed Card:**
- **Title:** [🚀 New push to ksm-aiot-upnvj/nexo](https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273)
- **Border Color:** `3447003`
- **Author:** Dzoel31
- **Description (Compact Markdown Body):**

**Dzoel31** pushed **14** new commit(s):
• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*
• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*
• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*
• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*
• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*
• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*
• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*
• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*
• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*
• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*

... and 4 other commit(s).

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Branch / Ref` | `refs/heads/main` | `True` |
| `Total Commits` | 14 | `True` |
| `Pusher` | Dzoel31 | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[🔍 Compare Commit (Diff)]` (https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273) &nbsp; | &nbsp; `[📂 Repository]` (https://github.com/ksm-aiot-upnvj/nexo)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Push Notification**\nRepo: **ksm-aiot-upnvj/nexo** | Branch: `refs/heads/main`",
  "embeds": [
    {
      "title": "🚀 New push to ksm-aiot-upnvj/nexo",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
      "description": "**Dzoel31** pushed **14** new commit(s):\n• [`e3c5fb2`](https://github.com/ksm-aiot-upnvj/nexo/commit/e3c5fb2ac92982dafe9a3f5cc1a6594745c620cc) Merge pull request #1 from ksm-aiot-upnvj/main — *Dzulfikri Adjmal*\n• [`98777e3`](https://github.com/ksm-aiot-upnvj/nexo/commit/98777e325a71fe7e8fa944bf38de7eb1b9e533db) fix(gateway): filter duplicate cd triggers and unescape... — *Dzoel31*\n• [`4f2d449`](https://github.com/ksm-aiot-upnvj/nexo/commit/4f2d449436dbbe27a83c542b2c7eb90b0fde8cd5) feat(db): implement async postgresql persistence,... — *Dzoel31*\n• [`277cae7`](https://github.com/ksm-aiot-upnvj/nexo/commit/277cae7ed2a59c3876dde1496499505ca3fca9b7) feat(agent): add end_discord_poll tool, integrate db... — *Dzoel31*\n• [`448e22d`](https://github.com/ksm-aiot-upnvj/nexo/commit/448e22deb3a8b0ebdb57164110891d10df9ef273) refactor(templates): simplify footer text in github... — *Dzoel31*\n• [`1d6ef27`](https://github.com/ksm-aiot-upnvj/nexo/commit/1d6ef275dd33235604c61af6b2544234ed0caf56) perf(agent): sanitize tool schema and reduce context... — *Dzoel31*\n• [`7e00bd2`](https://github.com/ksm-aiot-upnvj/nexo/commit/7e00bd2f2740196619d018947a3af031ea7634f2) feat(events): implement persistent discord event... — *Dzoel31*\n• [`1ff5d1a`](https://github.com/ksm-aiot-upnvj/nexo/commit/1ff5d1a3fa5484eadf3d82c34c412961508cc7b1) feat(tokens): implement true LRU token cache, usage... — *Dzoel31*\n• [`007d2ef`](https://github.com/ksm-aiot-upnvj/nexo/commit/007d2ef8633d62212d59fb8509ec6ee9c639c4ac) feat(conversation): implement 24-hour sliding TTL... — *Dzoel31*\n• [`d182d38`](https://github.com/ksm-aiot-upnvj/nexo/commit/d182d38060921757e65c6f8b07dc6a989a1d1774) security(prompt): fortify system prompt against prompt... — *Dzoel31*\n\n... and 4 other commit(s).",
      "color": 3447003,
      "author": {
        "name": "Dzoel31",
        "icon_url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Branch / Ref",
          "value": "`refs/heads/main`",
          "inline": true
        },
        {
          "name": "Total Commits",
          "value": "14",
          "inline": true
        },
        {
          "name": "Pusher",
          "value": "Dzoel31",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/82845859?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-09-01T13:44:06+07:00"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "Compare Commit (Diff)",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/compare/e1776c806d22...0da7eacc9273",
          "emoji": {
            "name": "🔍"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Repository",
          "url": "https://github.com/ksm-aiot-upnvj/nexo",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

## 🔹 Event: `pull_request` (GitHub Pull Request Event)
- **File Sumber Payload:** `data/payloads/pull_request.json`
- **Template Jinja:** `templates/pull_request_message.j2`
- **Total Payload Diterima:** 2

### 📦 Entri #1

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Pull Request Notification**
Repo: **ksm-aiot-upnvj/orion-frontend** | Branch: `bima/fix-ui`
```

**Embed Card:**
- **Title:** [🔍 Pull Request #1: Fix ui web](https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1)
- **Border Color:** `7291585`
- **Author:** Eunbimz
- **Description (Compact Markdown Body):**

Pull Request **#1** has been **closed** by **Eunbimz**.

**📝 Title:** Fix ui web

**📄 Description:**
No PR description provided.

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/orion-frontend | `True` |
| `Branch` | `bima/fix-ui` ➔ `main` | `True` |
| `Action Status` | Closed | `True` |
| `Lines Changed` | 🟢 +721 | 🔴 -256 | `True` |
| `Total Commits` | 1 | `True` |
| `Files Changed` | 12 | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[🔍 Review Pull Request]` (https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1) &nbsp; | &nbsp; `[📂 View Diff Files]` (https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1/files)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Pull Request Notification**\nRepo: **ksm-aiot-upnvj/orion-frontend** | Branch: `bima/fix-ui`",
  "embeds": [
    {
      "title": "🔍 Pull Request #1: Fix ui web",
      "url": "https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1",
      "description": "Pull Request **#1** has been **closed** by **Eunbimz**.\n\n**📝 Title:** Fix ui web\n\n**📄 Description:**\nNo PR description provided.",
      "color": 7291585,
      "author": {
        "name": "Eunbimz",
        "icon_url": "https://avatars.githubusercontent.com/u/200245610?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/orion-frontend",
          "inline": true
        },
        {
          "name": "Branch",
          "value": "`bima/fix-ui` ➔ `main`",
          "inline": true
        },
        {
          "name": "Action Status",
          "value": "Closed",
          "inline": true
        },
        {
          "name": "Lines Changed",
          "value": "🟢 +721 | 🔴 -256",
          "inline": true
        },
        {
          "name": "Total Commits",
          "value": "1",
          "inline": true
        },
        {
          "name": "Files Changed",
          "value": "12",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/200245610?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-08-30T10:47:18Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "Review Pull Request",
          "url": "https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1",
          "emoji": {
            "name": "🔍"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "View Diff Files",
          "url": "https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1/files",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #2

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
🚀 **GitHub Pull Request Notification**
Repo: **ksm-aiot-upnvj/orion-frontend** | Branch: `bima/fix-ui`
```

**Embed Card:**
- **Title:** [🔍 Pull Request #1: Fix ui web](https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1)
- **Border Color:** `7291585`
- **Author:** Eunbimz
- **Description (Compact Markdown Body):**

Pull Request **#1** has been **closed** by **Eunbimz**.

**📝 Title:** Fix ui web

**📄 Description:**
No PR description provided.

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/orion-frontend | `True` |
| `Branch` | `bima/fix-ui` ➔ `main` | `True` |
| `Action Status` | Closed | `True` |
| `Lines Changed` | 🟢 +721 | 🔴 -256 | `True` |
| `Total Commits` | 1 | `True` |
| `Files Changed` | 12 | `True` |

- **Footer:** Nexo GitHub Service • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[🔍 Review Pull Request]` (https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1) &nbsp; | &nbsp; `[📂 View Diff Files]` (https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1/files)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "🚀 **GitHub Pull Request Notification**\nRepo: **ksm-aiot-upnvj/orion-frontend** | Branch: `bima/fix-ui`",
  "embeds": [
    {
      "title": "🔍 Pull Request #1: Fix ui web",
      "url": "https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1",
      "description": "Pull Request **#1** has been **closed** by **Eunbimz**.\n\n**📝 Title:** Fix ui web\n\n**📄 Description:**\nNo PR description provided.",
      "color": 7291585,
      "author": {
        "name": "Eunbimz",
        "icon_url": "https://avatars.githubusercontent.com/u/200245610?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/orion-frontend",
          "inline": true
        },
        {
          "name": "Branch",
          "value": "`bima/fix-ui` ➔ `main`",
          "inline": true
        },
        {
          "name": "Action Status",
          "value": "Closed",
          "inline": true
        },
        {
          "name": "Lines Changed",
          "value": "🟢 +721 | 🔴 -256",
          "inline": true
        },
        {
          "name": "Total Commits",
          "value": "1",
          "inline": true
        },
        {
          "name": "Files Changed",
          "value": "12",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/200245610?v=4"
      },
      "footer": {
        "text": "Nexo GitHub Service • KSM AIoT"
      },
      "timestamp": "2026-08-30T10:47:18Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "Review Pull Request",
          "url": "https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1",
          "emoji": {
            "name": "🔍"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "View Diff Files",
          "url": "https://github.com/ksm-aiot-upnvj/orion-frontend/pull/1/files",
          "emoji": {
            "name": "📂"
          }
        }
      ]
    }
  ]
}
```

---

## 🔹 Event: `workflow_run` (GitHub Workflow Run (Actions) Event)
- **File Sumber Payload:** `data/payloads/workflow_run.json`
- **Template Jinja:** `templates/workflow_run_message.j2`
- **Total Payload Diterima:** 2

### 📦 Entri #1

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
✅ **GitHub Actions:** `Build & Push on Release` (success)
Repo: **ksm-aiot-upnvj/nexo**
```

**Embed Card:**
- **Title:** [⚡ Build & Push on Release #16 (nexo)](https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927)
- **Border Color:** `4437377`
- **Author:** KSM-AIoT
- **Description (Compact Markdown Body):**

Workflow **Build & Push on Release** is **success**.

**📝 Commit / Trigger:**
```text
chore(release): bump to 1.10.0
```

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Branch / Ref` | `1.10.0` | `True` |
| `Run Number` | #16 | `True` |
| `Status` | Completed | `True` |
| `Conclusion` | Success | `True` |
| `Triggered By` | KSM-AIoT | `True` |

- **Footer:** Nexo CI/CD Pipeline • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[📜 View Run Logs]` (https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927) &nbsp; | &nbsp; `[⚙️ Workflow File]` (https://github.com/ksm-aiot-upnvj/nexo/blob/1.10.0/.github/workflows/docker-push.yml)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "✅ **GitHub Actions:** `Build & Push on Release` (success)\nRepo: **ksm-aiot-upnvj/nexo**",
  "embeds": [
    {
      "title": "⚡ Build & Push on Release #16 (nexo)",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927",
      "description": "Workflow **Build & Push on Release** is **success**.\n\n**📝 Commit / Trigger:**\n```text\nchore(release): bump to 1.10.0\n```",
      "color": 4437377,
      "author": {
        "name": "KSM-AIoT",
        "icon_url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Branch / Ref",
          "value": "`1.10.0`",
          "inline": true
        },
        {
          "name": "Run Number",
          "value": "#16",
          "inline": true
        },
        {
          "name": "Status",
          "value": "Completed",
          "inline": true
        },
        {
          "name": "Conclusion",
          "value": "Success",
          "inline": true
        },
        {
          "name": "Triggered By",
          "value": "KSM-AIoT",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/297131769?v=4?s=64"
      },
      "footer": {
        "text": "Nexo CI/CD Pipeline • KSM AIoT"
      },
      "timestamp": "2026-09-01T06:47:15Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "View Run Logs",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927",
          "emoji": {
            "name": "📜"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Workflow File",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/blob/1.10.0/.github/workflows/docker-push.yml",
          "emoji": {
            "name": "⚙️"
          }
        }
      ]
    }
  ]
}
```

---

### 📦 Entri #2

#### 1. Preview Tampilan Pesan Discord
**Content / Notification Header:**
```text
✅ **GitHub Actions:** `Build & Push on Release` (success)
Repo: **ksm-aiot-upnvj/nexo**
```

**Embed Card:**
- **Title:** [⚡ Build & Push on Release #16 (nexo)](https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927)
- **Border Color:** `4437377`
- **Author:** KSM-AIoT
- **Description (Compact Markdown Body):**

Workflow **Build & Push on Release** is **success**.

**📝 Commit / Trigger:**
```text
chore(release): bump to 1.10.0
```

**Embed Fields:**

| Nama Field | Nilai Field | Inline |
| :--- | :--- | :---: |
| `Repository` | ksm-aiot-upnvj/nexo | `True` |
| `Branch / Ref` | `1.10.0` | `True` |
| `Run Number` | #16 | `True` |
| `Status` | Completed | `True` |
| `Conclusion` | Success | `True` |
| `Triggered By` | KSM-AIoT | `True` |

- **Footer:** Nexo CI/CD Pipeline • KSM AIoT

**Interactive Action Buttons (Discord Components):**

- **Baris #1:** `[📜 View Run Logs]` (https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927) &nbsp; | &nbsp; `[⚙️ Workflow File]` (https://github.com/ksm-aiot-upnvj/nexo/blob/1.10.0/.github/workflows/docker-push.yml)

#### 2. Raw JSON Payload yang Dikirim ke Discord API
```json
{
  "content": "✅ **GitHub Actions:** `Build & Push on Release` (success)\nRepo: **ksm-aiot-upnvj/nexo**",
  "embeds": [
    {
      "title": "⚡ Build & Push on Release #16 (nexo)",
      "url": "https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927",
      "description": "Workflow **Build & Push on Release** is **success**.\n\n**📝 Commit / Trigger:**\n```text\nchore(release): bump to 1.10.0\n```",
      "color": 4437377,
      "author": {
        "name": "KSM-AIoT",
        "icon_url": "https://avatars.githubusercontent.com/u/297131769?v=4"
      },
      "fields": [
        {
          "name": "Repository",
          "value": "ksm-aiot-upnvj/nexo",
          "inline": true
        },
        {
          "name": "Branch / Ref",
          "value": "`1.10.0`",
          "inline": true
        },
        {
          "name": "Run Number",
          "value": "#16",
          "inline": true
        },
        {
          "name": "Status",
          "value": "Completed",
          "inline": true
        },
        {
          "name": "Conclusion",
          "value": "Success",
          "inline": true
        },
        {
          "name": "Triggered By",
          "value": "KSM-AIoT",
          "inline": true
        }
      ],
      "thumbnail": {
        "url": "https://avatars.githubusercontent.com/u/297131769?v=4?s=64"
      },
      "footer": {
        "text": "Nexo CI/CD Pipeline • KSM AIoT"
      },
      "timestamp": "2026-09-01T06:47:15Z"
    }
  ],
  "components": [
    {
      "type": 1,
      "components": [
        {
          "type": 2,
          "style": 5,
          "label": "View Run Logs",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/actions/runs/33478980927",
          "emoji": {
            "name": "📜"
          }
        },
        {
          "type": 2,
          "style": 5,
          "label": "Workflow File",
          "url": "https://github.com/ksm-aiot-upnvj/nexo/blob/1.10.0/.github/workflows/docker-push.yml",
          "emoji": {
            "name": "⚙️"
          }
        }
      ]
    }
  ]
}
```

---

