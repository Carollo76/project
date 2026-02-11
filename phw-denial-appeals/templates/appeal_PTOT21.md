# Appeal Letter — PTOT21: Re-Evaluation Bundled

**Re: Appeal of Adverse Determination — Denial of Re-Evaluation Services**

---

**Date:** {{appeal_date}}

**To:**
{{payer_name}} Appeals Department
{{payer_address}}

**From:**
{{entity_name}}
{{entity_address}}
Phone: {{entity_phone}} | Fax: {{entity_fax}}
NPI: {{entity_npi}} | Tax ID: {{entity_tax_id}}
{{provider_name}}, {{provider_credentials}}

**Patient:** {{patient_name}}
**Date of Birth:** {{patient_dob}}
**Member ID:** {{member_id}}
**Claim Number:** {{claim_number}}
**Date(s) of Service:** {{dos}}
**CPT Code Denied:** {{cpt_code}} (97164 or 97168)
**Denied Amount:** ${{denied_amount}}
**Denial Code:** PTOT21 — Re-Evaluation Bundled
**Denial Date:** {{denial_date}}

---

## Assignment of Benefits

AOB on file authorizing {{entity_name}} to bill, collect, and appeal on behalf of {{patient_name}}.

## Out-of-Network Provider Statement

{{entity_name}} is an out-of-network provider. Bundling edits must be applied based on clinical documentation, not network status.

---

## Reason for Appeal

We are appealing the denial of re-evaluation services (CPT {{cpt_code}}) under code PTOT21 (Re-Evaluation Bundled). The denial indicates the re-evaluation is bundled into the treatment visit and does not qualify for separate payment.

**We respectfully disagree.** The re-evaluation was a medically necessary, comprehensive reassessment triggered by a specific clinical event and is distinct from routine treatment.

## Triggering Event

A re-evaluation was performed on {{dos}} due to the following triggering event:

**{{triggering_event}}**

This event necessitated a comprehensive reassessment to establish new baselines, update the plan of care, and revise treatment goals.

## Comprehensive Reassessment Evidence

### New Objective Measurements

| Test/Measure | Previous Value ({{previous_date}}) | Re-Eval Value ({{dos}}) | Change |
|--------------|-------------------------------------|------------------------|--------|
{{#reassessment_measures}}
| {{measure_name}} | {{previous_value}} | {{current_value}} | {{change}} |
{{/reassessment_measures}}

### Updated Plan of Care

The re-evaluation resulted in the following changes to the plan of care:

{{plan_of_care_changes}}

### New/Revised Goals

{{revised_goals}}

---

## CPT Code Distinction

The re-evaluation (CPT {{cpt_code}}) is a **distinct service** from treatment codes billed on the same date:

| Service | CPT | Time | Description |
|---------|-----|------|-------------|
| Re-Evaluation | {{cpt_code}} | {{reeval_time}} | Comprehensive reassessment with new baselines |
{{#treatment_codes}}
| {{treatment_description}} | {{code}} | {{time}} | {{description}} |
{{/treatment_codes}}

**Total distinct time documented:** {{total_time}} minutes

The re-evaluation involved a **comprehensive reassessment** including new measurements, clinical analysis, and revision of the plan of care. This is NOT the same as the brief assessment performed during a routine treatment visit.

---

## Regulatory and Legal Basis

1. **CPT Guidelines:** Re-evaluation (97164/97168) is a distinct service requiring a triggering event, comprehensive reassessment, and revised plan of care. It is NOT inherently bundled with treatment codes.

2. **CMS Chapter 15, §220.1:** Re-evaluation is a covered service when clinically indicated by a change in the patient's condition.

3. **NCCI Edits:** CPT 97164/97168 are not inherently bundled with treatment codes when a triggering event is documented and the services are distinct in time and scope. Modifier 59 or XE may be used to indicate distinct services.

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

1. **Overturn** the bundling denial for CPT {{cpt_code}} on {{dos}}
2. **Process separate payment** of ${{denied_amount}} for the re-evaluation
3. **Acknowledge** the clinical distinction between re-evaluation and treatment

## Enclosed Documentation

- [ ] Denial letter
- [ ] Assignment of Benefits
- [ ] Re-evaluation report with triggering event documentation
- [ ] Previous evaluation/progress note for comparison
- [ ] Treatment log showing distinct time for re-eval vs. treatment
- [ ] Updated plan of care resulting from re-evaluation

---

**Respectfully submitted,**

{{provider_name}}, {{provider_credentials}}
{{entity_name}}
{{entity_address}}
Phone: {{entity_phone}} | Fax: {{entity_fax}}
NPI: {{entity_npi}} | Tax ID: {{entity_tax_id}}
