# PHW Denial Appeal Automation — System Architecture

## Overview

End-to-end automation for Optum/UHC denial appeals at Prestige Health & Wellness (PHW), an out-of-network PT/OT practice in Manhattan, NY. The system handles denial intake, AI-powered appeal letter drafting, deadline tracking, and escalation routing.

## System Diagram

```
DrChrono (EHR)                    Monday.com (Board 18399605169)
  │ ERA/835 webhook                   │
  │ LINE_ITEM_CREATE                  │ Status webhooks
  │ LINE_ITEM_MODIFY                  │
  ▼                                   ▼
┌─────────────────────────────────────────────────┐
│                  n8n (self-hosted)               │
│                                                 │
│  ┌──────────────┐  ┌──────────────────────┐     │
│  │ WF1: Denial  │  │ WF2: Appeal          │     │
│  │ Intake       │──│ Generation           │     │
│  └──────────────┘  └──────────────────────┘     │
│         │                    │                   │
│         │          ┌────────────────────┐       │
│         │          │ WF3: Alert &       │       │
│         │          │ Escalation (cron)  │       │
│         │          └────────────────────┘       │
│         │                    │                   │
│         ▼                    ▼                   │
│  ┌──────────────────────────────────┐           │
│  │ Vertex AI — Gemini 2.5 Pro      │           │
│  │ (us-east1, HIPAA/BAA)           │           │
│  └──────────────────────────────────┘           │
└─────────────────────────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
  Monday.com     Google Drive    RingCentral
  (items,        (appeal         (alerts to
   groups,        letters)        billing team)
   statuses)
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

**Groups:**

| Group | ID | Purpose |
|-------|----|---------|
| New Denials | group_mm0fc0ne | Incoming denials awaiting appeal |
| In Progress | group_mm0fhrnr | Appeals being drafted/reviewed |
| Submitted | group_mm0fn6ad | Appeals sent to payer |
| Resolved | group_mm0fmapq | Won, Lost, or Escalated outcomes |

**Status Labels:**
New → Drafted → Under Review → Submitted → Awaiting Decision → Won / Lost / Escalated

### 2. n8n Workflows

#### Workflow 1: Denial Intake (`denial_intake.json`)

**Trigger:** Webhook (POST to `/phw-denial-intake`)
**Source:** DrChrono ERA/835 webhook or manual entry

```
Webhook → Parse Input → Needs AI? ─┬─ Yes → Gemini Classify → Parse ─┐
                                    └─ No  → Use Structured ──────────┘
                                                                       │
                    Monday.com Create Item ← Build Item ◄──────────────┘
                              │
                    Prepare Alert → RingCentral Notify → Response
```

**Input formats accepted:**
- DrChrono ERA/835 webhook payload (`{ era_835: {...} }`)
- Manual structured entry (`{ denial_code, patient_name, dos, ... }`)
- Raw/unstructured text (routed through Gemini classification)

#### Workflow 2: Appeal Generation (`appeal_generation.json`)

**Trigger:** Webhook from Monday.com status change (item set to "New")

```
Monday.com Webhook → Status=New? ─┬─ Yes → Fetch Item Details
                                   └─ No  → Skip
                                              │
DrChrono Fetch Clinical Docs ◄────────────────┘
          │
Build Prompt → Gemini Draft → Parse Response
          │
Google Docs Create → Update Monday.com (Drafted + link) → Move to In Progress
          │
RingCentral Alert ("Appeal ready for review")
```

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
| Classify Denial | `gemini/prompts/classify_denial.txt` | ERA/835 → structured JSON |
| Draft Appeal | `gemini/prompts/draft_appeal.txt` | Classification + clinical docs → appeal letter |
| Doc Audit | `gemini/prompts/doc_audit.txt` | Phase 3: visit note → prevention flags |

**Estimated cost:** $8–20/month at ~40 appeals/month

### 4. DrChrono (EHR)

**API Version:** v4 (Hunt Valley)
**Auth:** OAuth 2.0 (Client ID + Secret)
**Status:** API app to be created for this project

**Webhook events needed:**
- `LINE_ITEM_CREATE` — new claim line items (detects denials from ERA processing)
- `LINE_ITEM_MODIFY` — updated line items (denial reason code changes)
- `CLINICAL_NOTE_LOCK` — Phase 3: triggers doc audit when notes are finalized

**API endpoints used:**
- `GET /api/clinical_notes` — pull visit notes for appeal drafting
- `GET /api/line_items` — pull claim/denial details
- `GET /api/patients` — patient demographics

### 5. RingCentral

**Channels:**
- PHW Denials — intake alerts, deadline warnings, escalation routing
- PHW Doc Alerts — Phase 3 documentation audit feedback

**Message types:**
- New denial received
- Appeal drafted and ready for review
- Filing deadline approaching (30/14/7 days)
- Escalation instructions (NY DFS or Federal)

### 6. Google Drive

**Purpose:** Store generated appeal letters as Google Docs
**Auth:** Google Cloud service account with Drive/Docs scope
**Folder:** To be configured (set `GOOGLE_DRIVE_FOLDER_ID` env var)

## Environment Variables

Set these in your n8n instance (Settings → Variables):

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `RINGCENTRAL_WEBHOOK_DENIALS` | RingCentral webhook URL for denial alerts |
| `RINGCENTRAL_WEBHOOK_DOC_ALERTS` | RingCentral webhook URL for doc audit (Phase 3) |
| `DRCHRONO_API_URL` | DrChrono API base URL (default: `https://app.drchrono.com/api`) |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive folder for appeal letters |

## n8n Credentials to Configure

| Credential | Type | Used By |
|------------|------|---------|
| Google Cloud — Vertex AI | Google API (OAuth2) | WF1 (classify), WF2 (draft) |
| Google Cloud — Drive/Docs | Google API (OAuth2) | WF2 (create appeal doc) |
| Monday.com API | HTTP Header Auth (`Authorization: <token>`) | WF1, WF2, WF3 |
| DrChrono API | HTTP Header Auth (`Authorization: Bearer <token>`) | WF2 (clinical docs) |

## Denial Code Coverage

| Code | Label | Template | Appeal Strategy |
|------|-------|----------|-----------------|
| PTOT08A | MTB Reached | `appeal_PTOT08A.md` | Outcome measures + Jimmo v. Sebelius |
| PTOT05 | Non-Skilled | `appeal_PTOT05.md` | Clinical reasoning + real-time modifications |
| PTOT21 | Re-eval Bundled | `appeal_PTOT21.md` | Triggering event + CPT distinction |
| PTOT19 | Dup Eval | `appeal_PTOT19.md` | New episode + distinct ICD-10 codes |

## Data Flow — Full Appeal Lifecycle

```
1. DENIAL RECEIVED
   DrChrono ERA/835 → n8n Webhook → Gemini classifies → Monday.com item created
   → RingCentral: "New denial: Jane Doe — PTOT08A — $850"

2. APPEAL DRAFTED
   Monday.com status=New → n8n pulls clinical docs → Gemini drafts letter
   → Google Doc created → Monday.com updated (Drafted + link)
   → RingCentral: "Appeal ready for review"

3. HUMAN REVIEW
   Billing team reviews in Google Doc → edits as needed
   → Updates Monday.com status to "Under Review" then "Submitted"

4. TRACKING
   Daily cron checks deadlines → alerts at 30/14/7 days
   → RingCentral: "[WARNING] Jane Doe — 14 days to filing deadline"

5. OUTCOME
   Status → Won: item moves to Resolved, Outcome Amount recorded
   Status → Lost: item moves to Resolved, consider escalation
   Status → Escalated: routing instructions sent via RingCentral
     - Fully Insured → NY DFS External Appeal (§4914)
     - ERISA → Federal External Review (29 CFR §2590.715-2719)
```

## HIPAA Compliance

- No PHI in git, logs, or error messages
- API tokens in environment variables / n8n credential manager
- Vertex AI in GCP Assured Workloads (BAA covered)
- Google Workspace BAA covers Drive + Vertex AI
- Monday.com stores metadata only (no clinical notes)
- DrChrono ↔ n8n over HTTPS with OAuth2
- n8n self-hosted on BAA-covered infrastructure

## File Structure

```
phw-denial-appeals/
├── config/
│   ├── denial_codes.json           # 4 denial code strategies
│   └── escalation_rules.json       # NY DFS vs ERISA routing
├── templates/
│   ├── appeal_PTOT08A.md           # MTB Reached template
│   ├── appeal_PTOT05.md            # Non-Skilled template
│   ├── appeal_PTOT21.md            # Re-eval Bundled template
│   └── appeal_PTOT19.md            # Dup Eval template
├── gemini/prompts/
│   ├── classify_denial.txt         # Denial classification prompt
│   ├── draft_appeal.txt            # Appeal letter generation prompt
│   └── doc_audit.txt               # Prevention engine prompt (Phase 3)
├── monday/
│   ├── monday_client.py            # GraphQL API client
│   ├── setup_all.py                # Board + columns + groups setup
│   └── finish_setup.py             # Manual finishing script
├── n8n/workflows/
│   ├── denial_intake.json          # WF1: DrChrono → Monday.com
│   ├── appeal_generation.json      # WF2: Monday.com → Gemini → Google Doc
│   └── alert_escalation.json       # WF3: Deadlines + Escalation
├── scripts/
│   ├── test_vertex_ai.py           # Vertex AI connectivity test
│   ├── test_monday.py              # Monday.com API test
│   └── requirements.txt            # Python dependencies
└── docs/
    └── architecture.md             # This file
```
