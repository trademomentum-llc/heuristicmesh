# Requirements Document
## HeuristicMesh Fall Detection System (HM-FDS)
**Document Version:** 1.0  
**Classification:** Enterprise / Medical-Safety Grade  
**Owner:** Trade Momentum LLC / HeuristicMesh  
**Date:** 2026-08-11  
**Status:** Production Baseline  

### 1. Purpose
Deliver a fully edge-deployed, explainable, auditable fall-detection and emergency-response system that uses thermal sensing only (no RGB cameras), runs on the operator’s existing compute and network infrastructure, and is governed by the HeuristicMesh architectural philosophy.

### 2. Stakeholders & Success Criteria
- Primary user: elderly / high-fall-risk individual in residential or assisted-living environment  
- Operator: system owner (local control, no mandatory cloud dependency)  
- Secondary: caregivers, EMS, institutional buyers (hospitals, senior-care facilities)  
- Success = sub-2-second end-to-end alert latency from confirmed fall, false-positive rate < 3 % after calibration, full audit trail of every decision layer, zero reliance on black-box proprietary models for the final classification decision.

### 3. Functional Requirements
FR-1  Dual-thermal sensing: AMG8833 (8×8) continuous low-latency trigger + MLX90640 (32×24) high-resolution capture on trigger.  
FR-2  HeuristicMesh orchestration of four independent frameworks (Thermal Trigger, Spatial Analysis, Event Classification, Response).  
FR-3  Real-time inference on Jetson Orin Nano (int8 quantized vision encoder + rule/heuristic engine).  
FR-4  Configurable confidence threshold and multi-stage escalation (local notification → caregiver SMS/voice → EMS/911).  
FR-5  Full decision provenance: every framework output, confidence score, and mesh arbitration decision is logged with timestamp and sensor frame hash.  
FR-6  Local-only operation by default; optional encrypted outbound alert path.  
FR-7  MIDI or GPIO secondary trigger path (legacy / music / accessibility use-case compatibility).  
FR-8  Over-the-air model / heuristic update capability restricted to signed packages from the ASUS NUC control plane.

### 4. Non-Functional Requirements
NFR-1  End-to-end latency (trigger → confirmed alert) ≤ 1 800 ms under normal load.  
NFR-2  Power: sensor nodes < 1.5 W continuous; Jetson nodes able to run from PoE or local UPS.  
NFR-3  Explainability: every alert must be reconstructible from the four framework logs without access to model weights.  
NFR-4  Network isolation: system traffic never leaves the Zyxel-controlled LAN except for explicitly authorized alert destinations.  
NFR-5  Availability: 99.5 % uptime of the detection path; graceful degradation if one Jetson fails.  
NFR-6  Regulatory path readiness: design artifacts sufficient for later FDA 510(k) or CE MDR Class IIa pre-submission.

### 5. Constraints
- Existing hardware only: ASUS NUC, two Jetson Orin Nano, Zyxel USG Flex 100H, GS1200 switch, NWA90BE-class AP.  
- No cloud training or inference dependency for production inference path.  
- Jasterish language and full proprietary LLM remain long-term goals; near-term system must ship with transparent heuristics + lightweight vision encoder.  
- Sensors must share I2C bus safely (distinct addresses, proper pull-ups, bus arbitration).

### 6. Out of Scope (v1.0)
- RGB camera fusion  
- Continuous cloud streaming of thermal frames  
- Full Jasterish LLM training pipeline (tracked as Phase-2 work item)  
- Wearable or radar secondary sensors