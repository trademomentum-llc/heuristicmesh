# CONFIDENTIAL — INTERNAL DUAL-USE SAFETY CONTROL

# HeuristicMesh Human Testing Safety Gate

**Version:** 1.0  
**Date:** 2026-08-22  
**Status:** Specified; not implemented  
**Authorization:** **NOT AUTHORIZED FOR HUMAN-SUBJECT OR HUMAN-PARTICIPANT USE**

## 1. Purpose and Boundary

This document gates all testing that records, observes, instructs, or physically involves a person. HeuristicMesh is an experimental sensing system, not a diagnostic service or a substitute for clinical judgment. No medical, diagnostic, injury-prevention, or emergency-response effectiveness claim may be made from the current prototype.

Until every gate in Section 2 is satisfied, testing is limited to synthetic data, mannequins, instrumented surrogates, and previously collected datasets whose use is lawful and authorized. No passive extraction, covert observation, probing, or implied consent is permitted.

## 2. Mandatory Pre-Human Gates

| Gate | Required evidence | Decision owner | Status |
|---|---|---|---|
| Engineering validation | Hardware, integration, timing, failure-mode, alert-routing, and secure-wipe tests pass with unresolved defects disclosed | Engineering lead | Pending |
| Risk assessment | Scenario-level Likelihood × Impact register, mitigations, stop conditions, and residual-risk acceptance | Qualified safety lead | Pending |
| Clinical/safety oversight | Written review by a qualified clinician and a qualified physical-safety professional familiar with fall risk | Clinical/safety lead | Pending |
| Ethics/regulatory determination | Written determination of whether IRB/ethics review, FDA device requirements, state law, insurance, or site approval applies; required approvals obtained before recruitment | PI + qualified counsel/compliance reviewer | Pending |
| Prospective opt-in consent | Understandable, dated consent obtained before participation; risks, procedures, experimental status, data use, alternatives, and withdrawal rights explained | Qualified study staff | Pending |
| Privacy and data governance | Data-minimization map, access list, encryption, retention limit, deletion procedure, and participant access/withdrawal process | Privacy reviewer | Pending |
| Emergency readiness | Trained spotters, clinician-approved protocol, full-area impact protection, first-aid response, escalation criteria, and a completed drill | Qualified safety lead | Pending |

No gate may be self-approved by the person who implemented the control being reviewed.

## 3. Consent and Participant Control

1. Participation must be affirmative and opt-in. Silence, continued presence, prior care relationships, or device proximity are not consent.
2. Information must be presented in language the person understands, with time for questions and without coercion or loss of services for declining.
3. Consent is ongoing. A participant may pause or stop a trial, recording, or data use at any time without penalty.
4. A participant stop signal immediately terminates the trial. Restart requires renewed participant agreement and fresh safety-quorum approval.
5. Only the minimum necessary data may be collected. Each sensor and recording purpose must be listed in the consent form.
6. Participants must be told how to request access, correction where applicable, withdrawal from future use, or deletion where legally and technically possible.

## 4. Safety Quorum and Stop Rules

The safety quorum consists of three separately accountable roles: Principal Investigator, qualified clinical/safety lead, and independent safety officer. Starting a human session, changing an approved scenario, or restarting after an incident requires at least two of the three roles to sign the decision. No node, operator, or automated model owns execution.

Any one of the following terminates the session immediately: participant request; pain; dizziness; distress; equipment fault; unexpected movement; loss of protective coverage; sensor or logging integrity failure; privacy breach; or any observer's credible safety concern. Termination triggers simultaneous cessation of recording and actuation, participant assistance, data isolation, credential/session revocation where relevant, and an auditable incident review before reuse.

## 5. Prototype-Stage Prohibitions

- No deliberate head-risk, unbraced fall, induced trip/slip, syncope/collapse simulation, fall from furniture, or other full loss-of-balance maneuver by a human participant.
- No recruitment of older adults, post-surgical people, people with known fall risk, minors, people with impaired decision capacity, or other potentially vulnerable groups for prototype fall simulation.
- No emergency-services dispatch, clinical decision, or treatment recommendation based solely on prototype output.
- No unsupervised, remote-only, home, or care-setting human trial.
- No reuse of recordings outside the consented purpose and retention period.

## 6. Future Approved-Study Controls

If qualified reviewers later authorize a bounded human study, every approved physical maneuver must use full-area impact protection and trained spotters, remain within the participant's demonstrated capability, and have a documented safe alternative. The approved protocol must define workload and recovery limits, adverse-event reporting, independent monitoring, and a measured go/no-go threshold. Probabilistic model output may inform noncritical analysis but may not control participant safety.

## 7. Observation and Review Format

Safety and clinical reviews must separate:

1. **Observation:** directly recorded facts.
2. **Interpretation:** hedged explanation with uncertainty and alternatives.
3. **Recommendation:** bounded next action and escalation threshold.
4. **Strengths:** protective factors, successful controls, and participant agency.

No review may diagnose a participant. Elevated concern is referred to an appropriately qualified professional or emergency service under the approved plan.

## 8. References

- HHS Office for Human Research Protections, *Informed Consent FAQs* (45 CFR 46.116 and 46.117): https://www.hhs.gov/ohrp/regulations-and-policy/guidance/faq/informed-consent/index.html
- HHS Office for Human Research Protections, *Federal Policy for the Protection of Human Subjects (Common Rule)*: https://www.hhs.gov/ohrp/regulations-and-policy/regulations/common-rule/index.html
- U.S. Food and Drug Administration, *IDE Informed Consent*: https://www.fda.gov/medical-devices/investigational-device-exemption-ide/ide-informed-consent

These references do not determine that a particular HeuristicMesh activity is regulated research or a clinical investigation. A qualified reviewer must make and document that determination for the actual protocol, institution, jurisdiction, and intended claims.

