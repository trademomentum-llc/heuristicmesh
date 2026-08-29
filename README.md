# HeuristicMesh Complete Package
## Production System + Consumer Product Definition

### Structure
- `esp32/` – production firmware (centroid + velocity + binary protocol)
- `jetson/` – production ingestion + Framework 2 daemon
- `config/` – thresholds + MQTT topic schema
- `scripts/` – flash helper, Jetson runner, body-cam log template
- `docs/` – system architecture + fall scenarios
- Human testing is currently prohibited; see `docs/Human_Testing_Safety_Gate.md` and `plan.md` for the opt-in, qualified-oversight go/no-go controls.
- `product/` – consumer node brief, schematic, mechanical, BOM

This archive consolidates the operable thermal path and the manufacturable product definition.
