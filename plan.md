# CONFIDENTIAL — INTERNAL RESEARCH AND SAFETY PLANNING

# HeuristicMesh Human Testing Safety Plan

**Date:** 2026-08-22  
**Status:** Specified; not implemented  
**Current authorization:** Human fall simulation is prohibited

## 1. Objective

Establish the controls that must be independently verified before any person is invited to participate in HeuristicMesh data collection or fall-simulation work.

## 2. Status

| ID | Work item | Owner | Status | Go/no-go evidence |
|---|---|---|---|---|
| HMT-01 | Publish the human-testing safety gate | Principal Investigator | Complete | `docs/Human_Testing_Safety_Gate.md` |
| HMT-02 | Place the existing fall protocol behind the gate | Principal Investigator | Complete | Warning and gate reference in the production package |
| HMT-03 | Complete surrogate-only hardware, integration, and validation testing | Engineering lead | Pending | Signed validation report and unresolved-defect register |
| HMT-04 | Complete Likelihood × Impact risk assessment and emergency plan | Qualified safety lead | Pending | Approved risk register and drill record |
| HMT-05 | Obtain independent clinical/safety review and an ethics/regulatory determination | Qualified clinical/safety lead | Pending | Written approvals or documented non-applicability determination |
| HMT-06 | Approve understandable opt-in consent and data-governance materials | PI + clinical/safety lead + privacy reviewer | Pending | Versioned forms and retention/deletion procedure |
| HMT-07 | Authorize a bounded pilot | Safety quorum | Blocked | At least two approvals from the three named safety-quorum roles; all prior rows complete |

## 3. Go/No-Go Rule

No human testing may begin while any HMT-03 through HMT-06 item is incomplete. A participant may decline or stop unilaterally at any time; quorum approval can never override that decision.

## 4. Delivery Sequence

1. Prototype with synthetic data, mannequins, and instrumented surrogates.
2. Scale only after deterministic hardware and integration acceptance.
3. Seek certification, ethics, privacy, and qualified clinical/safety review as applicable.
4. Consider commercialization only after the validated system and human-study evidence support the intended claims.

