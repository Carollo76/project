# PHW Optum Denial Appeal Automation — Implementation Plan

## Overview

This plan covers the full build-out of the denial appeal automation system for Prestige Health & Wellness. The system spans Monday.com (pipeline + analytics), n8n (workflow orchestration), Vertex AI/Gemini (AI-powered appeal drafting), DrChrono (EHR data), RingCentral (alerts), and Google Drive (appeal letters).

All work involving PHI will be HIPAA-compliant. No non-BAA-covered services will be used.

---

## Phase 1: Foundation (Monday.com + Project Scaffolding)

### Step 1.1 — Project Structure

Create a clean project structure in this repo for all PHW automation assets:

```
phw-denial-appeals/
├── README.md                        # Project overview
├── monday/
│   ├── setup_boards.py              # Script to create/configure Monday.com boards via GraphQL API
│   ├── setup_dashboard.py           # Script to create dashboard + widgets
│   ├── cleanup_old_boards.py        # Script to delete old boards (18399114481, 18399114818)
│   └── monday_client.py             # Reusable Monday.com GraphQL client
├── templates/
│   ├── appeal_PTOT08A.md            # MTB Reached appeal template
│   ├── appeal_PTOT05.md             # Non-Skilled appeal template
│   ├── appeal_PTOT21.md             # Re-eval Bundled appeal template
│   ├── appeal_PTOT19.md             # Dup Eval appeal template
│   └── README.md                    # Template usage guide
├── gemini/
│   ├── prompts/
│   │   ├── classify_denial.txt      # Gemini prompt for denial classification
│   │   ├── draft_appeal.txt         # Gemini prompt for appeal letter generation
│   │   └── doc_audit.txt            # Gemini prompt for prevention engine doc audit
│   └── vertex_client.py             # Vertex AI HTTP client (for testing outside n8n)
├── n8n/
│   ├── workflows/
│   │   ├── denial_intake.json       # Workflow 1: Denial intake from DrChrono
│   │   ├── appeal_generation.json   # Workflow 2: AI appeal drafting
│   │   ├── alert_escalation.json    # Workflow 3: RingCentral alerts + escalation routing
│   │   └── prevention_engine.json   # Workflow 4: Daily pre-claim doc audit
│   └── README.md                    # n8n import/deployment instructions
├── config/
│   ├── denial_codes.json            # Denial code definitions + appeal strategies
│   └── escalation_rules.json        # Plan type routing rules (NY DFS vs ERISA)
├── scripts/
│   ├── test_vertex_ai.py            # Test Vertex AI connectivity
│   ├── test_monday.py               # Test Monday.com API connectivity
│   └── requirements.txt             # Python dependencies
└── docs/
    └── architecture.md              # System architecture documentation
```

**Files:** ~25 files across 7 directories
**Why:** Centralized, version-controlled home for all automation assets. Scripts are reusable and testable. n8n workflow JSONs can be imported directly into n8n.

### Step 1.2 — Monday.com Cleanup (Delete Old Boards)

Write `cleanup_old_boards.py` to delete the two incomplete boards:
- Board ID: `18399114481`
- Board ID: `18399114818`

**GraphQL mutation:**
```graphql
mutation { delete_board(board_id: 18399114481) { id } }
mutation { delete_board(board_id: 18399114818) { id } }
```

**Action:** Run the script with the user's API token to delete both boards.

### Step 1.3 — Monday.com Pipeline Board (PHW Denial Appeals)

Write `setup_boards.py` to create the full pipeline board via Monday.com GraphQL API. Steps:

1. **Create board** in Billing workspace (ID: 11690254):
   ```graphql
   mutation { create_board(board_name: "PHW Denial Appeals", board_kind: public, workspace_id: 11690254, description: "Optum/UHC denial appeal pipeline...") { id } }
   ```

2. **Create 11 columns** (Name column auto-exists) in exact order:
   - Denial Code (dropdown) — 4 labels
   - DOS (date)
   - Amount (numbers, USD)
   - Plan Type (dropdown) — 2 labels
   - Denial Date (date)
   - Filing Deadline (date)
   - Appeal Status (status) — 8 custom labels with specific colors
   - Appeal Letter (link)
   - Provider (dropdown) — 4 placeholder labels
   - Location (dropdown) — 4 placeholder labels
   - Outcome Amount (numbers)

3. **Configure Appeal Status labels** using `change_column_metadata`:
   - New (#579bfc), Drafted (#fdab3d), Under Review (#a25ddc), Submitted (#0086c0)
   - Awaiting Decision (#ffcb00), Won (#00c875, is_done: true), Lost (#df2f4a), Escalated (#bb3354)

4. **Create 4 groups** in order:
   - New Denials (light blue) — top group for new items
   - In Progress (orange)
   - Submitted (dark blue)
   - Resolved (green)

5. **Delete default "Group Title" group**

### Step 1.4 — Monday.com Analytics Dashboard

Write `setup_dashboard.py` to create the dashboard:

1. **Create dashboard** in Billing workspace connected to the pipeline board
2. **Add 5 widgets:**
   - Win Rate by Denial Code (chart — bar/pie, grouped by Denial Code, filtered to Won/Lost)
   - Appeals by Status (chart — bar, grouped by Appeal Status)
   - Total Denied Amount (number — sum of Amount column)
   - Total Recovered (number — sum of Outcome Amount column)
   - Pipeline Status (battery — Appeal Status distribution)

**Note:** Widget creation via API has specific schema requirements. The script will first fetch `all_widgets_schema` to understand required fields, then create each widget.

### Step 1.5 — Configuration Files

Create JSON configuration files:

- **`denial_codes.json`** — All 4 denial codes with:
  - Code, description, appeal strategy keywords
  - Required documentation checklist
  - Relevant CMS citations
  - Typical filing deadlines

- **`escalation_rules.json`** — Routing logic:
  - Fully Insured → NY DFS external appeal (binding, 30 days)
  - Self-Funded/ERISA → Federal external review (CMS/DOL)

### Step 1.6 — Appeal Letter Templates

Create 4 Markdown/Google Doc templates (one per denial code):

- **PTOT08A (MTB Reached):** Standardized outcome measures framework, exercise progression documentation, CMS MBPM Ch.15 §220.2 citation
- **PTOT05 (Non-Skilled):** Clinical reasoning justification, real-time modification documentation, safety concerns, CMS Ch.15 §220.2(B)
- **PTOT21 (Re-eval Bundled):** Triggering event documentation, comprehensive reassessment evidence, CPT 97164/97168 citation
- **PTOT19 (Dup Eval):** New episode evidence, distinct ICD-10 codes, provider-change justification

Each template includes:
- OON-specific language (PHW is out-of-network)
- AOB reference (Assignment of Benefits on file)
- Dual escalation path citations (state + federal)
- Placeholder variables for patient-specific data (e.g., `{{patient_name}}`, `{{dos}}`, `{{denial_code}}`)

---

## Phase 2: Appeal Generator (Gemini + n8n Workflows)

### Step 2.1 — Gemini Prompt Engineering

Create three carefully crafted prompts:

1. **`classify_denial.txt`** — Takes raw denial data (ERA/835 or manual entry) and:
   - Identifies which of the 4 denial codes applies
   - Extracts patient info, DOS, amount, plan type
   - Returns structured JSON for downstream processing

2. **`draft_appeal.txt`** — Takes classified denial + clinical docs and:
   - Selects correct appeal template
   - Fills in patient-specific data from DrChrono records
   - Generates tailored appeal letter with OON language
   - Includes appropriate CMS citations and escalation references
   - Returns appeal letter in Google Doc-ready format

3. **`doc_audit.txt`** (Phase 3) — Pre-claim documentation audit prompt

### Step 2.2 — Vertex AI Integration Testing

Create `test_vertex_ai.py` to verify:
- OAuth 2.0 authentication with service account JSON key
- Successful API call to `us-east1-aiplatform.googleapis.com`
- Gemini 2.5 Pro model responds with expected format
- Token usage tracking for cost monitoring (~$8-20/mo budget)

### Step 2.3 — n8n Workflow 1: Denial Intake

Build `denial_intake.json` (n8n workflow export):
- **Trigger:** DrChrono ERA/835 webhook OR manual webhook entry
- **Processing:**
  - Parse denial code, patient name, DOS, amount from incoming data
  - Call Gemini for classification (if raw/unstructured input)
  - Determine plan type (fully insured vs self-funded)
  - Calculate filing deadline (denial date + 12 months)
- **Output:** Create Monday.com item in "New Denials" group with all column values populated
- **Alert:** Send RingCentral message to billing team confirming new denial received

### Step 2.4 — n8n Workflow 2: Appeal Generation

Build `appeal_generation.json`:
- **Trigger:** Monday.com webhook — item status changes to "New"
- **Processing:**
  - Pull clinical documentation from DrChrono API (visit notes, eval data, outcome measures)
  - Send to Gemini with `draft_appeal.txt` prompt + denial-code-specific template
  - Generate appeal letter
  - Create Google Doc in Drive with the appeal letter
- **Output:**
  - Update Monday.com item: set Appeal Letter link, change status to "Drafted"
  - Move item to "In Progress" group
  - Send RingCentral alert: "Appeal drafted for [Patient] — review needed"

### Step 2.5 — n8n Workflow 3: Alert & Escalation

Build `alert_escalation.json`:
- **Trigger:** Monday.com webhook on status changes + daily cron for deadline checks
- **Processing:**
  - Deadline alerts at 30, 14, and 7 days before filing deadline
  - Escalation routing when status = "Escalated":
    - Fully Insured → generate NY DFS external appeal filing instructions
    - Self-Funded → generate Federal/ERISA review filing instructions
- **Output:** RingCentral messages to billing team with specific action items

### Step 2.6 — End-to-End Testing

- Process 10 historical denials through the full pipeline
- Verify: intake → classification → appeal draft → Monday.com tracking → alerts
- Validate appeal letter quality against Christian's standards
- Confirm deadline calculations are accurate

---

## Phase 3: Prevention Engine (Weeks 5-6)

### Step 3.1 — n8n Workflow 4: Daily Documentation Audit

Build `prevention_engine.json`:
- **Trigger:** Daily cron (e.g., 6 AM before billing runs)
- **Processing:**
  - Pull today's visit notes from DrChrono
  - Send each to Gemini with `doc_audit.txt` prompt
  - Gemini checks against denial-code-specific documentation checklists:
    - PTOT08A: Are standardized outcome measures included? Exercise progression documented?
    - PTOT05: Is clinical reasoning for skilled care documented? Safety concerns noted?
    - PTOT21: Is triggering event for re-eval documented? New goals established?
    - PTOT19: Is new episode evidence or distinct ICD-10 documented?
- **Output:** RingCentral alert to treating therapist with specific fix instructions

### Step 3.2 — Feedback Loop

- Connect denial outcomes (Won/Lost) back to Gemini prompt refinement
- Track which appeal strategies succeed most often per denial code
- Update templates and prompts based on win/loss patterns

---

## Execution Order (What I'll Build When Approved)

| Step | Task | Depends On |
|------|------|------------|
| 1 | Create project directory structure | Nothing |
| 2 | Write `monday_client.py` (reusable GraphQL client) | Nothing |
| 3 | Write + run `cleanup_old_boards.py` | API token from user |
| 4 | Write + run `setup_boards.py` (pipeline board) | Step 3 |
| 5 | Configure Appeal Status labels + groups | Step 4 |
| 6 | Write + run `setup_dashboard.py` (analytics) | Step 4 |
| 7 | Create `denial_codes.json` + `escalation_rules.json` | Nothing |
| 8 | Create 4 appeal letter templates | Nothing |
| 9 | Write Gemini prompts (classify, draft, audit) | Nothing |
| 10 | Write `test_vertex_ai.py` | Nothing |
| 11 | Build n8n workflow JSONs (4 workflows) | Steps 4, 9 |
| 12 | Run verification checklist | Steps 3-6 |

**Parallelizable:** Steps 1, 2, 7, 8, 9, 10 can all be done in parallel.
**Sequential:** Steps 3 → 4 → 5 → 6 → 12 must be in order.
**Needs user input:** Step 3 requires Monday.com API token to execute.

---

## What I Need From You Before Executing

1. **Monday.com API token** — to run the board cleanup and setup scripts
2. **Confirmation** — that you want all this built in the current repo alongside the stock analyzer, or if you'd prefer a separate repo
3. **DrChrono API details** (Phase 2) — API key/credentials and endpoint documentation
4. **RingCentral webhook URLs** (Phase 2) — for PHW Denials and PHW Doc Alerts channels
5. **Google Drive folder ID** (Phase 2) — where appeal letters should be saved

---

## HIPAA Compliance Notes

- All API tokens/keys stored in environment variables or n8n credential manager (never hardcoded)
- No PHI in git commits, logs, or error messages
- Vertex AI runs inside GCP Assured Workloads HIPAA project
- Google Workspace BAA covers Drive + Vertex AI
- AWS BAA covers n8n Lightsail instance
- Monday.com used for metadata only (denial codes, statuses, amounts — no clinical notes)
