# Appeal Letter — PTOT19: Duplicate Evaluation

**Re: Appeal of Adverse Determination — Denial of Evaluation Services**

---

**Date:** {{appeal_date}}

**To:**
{{payer_name}} Appeals Department
{{payer_address}}

**From:**
Prestige Health & Wellness
{{provider_name}}, {{provider_credentials}}
{{provider_npi}}

**Patient:** {{patient_name}}
**Date of Birth:** {{patient_dob}}
**Member ID:** {{member_id}}
**Claim Number:** {{claim_number}}
**Date(s) of Service:** {{dos}}
**CPT Code Denied:** {{cpt_code}} (97163 or 97167)
**Denied Amount:** ${{denied_amount}}
**Denial Code:** PTOT19 — Duplicate Evaluation
**Denial Date:** {{denial_date}}

---

## Assignment of Benefits

AOB on file authorizing Prestige Health & Wellness to bill, collect, and appeal on behalf of {{patient_name}}.

## Out-of-Network Provider Statement

Prestige Health & Wellness is an out-of-network provider. Episode of care determination is a clinical decision and is not affected by network status.

---

## Reason for Appeal

We are appealing the denial under code PTOT19 (Duplicate Evaluation). The denial states that a prior evaluation exists for this patient and the current evaluation is duplicative.

**We respectfully disagree.** This evaluation represents a **new and distinct episode of care** that is clinically separate from any prior evaluation on file.

## New Episode of Care Evidence

### Prior Episode

| Detail | Value |
|--------|-------|
| Prior Episode Dates | {{prior_episode_start}} to {{prior_episode_end}} |
| Prior Discharge Status | {{prior_discharge_status}} |
| Prior Diagnosis (ICD-10) | {{prior_icd10}} — {{prior_diagnosis}} |
| Prior Treating Provider | {{prior_provider}} |

### Current (New) Episode

| Detail | Value |
|--------|-------|
| New Episode Start Date | {{dos}} |
| New Referral Date | {{referral_date}} |
| Referring Physician | {{referring_physician}} |
| New Diagnosis (ICD-10) | {{new_icd10}} — {{new_diagnosis}} |
| Treating Provider | {{provider_name}} |

### Clinical Distinction

{{clinical_distinction}}

### Why This Is NOT a Duplicate

{{#reasons_not_duplicate}}
- **{{reason_title}}:** {{reason_detail}}
{{/reasons_not_duplicate}}

---

## New Evaluation Findings

### Independent Baseline Measurements

| Test/Measure | New Episode Baseline | Prior Episode Final (if available) |
|--------------|---------------------|-----------------------------------|
{{#baseline_measures}}
| {{measure_name}} | {{new_baseline}} | {{prior_final}} |
{{/baseline_measures}}

### New Plan of Care

{{new_plan_of_care}}

---

## Regulatory and Legal Basis

1. **CPT Guidelines:** A new evaluation is appropriate for each new episode of care or new condition. An evaluation is not duplicative when it addresses a distinct clinical presentation.

2. **CMS Chapter 15, §220.1:** Initial evaluation is a covered service for each new episode of care. A new episode begins when a prior episode has been formally concluded or when a new condition presents.

3. **NCCI Edits:** Evaluation codes are not duplicative when the clinical documentation demonstrates distinct episodes of care, different diagnoses, or different body regions.

---

## Escalation Notice

{{#is_fully_insured}}
If denied, we will file an **Independent External Review** with **NY DFS** (NY Insurance Law §4914). The decision is **binding**.
{{/is_fully_insured}}

{{#is_erisa}}
If denied, we will request **Federal External Review** through an IRO (29 CFR §2590.715-2719). The decision is **binding** on the plan.
{{/is_erisa}}

---

## Requested Action

1. **Overturn** the duplicate evaluation denial for {{dos}}
2. **Process payment** of ${{denied_amount}} for the new evaluation
3. **Acknowledge** this as a distinct episode of care

## Enclosed Documentation

- [ ] Denial letter
- [ ] Assignment of Benefits
- [ ] New physician referral/prescription
- [ ] Prior episode discharge summary (if available)
- [ ] Current evaluation report with independent baselines
- [ ] Documentation demonstrating distinct ICD-10 codes or body region
- [ ] New plan of care

---

**Respectfully submitted,**

{{provider_name}}, {{provider_credentials}}
NPI: {{provider_npi}}
Prestige Health & Wellness
