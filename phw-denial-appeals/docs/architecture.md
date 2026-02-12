# PHW Denial Appeal Automation — System Architecture

## Overview

End-to-end automation for insurance denial appeals across all 10 entities operating under the Prestige Health & Wellness (PHW) DBA. Each entity operates independently under its own legal name (e.g., FIDI Chiropractic PC). The system handles denial intake from multiple sources, AI-powered classification and appeal letter drafting, deadline tracking, escalation routing, and duplicate detection.

**Multi-Entity:** Denials are addressed to specific entities, and appeal letters are sent from that entity's letterhead — never from "Prestige Health & Wellness."

**Multi-Payer:** While auto-appeal is currently built for Optum/UHC denials, the system tracks ALL denials regardless of payer. Unknown payers or unknown denial codes are routed to staff for manual appeal.

## System Diagram

```
Google Drive                DrChrono (EHR)              Monday.com (Board 18399605169)
  │ "Denial Inbox"            │ Polled 2x/day             │
  │ folder trigger             │ (8 AM + 4 PM)             │ Status webhooks
  │ (scan & drop)              │                            │
  ▼                            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    n8n (self-hosted)                         │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ WF1: Denial Intake   │  │ WF2: Appeal          │        │
│  │ (3 intake paths)     │──│ Generation           │        │
│  │ + Entity Lookup      │  │ (entity-aware)       │        │
│  │ + Duplicate Check    │  └──────────────────────┘        │
│  └──────────────────────┘           │                      │
│         │                  ┌────────────────────┐          │
│         │                  │ WF3: Alert &       │          │
│         │                  │ Escalation (cron)  │          │
│         │                  └────────────────────┘          │
│         ▼                           ▼                      │
│  ┌──────────────────────────────────────────┐              │
│  │ Vertex AI — Gemini 2.5 Pro              │              │
│  │ (us-east1, HIPAA/BAA)                   │              │
│  │ + Text classification (ERA/manual)      │              │
│  │ + Multimodal classification (scans)     │              │
│  │ + Appeal letter drafting                │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
  Monday.com     Google Drive    RingCentral
  (items,        (scan intake    (alerts to
   groups,        + appeal        billing team)
   statuses)      letters)
```

## Components

### 1. Monday.com — Pipeline Board

**Board ID:** 18399605169
**Workspace:** Billing (ID: 11690254)
**URL:** https://phw-team.monday.com/boards/18399605169

| Column | Type | ID |
|--------|------|----|
| Name | name | name |
| Denial Code | dropdown | dropdown_mm0ffjcd |
| DOS | date | date_mm0fp9n1 |
| Amount | numbers | numeric_mm0fh3jn |
| Plan Type | dropdown | dropdown_mm0fjy49 |
| Denial Date | date | date_mm0frn70 |
| Filing Deadline | date | date_mm0fgzne |
| Appeal Status | status | color_mm0fj7fm |
| Appeal Letter | link | link_mm0fsy2k |
| Provider | dropdown | dropdown_mm0fdaya |
| Location | dropdown | dropdown_mm0fac7b |
| Outcome Amount | numbers | numeric_mm0fvbv1 |
| Entity Name | text | text_mm0gr7ga |
| Entity NPI | text | text_mm0gv12z |
| Payer Name | text | text_mm0gw2sh |

**Groups:**

| Group | ID | Purpose |
|-------|----|---------|
| New Denials | group_mm0fc0ne | Incoming denials awaiting appeal |
| In Progress | group_mm0fhrnr | Appeals being drafted/reviewed |
| Submitted | group_mm0fn6ad | Appeals sent to payer |
| Resolved | group_mm0fmapq | Won, Lost, or Escalated outcomes |

**Status Labels:**
New → Drafted → Under Review → Submitted → Awaiting Decision → Won / Lost / Escalated / Manual Review Required

### 2. n8n Workflows

#### Workflow 1: Denial Intake (`denial_intake.json`)

**Three intake paths converging into a shared pipeline:**

```
PATH A — Electronic (DrChrono ERA/835):
  Cron (8 AM + 4 PM) → Poll DrChrono API → Parse batch
  → Has denials? → Normalize ERA data ────────────────────────────┐
                                                                    │
PATH B — Scanned Paper Denials (Google Drive):                      │
  GDrive Trigger (every 2 min) → Download file                     │
  → Validate MIME type → Gemini multimodal classify                │
  → Parsed OK? ─┬─ YES → Move to Processed → Forward data ────────┤
                └─ NO  → Move to Failed → RingCentral error alert  │
                                                                    │
PATH C — Manual Fallback (Webhook POST):                            │
  Webhook → Parse input → Needs AI? ─┬─ YES → Gemini text classify ┤
                                      └─ NO  → Use structured data ─┘
                                                                    │
                          ALL PATHS CONVERGE HERE ◄─────────────────┘
                                    │
                          Entity Lookup (match entity name to config)
                                    │
                          Monday.com Duplicate Check (patient + DOS + code)
                                    │
                      ┌─ Not Duplicate ──────────┐
                      │                          │
                      │  Known Payer + Code?      │  Duplicate Found
                      │  YES → status: "New"     │  → RingCentral duplicate alert
                      │  NO  → status: "Manual   │  → No item created
                      │         Review Required"  │
                      │                          │
                      │  Build Monday.com Item    │
                      │  → Create Item            │
                      │  → RingCentral Alert      │
                      └──────────────────────────┘
```

**Input formats accepted:**
- DrChrono ERA/835 polling (electronic, 2x/day at 8 AM and 4 PM)
- Scanned denial letter dropped into Google Drive "Denial Inbox" folder (PDF, PNG, JPEG, TIFF, WEBP) — processed via Gemini 2.5 Pro multimodal classification (no separate OCR step)
- Manual webhook POST to `/phw-denial-intake` (fallback when scan fails)

**Key features:**
- **Multi-entity:** Gemini extracts entity name from denial, matched against `config/entities.json`
- **Multi-payer:** System extracts exact payer name; non-Optum/UHC denials routed to manual review
- **Unknown denial codes:** Codes not matching the 4 known types set to "OTHER" and routed to manual review
- **Duplicate detection:** Checks Monday.com for existing items with same patient + DOS + denial code before creating
- **DrChrono rate limits:** Polling 2x/day instead of webhooks — only ~10-20 API calls/day

#### Workflow 2: Appeal Generation (`appeal_generation.json`)

**Trigger:** Webhook from Monday.com status change (item set to "New")

```
Monday.com Webhook → Status=New? ─┬─ Yes → Fetch Item Details (including entity columns)
                                   └─ No  → Skip
                                              │
                              Entity Lookup (from ENTITIES_CONFIG env var)
                                              │
DrChrono Fetch Clinical Docs ◄────────────────┘
          │
Build Prompt (entity-aware — uses entity name, NOT "Prestige Health & Wellness")
          │
Gemini Draft → Parse Response
          │
Google Docs Create (titled: "Appeal — {Entity} — {Patient} — {Code} — {Date}")
          │
Update Monday.com (Drafted + link) → Move to In Progress
          │
RingCentral Alert ("Appeal ready for review" — includes entity name)
```

**Entity-aware drafting:** The appeal prompt instructs Gemini to use the specific entity's name, address, NPI, tax ID, phone, and fax throughout the letter. The template variable `{{entity_name}}` replaces the former hardcoded "Prestige Health & Wellness."

**Gemini prompt selects template by denial code:**
- PTOT08A → `appeal_PTOT08A.md`
- PTOT05 → `appeal_PTOT05.md`
- PTOT21 → `appeal_PTOT21.md`
- PTOT19 → `appeal_PTOT19.md`

#### Workflow 3: Alert & Escalation (`alert_escalation.json`)

**Triggers:**
1. Daily cron at 7 AM — deadline checks
2. Monday.com webhook — status change handling

```
[Cron 7 AM] → Fetch All Items → Check Deadlines → Alerts? → RingCentral
                                                    └─ No → Done

[Status Change] → Escalated? ─┬─ Yes → Fetch Item → Route by Plan Type → RingCentral
                               └─ No  → Won/Lost? → Move to Resolved group
```

**Escalation routing:**

| Plan Type | Path | Authority | Deadline | Citation |
|-----------|------|-----------|----------|----------|
| Fully Insured | NY DFS External Appeal | NY DFS | 120 days | NY Insurance Law §4914 |
| Self-Funded (ERISA) | Federal External Review | IRO via CMS/DOL | 120 days | 29 CFR §2590.715-2719 |

### 3. Vertex AI / Gemini

**Model:** Gemini 2.5 Pro
**Region:** us-east1
**Auth:** OAuth 2.0 service account

**Three prompts:**

| Prompt | File | Purpose |
|--------|------|---------|
| Classify Denial | `gemini/prompts/classify_denial.txt` | Text/ERA → structured JSON (entity + payer aware) |
| Classify Denial (Multimodal) | Embedded in `denial_intake.json` | Scanned PDF/image → structured JSON |
| Draft Appeal | `gemini/prompts/draft_appeal.txt` | Classification + clinical docs → entity-specific appeal letter |
| Doc Audit | `gemini/prompts/doc_audit.txt` | Phase 3: visit note → prevention flags |

**Estimated cost:** $8–20/month at ~40 appeals/month

### 4. DrChrono (EHR)

**API Version:** v4 (Hunt Valley)
**Auth:** OAuth 2.0 (Client ID + Secret)
**Polling:** 2x/day via cron (8 AM + 4 PM) — avoids rate limits

**API endpoints used:**
- `GET /api/line_items?since=...&status=denied` — poll for denied line items (WF1)
- `GET /api/clinical_notes` — pull visit notes for appeal drafting (WF2)
- `GET /api/patients` — patient demographics (WF2)

### 5. RingCentral

**Channels:**
- PHW Denials — intake alerts, deadline warnings, escalation routing
- PHW Doc Alerts — Phase 3 documentation audit feedback

**Message types:**
- New denial received (includes entity name, payer, source)
- Non-Optum payer detected (manual review required)
- Unknown denial code detected (manual review required)
- Entity not matched (config update needed)
- Duplicate denial detected (no new item created)
- Scan parse failed (file moved to Failed folder)
- Appeal drafted and ready for review
- Filing deadline approaching (30/14/7 days)
- Escalation instructions (NY DFS or Federal)

### 6. Google Drive

**Purpose:**
1. **Intake:** Watch "Denial Inbox" folder for scanned paper denials
2. **Output:** Store generated appeal letters as Google Docs

**Auth:** Google Cloud service account with Drive/Docs scope

**Folder Structure:**
```
PHW Denial Appeals/
├── Denial Inbox/          ← Staff drops scanned denial letters here
│                            (GOOGLE_DRIVE_DENIAL_INBOX_ID)
├── Processed Denials/     ← Successfully parsed scans moved here automatically
│                            (GOOGLE_DRIVE_PROCESSED_DENIALS_ID)
├── Failed Denials/        ← Scans that could not be parsed; staff reviews manually
│                            (GOOGLE_DRIVE_FAILED_DENIALS_ID)
└── Appeal Letters/        ← Generated appeal letter Google Docs
                             (GOOGLE_DRIVE_FOLDER_ID)
```

### 7. Entity Configuration (`config/entities.json`)

Master list of all 10 PHW entities. Each entity includes:
- `entity_name` — Legal name (e.g., "FIDI Chiropractic PC")
- `aliases` — Alternative names for fuzzy matching
- `npi`, `tax_id` — Billing identifiers
- `address`, `phone`, `fax` — Contact information
- `specialty` — Entity specialty type

Entity matching is performed by Gemini extracting the practice name from the denial letter, then matching against this config using exact match → alias match → fuzzy/contains match.

## Environment Variables

Set these in your n8n instance (Settings → Variables):

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `RINGCENTRAL_WEBHOOK_DENIALS` | RingCentral webhook URL for denial alerts |
| `RINGCENTRAL_WEBHOOK_DOC_ALERTS` | RingCentral webhook URL for doc audit (Phase 3) |
| `DRCHRONO_API_URL` | DrChrono API base URL (default: `https://app.drchrono.com/api`) |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive folder for appeal letters |
| `GOOGLE_DRIVE_DENIAL_INBOX_ID` | Google Drive folder for scanned denial intake |
| `GOOGLE_DRIVE_PROCESSED_DENIALS_ID` | Google Drive folder for processed scans |
| `GOOGLE_DRIVE_FAILED_DENIALS_ID` | Google Drive folder for failed-to-parse scans |
| `ENTITIES_CONFIG` | JSON string of entity master data (from config/entities.json) |

## n8n Credentials to Configure

| Credential | Type | Used By |
|------------|------|---------|
| Google Cloud — Vertex AI | Google API (OAuth2) | WF1 (classify), WF2 (draft) |
| Google Cloud — Drive/Docs | Google API (OAuth2) | WF1 (scan intake), WF2 (create appeal doc) |
| Monday.com API | HTTP Header Auth (`Authorization: <token>`) | WF1, WF2, WF3 |
| DrChrono API | HTTP Header Auth (`Authorization: Bearer <token>`) | WF1 (poll), WF2 (clinical docs) |

## Denial Code Coverage

| Code | Label | Template | Appeal Strategy | Auto-Appeal? |
|------|-------|----------|-----------------|--------------|
| PTOT08A | MTB Reached | `appeal_PTOT08A.md` | Outcome measures + Jimmo v. Sebelius | Yes (Optum) |
| PTOT05 | Non-Skilled | `appeal_PTOT05.md` | Clinical reasoning + real-time modifications | Yes (Optum) |
| PTOT21 | Re-eval Bundled | `appeal_PTOT21.md` | Triggering event + CPT distinction | Yes (Optum) |
| PTOT19 | Dup Eval | `appeal_PTOT19.md` | New episode + distinct ICD-10 codes | Yes (Optum) |
| OTHER | Unknown | — | Manual review required | No |

## Data Flow — Full Appeal Lifecycle

```
1. DENIAL RECEIVED
   Path A: DrChrono ERA/835 (polled 2x/day) → n8n normalizes → Entity Lookup
   Path B: Staff scans paper denial → drops PDF in Google Drive Inbox
           → n8n detects (2 min) → Gemini multimodal classifies → Entity Lookup
   Path C: Manual webhook POST (fallback) → n8n parses → Entity Lookup

   → Entity matched to config? (name, NPI, address, phone, fax, tax ID)
   → Duplicate check (patient + DOS + code against Monday.com board)
   → Known payer + known code? → Status: "New" (auto-appeal) or "Manual Review Required"
   → Monday.com item created
   → RingCentral: "New denial: FIDI Chiropractic PC — Jane Doe — PTOT08A — $850"

2. APPEAL DRAFTED (auto-appeal path only)
   Monday.com status=New → n8n pulls entity details + clinical docs
   → Gemini drafts entity-specific letter (FROM: FIDI Chiropractic PC, NOT PHW)
   → Google Doc created → Monday.com updated (Drafted + link)
   → RingCentral: "Appeal ready for review — FIDI Chiropractic PC"

3. HUMAN REVIEW
   Billing team reviews in Google Doc → edits as needed
   → Updates Monday.com status to "Under Review" then "Submitted"

4. TRACKING
   Daily cron checks deadlines → alerts at 30/14/7 days
   → RingCentral: "[WARNING] FIDI Chiropractic PC — Jane Doe — 14 days to deadline"

5. OUTCOME
   Status → Won: item moves to Resolved, Outcome Amount recorded
   Status → Lost: item moves to Resolved, consider escalation
   Status → Escalated: routing instructions sent via RingCentral
     - Fully Insured → NY DFS External Appeal (§4914)
     - ERISA → Federal External Review (29 CFR §2590.715-2719)
```

## Duplicate Detection

**When:** After Entity Lookup, before Monday.com item creation.
**How:** Query Monday.com board for items matching:
- Tier 1: Same patient name + same DOS + same denial code (definitive match)
- Tier 2: Same claim number if available

**What happens on duplicate:**
- No new Monday.com item created
- RingCentral alert: "Duplicate denial detected — existing item preserved"
- File moved to "Processed Denials" (if from Google Drive scan path)
- Prevents duplicate appeals from being drafted when the same denial arrives via ERA and paper

## Unknown Payer / Unknown Code Handling

| Scenario | Monday.com Status | Auto-Appeal? | Staff Action |
|----------|------------------|--------------|--------------|
| Known payer (Optum) + Known code (PTOT08A/05/21/19) | New | Yes | Review drafted appeal |
| Known payer (Optum) + Unknown code | Manual Review Required | No | Draft appeal manually |
| Unknown payer (Aetna, Cigna, etc.) + Any code | Manual Review Required | No | Draft appeal manually |
| Unknown payer + Unknown code | Manual Review Required | No | Draft appeal manually |

All denials are tracked in Monday.com regardless — nothing gets lost.

## HIPAA Compliance

- No PHI in git, logs, or error messages
- API tokens in environment variables / n8n credential manager
- Vertex AI in GCP Assured Workloads (BAA covered)
- Google Workspace BAA covers Drive + Vertex AI
- Monday.com stores metadata only (no clinical notes)
- DrChrono ↔ n8n over HTTPS with OAuth2
- n8n self-hosted on BAA-covered infrastructure
- Scanned denial letters are processed in-memory only (base64 in n8n → Vertex AI)
- No scanned document content persisted in n8n execution logs
- Google Drive folders within BAA-covered Google Workspace
- Files moved (not copied) from Inbox to Processed/Failed to minimize PHI exposure window

## File Structure

```
phw-denial-appeals/
├── config/
│   ├── denial_codes.json           # 4 denial code strategies
│   ├── escalation_rules.json       # NY DFS vs ERISA routing
│   └── entities.json               # 10 entity master data (name, NPI, address, etc.)
├── templates/
│   ├── appeal_PTOT08A.md           # MTB Reached template (entity-aware)
│   ├── appeal_PTOT05.md            # Non-Skilled template (entity-aware)
│   ├── appeal_PTOT21.md            # Re-eval Bundled template (entity-aware)
│   └── appeal_PTOT19.md            # Dup Eval template (entity-aware)
├── gemini/prompts/
│   ├── classify_denial.txt         # Denial classification (multi-entity, multi-payer)
│   ├── draft_appeal.txt            # Appeal letter generation (entity-aware)
│   └── doc_audit.txt               # Prevention engine prompt (Phase 3)
├── monday/
│   ├── monday_client.py            # GraphQL API client
│   ├── setup_all.py                # Board + columns + groups setup
│   └── finish_setup.py             # Manual finishing script
├── n8n/workflows/
│   ├── denial_intake.json          # WF1: 3 intake paths → Entity → Duplicate → Monday.com
│   ├── appeal_generation.json      # WF2: Monday.com → Gemini → entity-aware Google Doc
│   └── alert_escalation.json       # WF3: Deadlines + Escalation
├── scripts/
│   ├── test_vertex_ai.py           # Vertex AI connectivity test
│   ├── test_monday.py              # Monday.com API test
│   └── requirements.txt            # Python dependencies
└── docs/
    └── architecture.md             # This file
```
