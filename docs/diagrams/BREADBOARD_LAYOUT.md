# HeuristicMesh Breadboard Layout Guide
## ESP32-S3 + AMG8833 + USR-TCP232 (ModBus/Ethernet)

**Version:** 1.1  
**Date:** 2026-08-30  
**Status:** Active  
**Target:** Production-Ready Breadboard Layout

---

## 🎯 Overview

This document provides a **photorealistic breadboard layout** for the HeuristicMesh system with:
- **ESP32-S3 DevKitC-1** (Primary MCU)
- **2× AMG8833** thermal sensors (8×8 arrays)
- **USR-TCP232-410S** (Serial-to-Ethernet for ModBus/TCP)
- **Power management** (3.3V regulation, decoupling)
- **Status indicators** (LEDs for power, I2C, Ethernet)
- **Protection components** (diodes, capacitors)

---

## 📋 Parts List

### Core Components
| Qty | Part | Description | Notes |
|-----|------|-------------|-------|
| 1 | ESP32-S3-DevKitC-1 | Main microcontroller | 240MHz, WiFi, BLE |
| 2 | AMG8833 | Thermal IR sensor | 8×8 array, I2C, 3.3V |
| 1 | USR-TCP232-410S | Serial-to-Ethernet | ModBus/TCP, 100Mbps |

### Required Components
| Qty | Part | Value | Purpose |
|-----|------|-------|---------|
| 4 | Resistor | 4.7 kΩ | I2C pull-ups (2 per sensor) |
| 2 | Resistor | 220 Ω | LED current limiting |
| 2 | Resistor | 10 kΩ | Push button pull-ups |
| 3 | LED | 3mm/5mm | Status indicators (Power, I2C, Ethernet) |
| 2 | Push Button | Momentary | Reset + Manual trigger |
| 3 | Capacitor | 100 nF (0.1 µF) | Decoupling (1 per sensor + 1 for ESP32) |
| 1 | Capacitor | 10 µF | Bulk decoupling |
| 2 | Capacitor | 47 µF | Power stability |
| 1 | Diode | 1N4007 | Reverse polarity protection |

### Recommended Add-ons
| Qty | Part | Description | Purpose |
|-----|------|-------------|---------|
| 1 | Level Shifter | TXB0104E | 5V ↔ 3.3V (if needed) |
| 1 | Voltage Regulator | AMS1117-3.3 | External 5V→3.3V |
| 1 | MOSFET | IRLML6401 | Power control for sensors |
| 1 | Transistor | 2N2222 | General switching |
| 1 | Header | 2.54mm pitch | For modular connections |
| 1 | Breadboard | 830/1700+ points | Main prototyping board |
| 1 | Jumper Wires | Male-Male, Male-Female | Connections |

### Power Options
| Option | Voltage | Current | Notes |
|--------|---------|---------|-------|
| USB-C | 5V | 500mA-2A | Direct to ESP32-S3 |
| External PSU | 5V/3.3V | 2A+ | For full system |
| Battery | 3.7V LiPo | 2A+ | Portable operation |

---

## 🖼️ Photorealistic Breadboard Layout

### Layout Diagram (Top View)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────┐     ┌─────────────────────────┐               │
│  │   ESP32-S3 DevKitC-1     │     │   USR-TCP232-410S        │               │
│  │                         │     │                         │               │
│  │  ┌─────┐   ┌─────┐     │     │  ┌─────┐   ┌─────┐     │               │
│  │  │USB  │   │3.3V │     │     │  │TXD │   │RXD │     │               │
│  │  └─────┘   └─────┘     │     │  └─────┘   └─────┘     │               │
│  │  ┌─────┐   ┌─────┐     │     │  ┌─────┐   ┌─────┐     │               │
│  │  │G8   │   │G9   │◄────┼─────►│GND│   │5V  │     │               │
│  │  │SDA  │   │SCL  │     │     │  └─────┘   └─────┘     │               │
│  │  └─────┘   └─────┘     │     │  ┌─────┐                 │               │
│  │  ┌─────┐   ┌─────┐     │     │  │ETH │                 │               │
│  │  │G43  │   │G44  │◄────┼─────►│TXD │                 │               │
│  │  │TX   │   │RX   │     │     │  └─────┘                 │               │
│  │  └─────┘   └─────┘     │     │                         │               │
│  │  ┌─────┐               │     │  ┌─────┐                 │               │
│  │  │G2   │◄──────────────┼─────►│RXD │                 │               │
│  │  │LED  │               │     │  └─────┘                 │               │
│  │  └─────┘               │     │                         │               │
│  └─────────────────────────┘     └─────────────────────────┘               │
│                                    │                                         │
│  ┌─────────────────────────┐     ┌─────────────────────────┐               │
│  │   AMG8833 Sensor #1      │     │   AMG8833 Sensor #2      │               │
│  │  (I2C Address: 0x69)     │     │  (I2C Address: 0x68)     │               │
│  │                         │     │                         │               │
│  │  ┌─────┐   ┌─────┐     │     │  ┌─────┐   ┌─────┐     │               │
│  │  │VDD  │◄──┼──3.3V      │     │  │VDD  │◄──┼──3.3V      │               │
│  │  └─────┘   │      │     │     │  └─────┘   │      │     │               │
│  │  ┌─────┐   │      │     │     │  ┌─────┐   │      │     │               │
│  │  │GND  │◄──┘      │     │     │  │GND  │◄──┘      │     │               │
│  │  └─────┘          │     │     │  └─────┘          │     │               │
│  │  ┌─────┐   ┌─────┐     │     │  ┌─────┐   ┌─────┐     │               │
│  │  │SDA  │◄──┼──SDA Bus  │     │  │  │SDA  │◄──┼──SDA Bus  │     │               │
│  │  └─────┘   │      │     │     │  └─────┘   │      │     │               │
│  │  ┌─────┐   │      │     │     │  ┌─────┐   │      │     │               │
│  │  │SCL  │◄──┘      │     │     │  │SCL  │◄──┘      │     │               │
│  │  └─────┘          │     │     │  └─────┘          │     │               │
│  │  ┌─────┐          │     │     │  ┌─────┐          │     │               │
│  │  │AD0  │◄──3.3V   │     │     │  │AD0  │◄──GND    │     │               │
│  │  └─────┘          │     │     │  └─────┘          │     │               │
│  └─────────────────────────┘     └─────────────────────────┘               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    POWER & STATUS SECTION                           │  │
│  │                                                                     │  │
│  │  ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐                   │  │
│  │  │5V   │───│1N4007│───│10µF │───│47µF│───┬─────┤                   │  │
│  │  └─────┘   └─────┘   └─────┘   └─────┘   │     │                   │  │
│  │                                          │     │                   │  │
│  │  ┌─────┐   ┌─────┐   ┌─────┐           │     │                   │  │
│  │  │AMS1117│───│100nF│───┬─────┘     │     │                   │  │
│  │  │3.3V   │   └─────┘   │           │     │                   │  │
│  │  └─────┘               │           │     │                   │  │
│  │  ┌─────┐               │           │     │                   │  │
│  │  │3.3V │◄──────────────┘           │     │                   │  │
│  │  └─────┘                              │     │                   │  │
│  │  ┌─────┐   ┌─────┐                  │     │                   │  │
│  │  │LED1 │◄──│220Ω │◄─────────────────┘     │                   │  │
│  │  │PWR  │   └─────┘                          │                   │  │
│  │  └─────┘                                    │                   │  │
│  │  ┌─────┐   ┌─────┐                         │                   │  │
│  │  │LED2 │◄──│220Ω │◄────────────────────────┘                   │  │
│  │  │I2C  │   └─────┘                                              │  │
│  │  └─────┘                                                           │  │
│  │  ┌─────┐   ┌─────┐                                              │  │
│  │  │LED3 │◄──│220Ω │◄──────────────────────────────────────────┘  │  │
│  │  │ETH  │   └─────┘                                                   │  │
│  │  └─────┘                                                           │  │
│  │                                                                     │  │
│  │  ┌─────┐   ┌─────┐                                              │  │
│  │  │BTN1 │   │10kΩ │◄──GND                                       │  │
│  │  │RST  │   └─────┘                                               │  │
│  │  └─────┘   ┌─────┐                                               │  │
│  │            │     │                                               │  │
│  │  ┌─────┐   │     │                                               │  │
│  │  │BTN2 │───┘     │                                               │  │
│  │  │TRIG │         │                                               │  │
│  │  └─────┘         │                                               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Detailed Wiring Diagram

### Power Distribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ POWER RAIL LAYOUT                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EXTERNAL POWER (5V)────┬─────────────────────────────────────────────────┐ │
│                         │                                                     │ │
│                         ▼                                                     │ │
│  ┌─────────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐       │ │
│  │ 1N4007 Diode │◄────│ 10µF    │◄────│ 47µF    │◄────│ 5V Rail │       │ │
│  │ (Reverse    │     │ Elect.  │     │ Elect.  │     │         │       │ │
│  │  Polarity)  │     │         │     │         │     │         │       │ │
│  └──────┬──────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘       │ │
│         │                │                │                │              │ │
│         │                │                │                │              │ │
│         ▼                ▼                ▼                ▼              │ │
│  ┌─────────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐              │ │
│  │ AMS1117-3.3V │  │ ESP32   │  │ AMG #1   │  │ AMG #2   │              │ │
│  │ Regulator    │  │ 3.3V    │  │ VDD      │  │ VDD      │              │ │
│  └──────┬──────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘              │ │
│         │             │             │             │                    │ │
│         │             │             │             │                    │ │
│         ▼             ▼             ▼             ▼                    │ │
│  ┌─────────────────────────────────────────────────────────────────────┐  │ │
│  │                        3.3V RAIL                                    │  │ │
│  └─────────────────────────────────────────────────────────────────────┘  │ │
│                                                                             │ │
│  GND Distribution:                                                          │ │
│  ┌─────────────────────────────────────────────────────────────────────┐  │ │
│  │ All components share common GND rail connected to:                  │  │ │
│  │ - ESP32-S3 GND                                                           │  │ │
│  │ - AMG8833 #1 GND                                                          │  │ │
│  │ - AMG8833 #2 GND                                                          │  │ │
│  │ - USR-TCP232 GND                                                         │  │ │
│  │ - All LED cathodes                                                      │  │ │
│  │ - All pull-down resistors                                                │  │ │
│  └─────────────────────────────────────────────────────────────────────┘  │ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Signal Wiring

### I2C Bus (Shared between ESP32-S3 and 2× AMG8833)

```
ESP32-S3 I2C Bus:
├── GPIO 8 (SDA)────┬──4.7kΩ──┬────────────────────────────────────────┐
│                   │          │                                    │
│                   ▼          ▼                                    ▼
│              AMG8833 #1    AMG8833 #2                    3.3V Rail
│                 SDA          SDA                        (Pull-up)
│                   ▲          ▲                                    ▲
├── GPIO 9 (SCL)────┴──4.7kΩ──┴────────────────────────────────────────┘
│
│
└── GND─────────────────────────────────────────────────────────────────┘

I2C Address Configuration:
├── AMG8833 #1: AD0 → 3.3V → Address = 0x69
└── AMG8833 #2: AD0 → GND → Address = 0x68
```

### UART Bus (ESP32-S3 ↔ USR-TCP232)

```
ESP32-S3 UART:
├── GPIO 43 (TX)──────────────► USR-TCP232 RXD
│
├── GPIO 44 (RX)──────────────◄ USR-TCP232 TXD
│
└── GND───────────────────────┬────────────────────────────────────────┐
                                │                                    │
                                ▼                                    ▼
                           USR-TCP232 GND              USR-TCP232 VCC
                                                   (Connect to 5V)
```

### Status LEDs

```
Power LED (LED1):
├── Anode → 220Ω → 3.3V Rail
└── Cathode → GND

I2C Activity LED (LED2):
├── Anode → 220Ω → GPIO 2 (ESP32-S3)
└── Cathode → GND

Ethernet Activity LED (LED3):
├── Anode → 220Ω → USR-TCP232 Link Status (if available)
└── Cathode → GND
```

---

## 🏗️ Step-by-Step Assembly Guide

### Step 1: Prepare the Breadboard

1. **Place ESP32-S3 DevKitC-1** on the left side of the breadboard
2. **Place USR-TCP232** on the right side, parallel to ESP32
3. **Leave center area** for AMG8833 sensors and power components

### Step 2: Power Distribution

1. **Connect 5V power source** to breadboard positive rail
2. **Add reverse polarity protection diode (1N4007)**
3. **Add bulk decoupling capacitors** (10µF + 47µF) on 5V rail
4. **Add voltage regulator (AMS1117-3.3V)** if using external 5V
5. **Create 3.3V rail** across breadboard
6. **Add 100nF decoupling capacitor** near regulator output
7. **Connect GND rail** across entire breadboard

### Step 3: Install AMG8833 Sensors

**For AMG8833 #1 (Address 0x69):**
1. Connect VDD → 3.3V rail
2. Connect GND → GND rail
3. Connect SDA → ESP32-S3 GPIO 8
4. Connect SCL → ESP32-S3 GPIO 9
5. Connect AD0 → 3.3V rail (sets address to 0x69)
6. Add 4.7kΩ pull-up resistor from SDA to 3.3V
7. Add 4.7kΩ pull-up resistor from SCL to 3.3V
8. Add 100nF decoupling capacitor near sensor

**For AMG8833 #2 (Address 0x68):**
1. Connect VDD → 3.3V rail
2. Connect GND → GND rail
3. Connect SDA → ESP32-S3 GPIO 8 (shared bus)
4. Connect SCL → ESP32-S3 GPIO 9 (shared bus)
5. Connect AD0 → GND rail (sets address to 0x68)
6. Add 4.7kΩ pull-up resistor from SDA to 3.3V
7. Add 4.7kΩ pull-up resistor from SCL to 3.3V
8. Add 100nF decoupling capacitor near sensor

### Step 4: Install USR-TCP232

1. Connect VCC → 5V rail
2. Connect GND → GND rail
3. Connect TXD → ESP32-S3 GPIO 44 (RX)
4. Connect RXD → ESP32-S3 GPIO 43 (TX)
5. Connect Ethernet port to network switch (VLAN 30)

### Step 5: Add Status Indicators

1. **Power LED (LED1):**
   - Anode (+) → 220Ω resistor → 3.3V rail
   - Cathode (-) → GND rail

2. **I2C Activity LED (LED2):**
   - Anode (+) → 220Ω resistor → GPIO 2
   - Cathode (-) → GND rail

3. **Ethernet LED (LED3):**
   - Anode (+) → 220Ω resistor → USR-TCP232 (if link status pin available)
   - Cathode (-) → GND rail

### Step 6: Add Push Buttons

1. **Reset Button (BTN1):**
   - One side → ESP32-S3 EN (Enable) pin
   - Other side → GND
   - Add 10kΩ pull-up to 3.3V (ESP32 has internal pull-up, but external is more reliable)

2. **Manual Trigger Button (BTN2):**
   - One side → Any available GPIO (e.g., GPIO 3)
   - Other side → GND
   - Add 10kΩ pull-up to 3.3V

---

## 📐 Physical Layout Coordinates

For precise breadboard placement:

```
Breadboard Grid (Columns A-J, Rows 1-60):

ESP32-S3 DevKitC-1:
├── Position: A1 - J30 (spans 10 columns × 30 rows)
├── USB-C: Right side (J25-J30)
├── 3.3V Pin: B15
├── GND Pin: C15
├── GPIO 8 (SDA): D10
├── GPIO 9 (SCL): D11
├── GPIO 43 (TX): E20
├── GPIO 44 (RX): E21
├── GPIO 2 (LED): F5
└── EN Pin: G3

USR-TCP232:
├── Position: A31 - H60 (right side)
├── VCC: A35
├── GND: B35
├── TXD: C38
├── RXD: D38
├── Ethernet: Right edge (A40-H60)
└── Status LEDs: Built-in

AMG8833 #1:
├── Position: L1 - S15 (top center)
├── VDD: L5 → 3.3V rail
├── GND: M5 → GND rail
├── SDA: N10 → I2C SDA bus
├── SCL: O10 → I2C SCL bus
└── AD0: P10 → 3.3V rail

AMG8833 #2:
├── Position: L16 - S30 (bottom center)
├── VDD: L20 → 3.3V rail
├── GND: M20 → GND rail
├── SDA: N25 → I2C SDA bus
├── SCL: O25 → I2C SCL bus
└── AD0: P25 → GND rail

Power Section:
├── 5V Rail: Column 1, Rows 1-60
├── 3.3V Rail: Column 2, Rows 1-60
├── GND Rail: Columns 3-4, Rows 1-60
├── AMS1117: E1-E5
├── 1N4007: D1-D3
├── 10µF Cap: E6-F6
├── 47µF Cap: E7-F7
└── 100nF Cap: G8-H8

Status LEDs:
├── LED1 (Power): A60, B60 (220Ω resistor)
├── LED2 (I2C): C60, D60 (220Ω resistor)
└── LED3 (ETH): E60, F60 (220Ω resistor)

Buttons:
├── BTN1 (Reset): G60, H60 (10kΩ pull-up)
└── BTN2 (Trigger): I60, J60 (10kΩ pull-up)
```

---

## 🔌 Pin Configuration Summary

### ESP32-S3 DevKitC-1 Pinout

| Pin | Function | Connection | Notes |
|-----|----------|------------|-------|
| 3.3V | Power Out | AMG8833 VDD ×2 | Max 600mA total |
| GND | Ground | All components | Common ground |
| EN | Enable | Reset button | Active high |
| GPIO 2 | Status LED | LED2 (I2C activity) | Built-in LED on some boards |
| GPIO 3 | Input | Manual trigger button | Optional |
| GPIO 8 | I2C SDA | AMG8833 #1 & #2 SDA | Shared bus |
| GPIO 9 | I2C SCL | AMG8833 #1 & #2 SCL | Shared bus |
| GPIO 43 | UART TX | USR-TCP232 RXD | Serial out |
| GPIO 44 | UART RX | USR-TCP232 TXD | Serial in |

### AMG8833 Pinout (Both Sensors)

| Pin | Function | Connection | Notes |
|-----|----------|------------|-------|
| VDD | Power | 3.3V rail | 3.3V only |
| GND | Ground | GND rail | Common ground |
| SDA | I2C Data | ESP32 GPIO 8 | Shared bus |
| SCL | I2C Clock | ESP32 GPIO 9 | Shared bus |
| AD0 | Address | 3.3V or GND | 0x69 or 0x68 |
| INT | Interrupt | Optional | Not used in this config |

### USR-TCP232 Pinout

| Pin | Function | Connection | Notes |
|-----|----------|------------|-------|
| VCC | Power | 5V rail | 5V required |
| GND | Ground | GND rail | Common ground |
| TXD | Transmit | ESP32 GPIO 44 | To ESP32 RX |
| RXD | Receive | ESP32 GPIO 43 | To ESP32 TX |
| ETH | Ethernet | Network switch | VLAN 30 |

---

## 💡 Advanced Configuration (Optional)

### Adding Transistors for Power Control

**N-Channel MOSFET (IRLML6401) for Sensor Power:**
```
3.3V Rail────┬────────────────────────────────────────┐
             │                                    │
             ▼                                    ▼
  ┌─────────────┐                    ┌─────────────┐
  │ IRLML6401   │                    │ AMG8833     │
  │ MOSFET      │                    │ Sensors     │
  │             │                    │             │
  │ D (Drain)   │◄───────────────────│ VDD         │
  │ G (Gate)    │◄──GPIO 5 (ESP32)    │             │
  │ S (Source)  │────► GND Rail       │             │
  └─────────────┘                    └─────────────┘
```

**Benefits:**
- Software power cycling for sensors
- Reduced power consumption
- Hardware reset capability
- Control via GPIO 5

### Adding Level Shifter (TXB0104E)

If mixing 5V and 3.3V signals:
```
ESP32 GPIO 8 (3.3V)────► TXB0104E LV1 (3.3V side)
TXB0104E HV1 (5V side)────► External 5V device

TXB0104E OE─────────────► 3.3V (Enable)
TXB0104E GND────────────► GND
```

### Adding Ethernet Directly (ESP32-S3 Ethernet variant)

If using ESP32-S3 with built-in Ethernet:
- Replace USR-TCP232 with Ethernet PHY
- Connect RMII/RMII signals
- Reduces component count

---

## 🔍 Testing & Verification

### Step 1: Power On Test
1. Connect power source
2. Verify Power LED (LED1) illuminates
3. Check 3.3V rail voltage: **3.25-3.35V**
4. Check 5V rail voltage: **4.9-5.1V**

### Step 2: I2C Bus Test
```bash
# Run I2C scan from ESP32 serial monitor
# Expected output:
# [SYS] Device found at 0x68
# [SYS] Device found at 0x69
```

### Step 3: Sensor Test
```bash
# Verify AMG8833 initialization
# Expected output:
# [OK] AMG8833 ready (for both sensors)
```

### Step 4: UART Test
```bash
# Send test message from ESP32 to USR-TCP232
# Verify message received on network
ping 192.168.30.10  # USR-TCP232 IP
```

### Step 5: Full System Test
1. Connect to Jetson via USB
2. Run ingestion script
3. Verify frames streaming at ~20Hz
4. Test fall detection with hand movement

---

## 📊 Performance Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| I2C Speed | 400 kHz | Fast Mode |
| UART Speed | 115200 baud | For USR-TCP232 |
| USB Speed | 921600 baud | Direct to Jetson |
| AMG8833 Frame Rate | 10-20 Hz | Configurable |
| Power Consumption | ~500mA | Full system |
| Operating Voltage | 3.3V/5V | Dual rail |
| Temperature Range | -20°C to +80°C | AMG8833 spec |
| Accuracy | ±2.5°C | Typical |

---

## 🛡️ Safety & Best Practices

### ⚠️ Critical Warnings

1. **Never connect 5V to AMG8833 VDD** - Sensor is 3.3V only!
2. **Never connect 5V to ESP32-S3 GPIO** - Not 5V tolerant!
3. **Use separate power supplies** for high-current devices
4. **Add fuse or PTC** for overcurrent protection
5. **Verify polarity** before powering on

### ✅ Best Practices

1. **Use shielded cables** for I2C bus > 30cm
2. **Keep I2C bus short** (< 50cm for 400kHz)
3. **Add decoupling capacitors** near each sensor
4. **Use twisted pairs** for SDA/SCL signals
5. **Label all connections** for future maintenance
6. **Test each component** before full assembly
7. **Use color-coded wires** (Red=3.3V, Black=GND, etc.)

---

## 📚 Reference Images

### Recommended Breadboard Layout

```
Visual representation (approximate):

┌─────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ ESP32-S3    │    │ AMG8833 #1  │    │    USR-TCP232        │  │
│  │             │    │ (0x69)       │    │                     │  │
│  │ ┌───────┐   │    │ ┌───────┐    │    │  ┌───────┐          │  │
│  │ │ USB  │   │    │ │       │    │    │  │ ETH   │          │  │
│  │ └───────┘   │    │ │       │    │    │  │       │          │  │
│  │             │    │ │       │    │    │  └───────┘          │  │
│  │ ┌───────┐   │    │ └───────┘    │    │                     │  │
│  │ │ 3.3V │───┼────► VDD         │    │  ┌───────┐          │  │
│  │ └───────┘   │    │ ┌───────┐    │    │  │ VCC   │◄─────────┘  │
│  │             │    │ │ GND   │    │    │  │ 5V    │  5V Rail   │
│  │ ┌───────┐   │    │ └───────┘    │    │  └───────┘          │  │
│  │ │ G8   │───┼────► SDA         │    │                     │  │
│  │ │ SDA  │   │    │ ┌───────┐    │    │  ┌───────┐          │  │
│  │ └───────┘   │    │ │ SCL   │    │    │  │ RXD   │◄─────┘  │
│  │             │    │ └───────┘    │    │  │       │    TXD    │
│  │ ┌───────┐   │    │ ┌───────┐    │    │  └───────┘          │  │
│  │ │ G9   │───┼────► SCL         │    │                     │  │
│  │ │ SCL  │   │    │ └───────┘    │    │  ┌───────┐          │  │
│  │ └───────┘   │    │ ┌───────┐    │    │  │ GND   │◄─────────┘  │
│  │             │    │ │ AD0   │    │    │  └───────┘  GND Rail │
│  │ ┌───────┐   │    │ └───────┘    │    │                     │  │
│  │ │ G43  │───┼─────────────────► RXD │    │                     │  │
│  │ │ TX   │   │    │ ┌───────┐    │    │                     │  │
│  │ └───────┘   │    │ │ AD0   │◄──┘    │    │                     │  │
│  │             │    │ └───────┘    │    │                     │  │
│  │ ┌───────┐   │    └─────────────┘    │    └─────────────────────┘  │
│  │ │ G44  │───┼─────────────────► TXD │    ┌─────────────────────┐  │
│  │ │ RX   │   │    ┌─────────────┐    │    │    AMG8833 #2       │  │
│  │ └───────┘   │    │ AMG8833 #2  │    │    │    (0x68)            │  │
│  └─────────────┘    │ (0x68)       │    │    └─────────────────────┘  │
│                    │ ┌───────┐    │                              │
│                    │ │ VDD   │◄──┘                              │
│                    │ └───────┘    │                              │
│                    │ ┌───────┐    │                              │
│                    │ │ GND   │◄──────────────────────────────┘              │
│                    │ └───────┘    │                              │
│                    │ ┌───────┐    │                              │
│                    │ │ SDA   │◄──┘                              │
│                    │ └───────┘    │                              │
│                    │ ┌───────┐    │                              │
│                    │ │ SCL   │◄──┘                              │
│                    │ └───────┘    │                              │
│                    │ ┌───────┐    │                              │
│                    │ │ AD0   │◄──────────────────────────────┘              │
│                    │ └───────┘    │                              │
│                    └─────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Troubleshooting Guide

### Common Issues & Solutions

| Issue | Symptom | Cause | Solution |
|-------|---------|-------|----------|
| No power | LEDs off | No 5V input | Check power supply, diode, connections |
| ESP32 not detected | No serial output | USB driver | Install CP210x/CH340 driver |
| I2C scan empty | No devices found | Wiring error | Check SDA, SCL, pull-ups, power |
| Wrong I2C address | Device not at expected addr | AD0 misconfigured | Verify AD0 pull-up/down |
| Sensor read errors | Garbled data | Noise on I2C | Add decoupling caps, shorten wires |
| USR-TCP232 not responding | No Ethernet | IP config | Check USR-TCP232 settings |
| Overheating | Hot components | Excessive current | Check power, add heat sinks |

### Debug Commands

```bash
# ESP32 Serial Monitor (921600 baud)
# Run I2C scan
# Expected: Found 0x68, Found 0x69

# Test USR-TCP232
nc 192.168.30.10 502  # Test ModBus/TCP connection

# Check network
ping 192.168.30.10
arp -a
```

---

## 📝 Changelog

### v1.1 (2026-08-30)
- Updated for AMG8833-only configuration
- Removed MLX90640 references
- Added USR-TCP232 Ethernet/ModBus support
- Added comprehensive power management
- Added status LEDs and buttons

### v1.0 (2026-08-29)
- Initial version with AMG8833 and MLX90640

---

**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-30  
**Version:** 1.1
