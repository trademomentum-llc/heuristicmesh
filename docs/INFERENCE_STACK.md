# Inference Stack
**Snapshot Date:** 2026-08-11 conversation snapshot

## Models Discussed for the Prototype

As of 2026-08-11, the candidate models running int8 on Jetson were:

- DeepSeek 3B - text-only
- Qwen 2.5B - primarily text
- Qwen 6.5B - primarily text
- Llama 7B - text-only

Owner question recorded in the conversation: were these models multimodal?  
Recorded answer: no.

Thermal data therefore needs a vision model trained or fine-tuned on infrared data, not a text LLM.

## Vision Path for Fall Detection

1. MLX90640 frames are captured during an alert window opened by the AMG8833 trigger.
2. A quantized vision model evaluates the thermal sequence for posture collapse, rapid position change, and immobility.
3. The model produces a confidence score.
4. The mesh and alert logic act only if the confidence threshold is met.

False positives that must not alert:

- sitting down
- bending over

## Prototype Implementation Options

- Use a pre-trained thermal fall model
- Fine-tune a vision model for thermal fall detection
- Use CV plus heuristics such as skeleton and motion analysis
- Adapt YOLO or MediaPipe Pose to thermal data
- Follow the existing specification direction: YOLOv8n-pose thermal-adapted or MobileNet-V3 with a pose head, quantized to int8

## Two-Stage Reasoning Constraint

If a language model is used later, the system should stay split into two stages:

1. Vision encoder produces structured features from thermal frames.
2. Mesh or Jasterish logic reasons over those structured features.

Do not feed raw thermal pixels to an LLM.

## Latency Targets

- AMG trigger: <= 50 ms
- MLX transfer: <= 200 ms
- Jetson inference: <= 80-100 ms
- Mesh plus alert: <= 100 ms
- End to end: <= 1800 ms

## Phase Separation

Jasterish as a from-scratch LLM is a Phase 2 parallel track and must not block the prototype. Training hardware mentioned in the conversation was Jetson plus an Nvidia K80.
