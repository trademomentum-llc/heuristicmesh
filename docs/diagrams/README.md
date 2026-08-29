# HeuristicMesh Photorealistic Diagrams

This directory contains **photorealistic diagram definitions** for the HeuristicMesh fall detection system. All diagrams are provided in multiple formats to support different rendering tools.

---

## 📁 Available Diagrams

| Diagram | File | Format | Description |
|---------|------|--------|-------------|
| **System Architecture** | `SYSTEM_ARCHITECTURE.md` | PlantUML, Graphviz | Complete system overview with all components |
| **Hardware Wiring** | `HARDWARE_WIRING.md` | PlantUML, Graphviz | ESP32-S3 + AMG8833 + USR-TCP232 connections |
| **Data Flow** | `DATA_FLOW.md` | PlantUML, Graphviz | End-to-end data pipeline |
| **VLAN Topology** | `VLAN_TOPOLOGY.md` | PlantUML, Graphviz | Network infrastructure with VLANs |
| **MQTT Topics** | `MQTT_TOPICS.md` | PlantUML | Complete MQTT topic hierarchy |

---

## 🎨 Rendering Options

### Quick Start (Online Renderers)

#### 1. **PlantUML Web Server** (Recommended)
- Go to: [http://www.plantuml.com/plantuml/](http://www.plantuml.com/plantuml/)
- Copy/paste any PlantUML code from the `.md` files
- Download as PNG/SVG/LaTeX

#### 2. **Mermaid Live Editor**
- Go to: [https://mermaid.live/](https://mermaid.live/)
- Copy/paste Mermaid code
- Download as PNG/SVG

#### 3. **Graphviz Online**
- Go to: [https://dreampuf.github.io/GraphvizOnline/](https://dreampuf.github.io/GraphvizOnline/)
- Copy/paste DOT code
- Download as PNG/SVG

---

### Local Rendering

#### PlantUML (Best for Photorealistic)

1. **Install Java:**
   ```bash
   sudo apt install default-jre
   ```

2. **Download PlantUML:**
   ```bash
   wget https://github.com/plantuml/plantuml/releases/download/v1.2024.0/plantuml-1.2024.0.jar
   ```

3. **Render a Diagram:**
   ```bash
   # Extract PlantUML code from markdown
   grep -A 1000 "@startuml" SYSTEM_ARCHITECTURE.md > system.puml
   
   # Render to PNG
   java -jar plantuml-1.2024.0.jar -tpng system.puml
   
   # Render to SVG (vector, scalable)
   java -jar plantuml-1.2024.0.jar -tsvg system.puml
   ```

4. **Batch Render All Diagrams:**
   ```bash
   #!/bin/bash
   for file in *.md; do
       # Extract first PlantUML diagram
       awk '/@startuml/,/^@enduml/' "$file" > "${file%.md}.puml"
       java -jar plantuml-1.2024.0.jar -tpng "${file%.md}.puml"
   done
   ```

#### Graphviz (DOT)

1. **Install Graphviz:**
   ```bash
   sudo apt install graphviz
   ```

2. **Render:**
   ```bash
   dot -Tpng system_architecture.dot -o system_architecture.png
   ```

3. **Render All:**
   ```bash
   for file in *.dot; do
       dot -Tpng "$file" -o "${file%.dot}.png"
   done
   ```

#### Mermaid CLI

1. **Install Mermaid CLI:**
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Render:**
   ```bash
   mmdc -i data_flow.mmd -o data_flow.png
   ```

---

## 🎯 Diagram Descriptions

### 1. System Architecture (`SYSTEM_ARCHITECTURE.md`)

**Shows:** All hardware components and their connections
- **Sensor Layer:** 3× ESP32-S3, 1× ESP32-S2-WROOM, 2× AMG8833
- **Network Layer:** Zyxel USG Flex 100H, GS1200 Switch, NWA90BE AP, USR-TCP232
- **Compute Layer:** 2× Jetson Orin Nano
- **Control Plane:** ASUS NUC with MQTT
- **Alert Layer:** Caregiver tablets, EMS/911, local alarms
- **Ground Truth:** IR body cams, IR cameras

**Best for:** Understanding the complete system at a high level

### 2. Hardware Wiring (`HARDWARE_WIRING.md`)

**Shows:** Detailed wiring for ESP32-S3 + AMG8833 + USR-TCP232
- I2C connections (SDA, SCL)
- Pull-up resistors (4.7kΩ)
- UART connections (TX, RX)
- USB connections
- Power connections (3.3V, 5V)
- Pin assignments (GPIO 8, 9, 43, 44)

**Best for:** Physical hardware setup and troubleshooting

### 3. Data Flow (`DATA_FLOW.md`)

**Shows:** How data moves through the system
- AMG8833 continuous polling → ESP32
- Fall candidate detection → MLX90640 burst capture
- USB serial → Jetson ingest
- Framework 1 → Framework 2 → Framework 3 → Framework 4
- Provenance logging
- MQTT publishing
- Alert routing
- Ground truth sync

**Best for:** Software development and debugging

### 4. VLAN Topology (`VLAN_TOPOLOGY.md`)

**Shows:** Network infrastructure with VLAN isolation
- VLAN 10: Management (NUC, MQTT, switch management)
- VLAN 20: Inference (Jetson A, Jetson B)
- VLAN 30: Sensors (ESP32s, USR-TCP232)
- VLAN 40: Alert (AP, caregiver tablets)
- Firewall rules and ACLs
- Inter-VLAN routing

**Best for:** Network configuration and security planning

### 5. MQTT Topics (`MQTT_TOPICS.md`)

**Shows:** Complete MQTT topic hierarchy
- Framework 1 topics (telemetry, status, fall_flag)
- Framework 2 topics (event, debug)
- Framework 3 topics (classified)
- Framework 4 topics (alert, log)
- System topics (heartbeat, config)
- Framework 3.5 topics (environmental sensors)
- Payload formats for each topic

**Best for:** MQTT integration and message handling

---

## 📐 Diagram Style Guide

All diagrams follow these photorealistic styling conventions:

### Colors
| Category | Color | Hex Code | RGB |
|----------|-------|----------|-----|
| Sensors | Light Pink | #FFE4E1 | 255, 228, 225 |
| Compute | Light Purple | #E6E6FA | 230, 230, 250 |
| Network | Light Blue | #F0F8FF | 240, 248, 255 |
| Control | Light Gold | #FFFACD | 255, 250, 205 |
| Ground Truth | Beige | #F5F5DC | 245, 245, 220 |
| Data | White | #FFFFFF | 255, 255, 255 |

### Line Styles
| Type | Style | Color | Thickness |
|------|-------|-------|-----------|
| Power | Solid | Red (#FF0000) | 2px |
| I2C | Dashed | Blue (#0000FF) | 2px |
| UART | Dashed | Green (#00AA00) | 2px |
| Ethernet | Solid | Gray (#666666) | 2px |
| USB | Solid | Brown (#8B4513) | 2px |
| Fall Path | Solid | Red (#FF0000) | 3px |
| Normal Path | Solid | Blue (#0000FF) | 2px |

### Fonts
- **Primary:** Arial
- **Size:** 11-12pt for body, 14pt for titles
- **Weight:** Bold for headers, normal for body

---

## 🔧 Customization

### Modify Colors
In PlantUML, change the style definitions:
```plantuml
<style>
    .sensor {
        BackgroundColor #FFC0CB  // Change to lighter pink
        BorderColor #FF1493
    }
</style>
```

### Add Components
Edit the diagram definitions to add new hardware:
```plantuml
component "MLX90640" as MLX <<sensor>>
ESP32 --> MLX : "I2C 0x33"
```

### Change Layout
```plantuml
' Change direction
left to right direction

' Or top to bottom
top to bottom direction
```

---

## 📦 Output Formats

| Format | Extension | Use Case | Quality |
|--------|-----------|----------|---------|
| PNG | .png | Presentations, documents | High |
| SVG | .svg | Web, scalable graphics | Best |
| PDF | .pdf | Print, professional docs | Best |
| LaTeX | .tex | Academic papers | High |
| EPS | .eps | Vector graphics | High |

---

## 💡 Tips for Best Results

1. **For presentations:** Use PNG at 300 DPI
2. **For documentation:** Use SVG for scalability
3. **For printing:** Use PDF or EPS
4. **For web:** Use SVG with CSS styling
5. **For professional diagrams:** Use PlantUML with custom styles

---

## 🔗 External Resources

- [PlantUML Documentation](https://plantuml.com/)
- [Graphviz Documentation](https://graphviz.org/doc/info/lang.html)
- [Mermaid Documentation](https://mermaid.js.org/)
- [PlantUML Color Codes](https://www.rapidtables.com/web/color/RGB_Color.html)
- [Color Hex Picker](https://htmlcolorcodes.com/)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-29 | Initial release with 5 diagrams |

---

**Need a different format?** The diagrams can be converted to:
- Visio (via SVG import)
- Adobe Illustrator (via SVG import)
- CAD software (via DXF export from Graphviz)
- 3D models (via specialized tools)

Contact the engineering team for custom diagram requests.
