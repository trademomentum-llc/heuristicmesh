# HeuristicMesh Architecture Philosophy
**Document Version:** 1.1  
**Date:** 2026-09-10  
**Source:** Owner conversation of 2026-08-11, merged into project canon  
**Status:** Canonical positioning. Does not replace `HeuristicMesh_Design_Spec.md`.

## 1. What HeuristicMesh Is (and Is Not)

HeuristicMesh is **not** the product. It is the architectural philosophy that powers the product.

Owner position (2026-08-11):

> Heuristic mesh is the underlying framework or frameworks logically... As those frameworks are meshed together to create the system that monitors and detects falls

- **Product** = the fall-detection application (thermal nodes + edge inference + alert path).
- **HeuristicMesh** = discrete, purpose-built heuristic layers bound by an orchestration mesh.
- **Mesh** = the layer that passes state between frameworks, weighs confidence at each stage, and decides when to escalate.
- Domain: `heuristicmesh.com` is owned by the project.

Owner position on why heuristics, not a black-box LLM, are the business model:

> Actually that third option of using the computer heuristics aligns amazingly with my business model because that's all an llm is doing. Is taking a bunch of computer processes and meshing them together anyway? And since I own heuristicmesh.com that might be the way I'm steering towards

## 2. Atomic Primitives

| Primitive | Definition | Testable independently? |
|-----------|------------|-------------------------|
| Framework | A discrete, purpose-built heuristic layer with a single question it answers | Yes |
| Mesh | Orchestration that passes state, weighs confidence, and decides escalation | Yes |
| Confidence | Explicit score produced by a framework, consumed by the mesh | Yes |
| Escalation | Mesh decision to promote an event to the next framework or to alert | Yes |
| Provenance | Reconstructible record of which framework fired, with what inputs and score | Yes |

An LLM, at its core, is a heuristic engine over weighted patterns. HeuristicMesh makes those heuristics explicit, layer-by-layer, instead of burying them in parameters.

## 3. Four Frameworks (Fall Detection Instantiation)

| # | Framework | Sensor / Engine | Question it answers |
|---|-----------|-----------------|---------------------|
| 1 | Thermal Trigger Heuristics | AMG8833 (8x8 = 64 px) | Is there a heat signature? Is it moving abnormally? |
| 2 | Spatial Analysis Heuristics | MLX90640 (32x24 = 768 px) | What is the body's shape, orientation, and position in space? |
| 3 | Event Classification Heuristics | Computer-vision rules | Rapid descent + horizontal posture + prolonged immobility = fall? |
| 4 | Response Heuristics | Alert logic | Has the confidence threshold been met? Escalate to future production EMS / 911 / notification paths? |

Pipeline:

1. AMG8833 - real-time thermal trigger (heat + motion anomaly).
2. MLX90640 - high-res thermal capture (body shape, posture, position).
3. Mesh layer - structured CV rules (rapid descent + horizontal position + immobility = fall confirmed).
4. Alert output - future production EMS / 911 / notification logic.

Physical interconnection, VLANs, and failure modes live in `HeuristicMesh_Design_Spec.md`.

## 4. Why This Architecture

- **Transparent** - each heuristic layer is controlled explicitly.
- **Efficient** - no massive parameter overhead; runs lean on the Jetson stack.
- **Independently testable and improvable** - a misfire is attributable to one framework.
- **Explainable at every layer** - required for medical / safety applications.
- **Domain-specific** - purpose-built for fall detection, not a general model.
- **Certifiable** - a transparent heuristic architecture documents itself; a black box does not.

Owner position on transparency as the moat:

> The business angle is much stronger with a transparent deployable medical safety system as opposed to a black box llm... I'm not going to sugarcoat it for the big Enterprise corporations + black box it myself, I think in medical and safety Fields its transparency

## 5. Jasterish Role (Phase 2, Parallel Track)

Jasterish is the proprietary language created for this project. Long-term it is the native language for defining mesh logic across frameworks.

Owner position:

> ideally what I'm doing is building an llm from a proprietary language that I created called jasterish. At that point, I would train the proprietary model on fall data

Constraint: building a from-scratch Jasterish LLM is a long-term project. It does **not** gate the fall-detection prototype.

Phased plan:
1. Ship a working fall-detection prototype on existing models + computer heuristics.
2. Develop Jasterish (language + optional LLM) in parallel.
3. Two-stage inference if a language model is used later: vision encoder produces structured features; Jasterish / mesh logic reasons over those features. Seeing is separated from deciding.

## 6. What Must Stay True

- No framework may hide its decision rule inside an uninspectable model.
- No environmental or contextual sensor (Framework 3.5) may fire an alert by itself. It may only modulate confidence.
- Every alert must be reconstructible from local logs.
- No emergency-services dispatch, clinical decision, or treatment recommendation may be based solely on prototype output.
- Human testing remains prohibited until `Human_Testing_Safety_Gate.md` is explicitly cleared.
