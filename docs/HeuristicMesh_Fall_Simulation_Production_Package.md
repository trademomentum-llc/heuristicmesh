# HeuristicMesh Fall Simulation Production Package
## Controlled Ground-Truth Data Collection Protocol
**Version:** 1.0  
**Date:** 2026-08-11  
**Classification:** Internal Data-Collection Protocol  
**Purpose:** Generate synchronized multi-modal (thermal + NIR + body-cam) labeled datasets for Framework 2 / Framework 3 training and validation.

> **SAFETY HOLD — NOT AUTHORIZED FOR HUMAN USE.** This document describes candidate scenarios only. Every reference to a “subject” means a non-human surrogate unless all gates in `Human_Testing_Safety_Gate.md` are independently satisfied and documented. The current prototype may not be used for deliberate human falls, passive recording, diagnosis, or emergency-response decisions.

---

## 1. Scene Description (Physical Setup)

**Environment**
- Quiet indoor room, minimum 4 m × 4 m clear floor space.
- Flooring: mix of hard surface (tile or wood) and one low-pile rug section to support both slip and trip scenarios.
- Ambient temperature: 20–24 °C (stable). No direct sunlight or strong HVAC drafts across the sensor FOV.
- Lighting: normal indoor LED (3000–4000 K). NIR cameras will operate with IR-cut forced open; no additional visible lighting changes required.

**Sensor Placement (fixed)**
- AMG8833 + MLX90640 (via ESP32 concentrator): ceiling or high wall mount, 2.4–2.8 m height, angled 30–45° downward to cover the primary activity zone (approx. 3 m × 3 m).
- Jetson A + Arducam OV5467S: primary room overview, same optical axis preference as thermal sensors if possible.
- Jetson B + second Arducam: secondary angle (90° offset preferred) for occlusion handling.
- NUC: outside the activity zone, running the orchestrator and event logger.

**Subject Preparation**
- Human subject preparation is prohibited at the current project stage. Use a mannequin or instrumented surrogate.
- Subject wears both CQH body cameras (chest and upper back or shoulder) and the Ksadbossbo unit (waist or chest secondary).
- Clothing: normal indoor clothing (long sleeves acceptable). Avoid heavy reflective materials.
- Body cameras started 60–90 seconds before first scenario and left running continuously for the entire session.
- Subject is briefed on safe fall techniques (see safety section). A padded mat is available but used only for higher-risk scenarios.

**Safety**
- The controlling requirements are in `Human_Testing_Safety_Gate.md`; if they conflict with this scenario package, the safety gate prevails.
- Prototype-stage execution is surrogate-only. Deliberate human head-risk, unbraced fall, trip/slip, syncope/collapse, and furniture-fall scenarios are prohibited.
- A future approved human protocol requires prospective opt-in consent, qualified clinical and physical-safety oversight, full-area impact protection, an emergency plan, and two-of-three safety-quorum authorization.
- A participant may stop unilaterally at any time. Any pain, dizziness, distress, equipment fault, privacy concern, or observer safety concern terminates the session.

---

## 2. Orchestrator’s Script (Session Director)

**Activation prerequisite:** This script remains inactive for human participants until every mandatory gate in `Human_Testing_Safety_Gate.md` is approved. Automated systems may not authorize, start, or continue a human trial.

**Pre-Session (T-10 min)**
1. Confirm all sensors online and logging (ESP32 burst ready, Jetsons streaming, NUC event logger running).
2. Start all three body cameras. Verbally note the start time and any clock offset.
3. Position subject in the center of the primary FOV.
4. Announce: “Session start. All systems recording. Subject ready.”

**Per Scenario Template**
1. State the scenario ID and short name clearly (for audio track on body cams and NUC log).
2. Give the subject the precise starting posture and any props required.
3. Countdown: “Three… two… one… execute.”
4. After the fall settles (subject remains still for 4–6 seconds), call “Hold… recover.”
5. Log the exact system timestamp of the “execute” command and the moment the subject contacts the floor.
6. Allow 30–60 seconds recovery / repositioning before next trial.
7. After every third trial, verify body-camera recording status and free storage.

**Post-Session**
1. Call “Session end. Stop all body cameras.”
2. Copy AVI files immediately.
3. Run the body-camera sync utility against the NUC event log.
4. Archive raw thermal bursts, NIR frames, and labeled CSV together.

---

## 3. Fall Scenarios — Accurate & Complete Detail

Scenarios are ordered by clinical frequency first, then by detection difficulty. Each entry contains the information required for consistent, repeatable capture.

### Tier 1 — Most Common Falls (High Frequency, Moderate Detection Difficulty)

**S01 — Forward Trip over Low Obstacle**
- Clinical relevance: Most frequent community fall mechanism (uneven surface, rug edge, pet, cable).
- Starting posture: Standing, normal gait initiation toward the obstacle.
- Execution: Subject walks at normal pace, catches toe on 2–4 cm obstacle (rolled towel or low threshold), loses forward balance, and falls forward onto hands/knees or side.
- Hold: Remain still 5 seconds after impact.
- Why real data is required: Variable arm-bracing, partial recovery attempts, and thermal motion blur differ markedly from synthetic data.
- Recommended trials: 6–8 (mix left/right lead foot).

**S02 — Backward Loss of Balance (Sit-to-Stand Failure)**
- Clinical relevance: Extremely common in elderly and post-surgical patients when rising from chair.
- Starting posture: Seated on standard chair, feet flat.
- Execution: Subject attempts to stand; knees or hips give way; falls backward or slightly sideways into the chair or onto the floor behind the chair.
- Hold: 5 seconds.
- Why real data is required: Slow initial descent followed by sudden acceleration is frequently misclassified as “sitting” by pure velocity thresholds.
- Recommended trials: 6 (3 successful partial recoveries, 3 full falls).

**S03 — Lateral Slip on Smooth Surface**
- Clinical relevance: Wet floor, polished wood, or sock-on-tile.
- Starting posture: Standing or slow walk.
- Execution: Foot slips laterally; subject falls to the side, often with arm extension.
- Hold: 5 seconds.
- Why real data is required: Asymmetric thermal signature and rapid horizontal centroid shift are under-represented in public datasets.
- Recommended trials: 6 (3 left, 3 right).

### Tier 2 — High-Impact / High-Injury-Risk Common Falls

**S04 — Forward Fall with Incomplete Arm Brace (Head-Risk)**
- Clinical relevance: Second most common serious injury mechanism.
- Execution: Same as S01 but subject deliberately delays or reduces arm extension so the fall progresses further toward the torso/head.
- Safety: Use landing mat; spotter ready.
- Recommended trials: 4 only.

**S05 — Fall from Standing with Rotation (Twist + Fall)**
- Clinical relevance: Turning while walking or reaching.
- Execution: Subject turns 90–180° and loses balance mid-turn, falling obliquely.
- Why real data is required: Complex multi-axis motion confuses both skeleton estimators and simple thermal centroid trackers.
- Recommended trials: 6.

### Tier 3 — Most Elusive Falls (Low Frequency but High False-Negative Rate)

These are the scenarios that pure computer-vision or simple thermal rules routinely miss or misclassify. Real multi-modal data is essential.

**S06 — Slow Syncope / Collapse (Gradual Loss of Postural Tone)**
- Clinical relevance: Orthostatic hypotension, cardiac, or vasovagal events.
- Starting posture: Standing still for 10–15 seconds.
- Execution: Subject slowly buckles at the knees and hips over 2–4 seconds, sliding or crumpling downward rather than falling sharply. Arms may remain at sides or make only weak protective movements.
- Hold: Full 8–10 seconds of immobility.
- Why real data is required: Low peak velocity; many systems interpret this as “intentional sitting” or “kneeling.” Thermal signature shows gradual rather than abrupt shape change.
- Recommended trials: 8–10 (highest priority for elusive-class data).

**S07 — Fall from Bed / Edge of Bed (Night-Time Scenario)**
- Clinical relevance: Extremely common in hospitals and home care; high injury rate.
- Starting posture: Lying or sitting on edge of bed (use low platform or actual bed).
- Execution: Subject rolls or slides off the edge, landing on side or back.
- Why real data is required: Partial occlusion by bed frame, atypical starting height, and prolonged contact with furniture before final impact.
- Recommended trials: 6.

**S08 — Assisted / Near-Fall with Recovery then Secondary Collapse**
- Clinical relevance: Subject begins to fall, catches themselves momentarily on furniture or wall, then loses grip and completes the fall.
- Execution: Initiate a lateral or backward loss of balance, briefly stabilize on a chair or wall, then release and fall.
- Why real data is required: Creates two motion peaks and a deceptive “recovery” interval that confuses temporal models.
- Recommended trials: 6.

**S09 — Fall While Carrying Object (Occlusion + Dual Motion)**
- Clinical relevance: Carrying laundry, tray, or walker.
- Execution: Subject holds a lightweight object (empty box or bag) and executes a trip or slip. The object may be dropped or held.
- Why real data is required: Object creates additional thermal mass and visual occlusion; algorithms must distinguish subject from carried item.
- Recommended trials: 5.

**S10 — Very Slow Controlled Descent into Sitting Position that Continues to Floor (False-Positive Trap)**
- Clinical relevance: Differentiates intentional floor sitting from true fall.
- Execution: Subject slowly and deliberately lowers to the floor as if sitting, then continues past the normal sitting posture into a full supine or side-lying position without a distinct impact.
- Why real data is required: Creates the exact boundary case that causes false positives in many commercial systems.
- Recommended trials: 6 (critical negative class).

---

## 4. Session Structure Recommendation

**Session A (Common Falls Focus)**  
S01 × 6, S02 × 6, S03 × 6, S05 × 4 → ~22 trials

**Session B (Elusive + High-Value)**  
S06 × 8, S07 × 6, S08 × 6, S10 × 6 → ~26 trials

**Session C (Mixed + Object/Rotation)**  
S04 × 4, S09 × 5, plus 4 free-form “worst-case” falls directed by the subject → ~15 trials

Each session should last 45–75 minutes including recovery time. Body cameras run continuously; NUC logs every “execute” and “floor contact” timestamp with nanosecond precision.

---

## 5. Data Package Deliverable per Session

- Raw thermal burst files (ESP32 binary)
- NIR video from both Jetsons
- Three body-camera AVI files
- NUC event log (JSONL)
- Output of `hm_bodycam_sync.py` → labeled CSV
- Short session notes (any deviations, subject fatigue, sensor anomalies)

This package constitutes the minimum viable labeled dataset for the next training iteration of Frameworks 2 and 3.
