# HeuristicMesh Breadboard Wiring Guide
## Complete Connection Reference

**Version:** 1.1  
**Date:** 2026-08-30  
**Status:** Active  
**Purpose:** Step-by-step wiring instructions with visual references

---

## 📚 Quick Reference Tables

### Color Coding Standard

| Function | Color | Notes |
|----------|-------|-------|
| 5V Power | Red | Primary power rail |
| 3.3V Power | Orange/Yellow | Regulated power |
| GND | Black | Common ground |
| SDA (I2C Data) | Blue | Shared bus |
| SCL (I2C Clock) | Green | Shared bus |
| UART TX | Purple | ESP32 to USR-TCP232 |
| UART RX | Gray | USR-TCP232 to ESP32 |
| GPIO | White | General purpose |
| Status LED | Any | Color-coded by function |

---

## 🔌 Connection-by-Connection Guide

### Connection 1: Power Input

**Purpose:** Provide 5V power to the system

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 1: POWER INPUT                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  EXTERNAL POWER SOURCE                                               │
│       │                                                             │
│       ├── Red Wire (5V+)                                             │
│       │                                                             │
│       ▼                                                             │
│  ┌────────┐                                                         │
│  │ 1N4007 │  ← Diode (Cathode to breadboard)                       │
│  │ Diode  │    Anode: External 5V+                                  │
│  │        │    Cathode: Breadboard 5V rail                         │
│  └────┬───┘                                                         │
│       │                                                             │
│       ▼                                                             │
│  BREADBOARD 5V RAIL (Column A, all rows)                            │
│       │                                                             │
│       ▼                                                             │
│  ┌────────┐                                                         │
│  │ 10µF   │  ← Electrolytic Capacitor                              │
│  │ Cap    │    (+) to 5V rail                                       │
│  │        │    (-) to GND rail                                      │
│  └────┬───┘                                                         │
│       │                                                             │
│       ▼                                                             │
│  GND RAIL (Column B, all rows)                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Components Used:**
- 1× 1N4007 diode (reverse polarity protection)
- 1× 10µF electrolytic capacitor (bulk decoupling)

**Verification:**
- Measure voltage across 5V rail and GND: **4.9-5.1V**
- Diode should be oriented with **cathode (banded end) toward breadboard**

---

### Connection 2: 3.3V Regulation

**Purpose:** Convert 5V to 3.3V for ESP32 and sensors

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 2: 3.3V REGULATION                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FROM 5V RAIL                                                       │
│       │                                                             │
│       ▼                                                             │
│  ┌────────┐                                                         │
│  │ AMS1117 │  ← 3.3V Voltage Regulator                              │
│  │ 3.3V    │    IN: 5V rail                                         │
│  │ Reg     │    OUT: 3.3V rail                                      │
│  │        │    GND: GND rail                                       │
│  └────┬───┬───┬───┘                                                 │
│       │   │   │                                                     │
│       │   │   ▼                                                     │
│       │   │  ┌────────┐                                             │
│       │   │  │ GND    │  ← Regulator GND pin                          │
│       │   │  └────────┘                                             │
│       │   │                                                          │
│       │   ▼                                                          │
│       │  ┌────────┐                                                  │
│       │  │ OUT    │  ← 3.3V Output                                   │
│       │  └────┬───┘                                                  │
│       │       │                                                      │
│       ▼       ▼                                                      │
│  ┌────────┐  ┌────────┐                                             │
│  │ 47µF   │  │ 100nF  │  ← Additional decoupling                       │
│  │ Cap    │  │ Cap    │    Both: (+) to 3.3V rail, (-) to GND         │
│  └────────┘  └────────┘                                             │
│       │                                                             │
│       ▼                                                             │
│  BREADBOARD 3.3V RAIL (Column C, all rows)                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Components Used:**
- 1× AMS1117-3.3V voltage regulator
- 1× 47µF electrolytic capacitor (bulk decoupling)
- 1× 100nF ceramic capacitor (high-frequency decoupling)

**Verification:**
- Measure voltage across 3.3V rail and GND: **3.25-3.35V**
- Regulator should not get hot (if it does, check current draw)

---

### Connection 3: ESP32-S3 Power

**Purpose:** Power the ESP32-S3 DevKitC-1

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 3: ESP32-S3 POWER                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ESP32-S3 DevKitC-1                                                 │
│       │                                                             │
│       ├── 3.3V Pin                                                  │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD 3.3V RAIL (Column C)                            │
│       │                                                             │
│       ├── GND Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD GND RAIL (Column B)                             │
│       │                                                             │
│       ├── 5V Pin (USB)                                               │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD 5V RAIL (Column A)                              │
│       │    (Optional - for USB power)                               │
│       │                                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Note:** ESP32-S3 DevKitC-1 has **three power options**:
1. **USB-C** (5V) - Simplest for development
2. **5V Pin** - From external 5V supply
3. **3.3V Pin** - From regulated 3.3V rail

**Recommendation:** Use **USB-C** for development, **3.3V rail** for breadboard power

---

### Connection 4: AMG8833 #1 (Address 0x69)

**Purpose:** Connect first thermal sensor

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 4: AMG8833 #1 (I2C Address 0x69)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AMG8833 Sensor #1                                                  │
│       │                                                             │
│       ├── VDD Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD 3.3V RAIL (Column C)                            │
│       │                                                             │
│       ├── GND Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD GND RAIL (Column B)                             │
│       │                                                             │
│       ├── SDA Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ┌────────┐                                                 │
│       │  │ 4.7kΩ  │  ← Pull-up resistor                               │
│       │  │ Res   │    One end: SDA pin                                │
│       │  └────┬───┘    Other end: 3.3V rail                          │
│       │       │                                                        │
│       │       ▼                                                        │
│       │  I2C SDA BUS (Blue wire)                                     │
│       │    Connects to: ESP32 GPIO 8, AMG8833 #2 SDA                 │
│       │                                                             │
│       ├── SCL Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ┌────────┐                                                 │
│       │  │ 4.7kΩ  │  ← Pull-up resistor                               │
│       │  │ Res   │    One end: SCL pin                                │
│       │  └────┬───┘    Other end: 3.3V rail                          │
│       │       │                                                        │
│       │       ▼                                                        │
│       │  I2C SCL BUS (Green wire)                                    │
│       │    Connects to: ESP32 GPIO 9, AMG8833 #2 SCL                 │
│       │                                                             │
│       └── AD0 Pin                                                   │
│            │                                                         │
│            ▼                                                         │
│       BREADBOARD 3.3V RAIL (Column C)                               │
│            Sets I2C address to 0x69                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Components Used:**
- 1× AMG8833 thermal sensor
- 2× 4.7kΩ resistors (I2C pull-ups)
- 1× 100nF capacitor (optional, near sensor)

**Verification:**
- I2C scan should show device at **0x69**
- Test with `amg.readPixels()` - should return valid data

---

### Connection 5: AMG8833 #2 (Address 0x68)

**Purpose:** Connect second thermal sensor

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 5: AMG8833 #2 (I2C Address 0x68)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AMG8833 Sensor #2                                                  │
│       │                                                             │
│       ├── VDD Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD 3.3V RAIL (Column C)                            │
│       │                                                             │
│       ├── GND Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD GND RAIL (Column B)                             │
│       │                                                             │
│       ├── SDA Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  I2C SDA BUS (Blue wire)                                     │
│       │    Already connected to ESP32 GPIO 8 and AMG8833 #1        │
│       │                                                             │
│       ├── SCL Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  I2C SCL BUS (Green wire)                                    │
│       │    Already connected to ESP32 GPIO 9 and AMG8833 #1        │
│       │                                                             │
│       └── AD0 Pin                                                   │
│            │                                                         │
│            ▼                                                         │
│       BREADBOARD GND RAIL (Column B)                                │
│            Sets I2C address to 0x68                                │
│            (Different from #1 to avoid address conflict)            │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Components Used:**
- 1× AMG8833 thermal sensor
- 2× 4.7kΩ resistors (I2C pull-ups - can share with #1)
- 1× 100nF capacitor (optional, near sensor)

**Verification:**
- I2C scan should show devices at **0x68 and 0x69**
- Both sensors should respond to read commands

---

### Connection 6: I2C Pull-Up Resistors

**Purpose:** Ensure reliable I2C communication

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 6: I2C PULL-UP RESISTORS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  I2C SDA BUS (Blue wire)                                           │
│       │                                                             │
│       ├── 4.7kΩ Resistor #1 (Near ESP32)                            │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  3.3V RAIL                                                  │
│       │                                                             │
│       ├── 4.7kΩ Resistor #2 (Near AMG8833 #1)                       │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  3.3V RAIL                                                  │
│       │                                                             │
│  I2C SCL BUS (Green wire)                                          │
│       │                                                             │
│       ├── 4.7kΩ Resistor #3 (Near ESP32)                            │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  3.3V RAIL                                                  │
│       │                                                             │
│       └── 4.7kΩ Resistor #4 (Near AMG8833 #1)                       │
│            │                                                        │
│            ▼                                                        │
│       3.3V RAIL                                                  │
│                                                                     │
│  Note: You can use 2 resistors total (one per line) shared       │
│  between both sensors, or 4 resistors (one per sensor per line)  │
│  for better noise immunity.                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Best Practice:**
- For short buses (< 30cm): **2 resistors** (one per line) is sufficient
- For longer buses: **4 resistors** (better noise immunity)
- **Never** use pull-ups > 10kΩ for 400kHz I2C

---

### Connection 7: ESP32-S3 to USR-TCP232 (UART)

**Purpose:** Enable Serial-to-Ethernet communication

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 7: ESP32-S3 TO USR-TCP232 (UART)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ESP32-S3 DevKitC-1                                                 │
│       │                                                             │
│       ├── GPIO 43 (TX)                                              │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ┌────────┐                                                 │
│       │  │ Purple │  ← UART TX (ESP32 out)                           │
│       │  │ Wire   │    Connects to: USR-TCP232 RXD                   │
│       │  └────────┘                                                 │
│       │                                                             │
│       └── GPIO 44 (RX)                                              │
│            │                                                        │
│            ▼                                                        │
│       ┌────────┐                                                   │
│       │ Gray   │  ← UART RX (ESP32 in)                            │
│       │ Wire   │    Connects to: USR-TCP232 TXD                   │
│       └────────┘                                                   │
│                                                                     │
│  USR-TCP232-410S                                                   │
│       │                                                             │
│       ├── RXD Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  Purple wire from ESP32 GPIO 43                             │
│       │                                                             │
│       ├── TXD Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  Gray wire from ESP32 GPIO 44                              │
│       │                                                             │
│       ├── VCC Pin                                                   │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  BREADBOARD 5V RAIL (Column A)                               │
│       │                                                             │
│       └── GND Pin                                                   │
│            │                                                        │
│            ▼                                                        │
│       BREADBOARD GND RAIL (Column B)                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Important:**
- USR-TCP232 **requires 5V power** (not 3.3V)
- ESP32 GPIO are **3.3V** but are **5V tolerant** on input
- USR-TCP232 TX output is **5V**, but ESP32 can handle it

**Verification:**
- Connect USR-TCP232 to network (VLAN 30)
- Configure IP address (e.g., 192.168.30.10)
- Test with `ping 192.168.30.10`
- Test serial communication at 115200 baud

---

### Connection 8: Status LEDs

**Purpose:** Visual system status indicators

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 8: STATUS LEDS                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LED1: Power Indicator (Red)                                       │
│       │                                                             │
│       ├── Anode (+)                                                │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ┌────────┐                                                 │
│       │  │ 220Ω   │  ← Current limiting resistor                     │
│       │  │ Res    │    One end: LED anode                            │
│       │  └────┬───┘    Other end: 3.3V rail                          │
│       │       │                                                        │
│       │       ▼                                                        │
│       │  3.3V RAIL                                                  │
│       │                                                             │
│       └── Cathode (-)                                               │
│            │                                                        │
│            ▼                                                        │
│       BREADBOARD GND RAIL                                           │
│                                                                     │
│  LED2: I2C Activity Indicator (Green)                              │
│       │                                                             │
│       ├── Anode (+)                                                │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ┌────────┐                                                 │
│       │  │ 220Ω   │  ← Current limiting resistor                     │
│       │  │ Res    │    One end: LED anode                            │
│       │  └────┬───┘    Other end: ESP32 GPIO 2                       │
│       │       │                                                        │
│       │       ▼                                                        │
│       │  ESP32 GPIO 2                                               │
│       │                                                             │
│       └── Cathode (-)                                               │
│            │                                                        │
│            ▼                                                        │
│       BREADBOARD GND RAIL                                           │
│                                                                     │
│  LED3: Ethernet Activity Indicator (Blue)                          │
│       │                                                             │
│       ├── Anode (+)                                                │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ┌────────┐                                                 │
│       │  │ 220Ω   │  ← Current limiting resistor                     │
│       │  │ Res    │    One end: LED anode                            │
│       │  └────┬───┘    Other end: USR-TCP232 Link Status (if available)│
│       │       │                                                        │
│       │       ▼                                                        │
│       │  USR-TCP232 Link Status pin (check datasheet)                 │
│       │                                                             │
│       └── Cathode (-)                                               │
│            │                                                        │
│            ▼                                                        │
│       BREADBOARD GND RAIL                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**LED Color Recommendations:**
- **LED1 (Power)**: Red - Always on when powered
- **LED2 (I2C)**: Green - Blinks on I2C activity
- **LED3 (Ethernet)**: Blue - Blinks on network activity

---

### Connection 9: Reset & Trigger Buttons

**Purpose:** Manual control inputs

```
┌─────────────────────────────────────────────────────────────────┐
│ CONNECTION 9: BUTTONS                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                     │
│  BTN1: Reset Button (Momentary)                                     │
│       │                                                             │
│       ├── One Side                                                 │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ESP32 EN Pin (Enable)                                      │
│       │    Active LOW - press to reset                              │
│       │                                                             │
│       └── Other Side                                                │
│            │                                                        │
│            ▼                                                        │
│       ┌────────┐                                                   │
│       │ 10kΩ   │  ← Pull-up resistor                                │
│       │ Res    │    One end: Button other side                       │
│       │        │    Other end: 3.3V rail                             │
│       └────┬───┘                                                   │
│            │                                                        │
│            ▼                                                        │
│       3.3V RAIL                                                  │
│                                                                     │
│  BTN2: Manual Trigger Button (Momentary)                           │
│       │                                                             │
│       ├── One Side                                                 │
│       │    │                                                        │
│       │    ▼                                                        │
│       │  ESP32 GPIO 3 (or any available GPIO)                      │
│       │                                                             │
│       └── Other Side                                                │
│            │                                                        │
│            ▼                                                        │
│       ┌────────┐                                                   │
│       │ 10kΩ   │  ← Pull-up resistor                                │
│       │ Res    │    One end: Button other side                       │
│       │        │    Other end: 3.3V rail                             │
│       └────┬───┘                                                   │
│            │                                                        │
│            ▼                                                        │
│       3.3V RAIL                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Note:** ESP32-S3 has **internal pull-ups**, but external 10kΩ resistors provide better reliability.

---

## 📊 Verification Checklist

### Power Verification
- [ ] 5V rail measures 4.9-5.1V
- [ ] 3.3V rail measures 3.25-3.35V
- [ ] GND rail is continuous (0Ω between any two GND points)
- [ ] No shorts between power rails and GND
- [ ] Diode is oriented correctly (band toward breadboard)

### I2C Verification
- [ ] Both AMG8833 sensors detected at 0x68 and 0x69
- [ ] I2C scan shows both devices
- [ ] Pull-up resistors are 4.7kΩ
- [ ] SDA and SCL lines are not shorted
- [ ] Each sensor can be read independently

### UART Verification
- [ ] USR-TCP232 powers on (status LEDs)
- [ ] Ethernet link LED is active
- [ ] Can ping USR-TCP232 IP address
- [ ] Serial communication works at 115200 baud

### System Verification
- [ ] ESP32 boots successfully
- [ ] Serial monitor shows initialization messages
- [ ] All status LEDs function correctly
- [ ] Fall detection triggers with hand movement
- [ ] Data streams to Jetson/NUC

---

## 🎯 Troubleshooting Matrix

| Symptom | Possible Cause | Test | Solution |
|---------|---------------|------|----------|
| No power anywhere | Bad power supply | Measure 5V input | Check power source, connections |
| 5V OK but no 3.3V | Regulator failure | Measure 3.3V rail | Check AMS1117, input caps |
| ESP32 not detected | USB driver | Try different USB cable/port | Install CP210x/CH340 driver |
| I2C scan empty | No pull-ups | Check SDA/SCL with oscilloscope | Add 4.7kΩ pull-ups to 3.3V |
| I2C scan empty | Wiring error | Visual inspection | Check all I2C connections |
| I2C scan empty | Address conflict | Check AD0 pins | Verify AD0 pull-up/down |
| Only one sensor found | Address conflict | I2C scan | Check both AD0 configurations |
| Garbled I2C data | Noise | Try lower I2C speed | Add decoupling caps, shorten wires |
| USR-TCP232 not responding | No power | Check 5V at USR-TCP232 | Verify 5V rail connection |
| USR-TCP232 not responding | Wrong baud | Check serial settings | Set to 115200 baud |
| Ethernet not working | Bad cable | Try different cable | Replace Ethernet cable |
| Ethernet not working | Wrong VLAN | Check network config | Verify VLAN 30 configuration |

---

## 📝 Bill of Materials (BOM)

### Required Components (Minimum)

| # | Part | Quantity | Estimated Cost | Notes |
|---|------|----------|---------------|-------|
| 1 | ESP32-S3-DevKitC-1 | 1 | $15-20 | Main microcontroller |
| 2 | AMG8833 Thermal Sensor | 2 | $20-30 each | 8×8 thermal array |
| 3 | USR-TCP232-410S | 1 | $25-35 | Serial-to-Ethernet |
| 4 | Breadboard | 1 | $10-15 | 830+ points recommended |
| 5 | Jumper Wires | 50+ | $5-10 | Male-Male, Male-Female |
| 6 | Resistor 4.7kΩ | 4 | $0.10 each | I2C pull-ups |
| 7 | Resistor 220Ω | 3 | $0.10 each | LED current limiting |
| 8 | Resistor 10kΩ | 2 | $0.10 each | Button pull-ups |
| 9 | LED | 3 | $0.20 each | Status indicators |
| 10 | Push Button | 2 | $0.50 each | Reset + Trigger |
| 11 | Capacitor 10µF | 1 | $0.50 | Electrolytic, bulk decoupling |
| 12 | Capacitor 47µF | 1 | $0.50 | Electrolytic, bulk decoupling |
| 13 | Capacitor 100nF | 3 | $0.20 each | Ceramic, high-frequency decoupling |
| 14 | Diode 1N4007 | 1 | $0.20 | Reverse polarity protection |
| 15 | Voltage Regulator AMS1117-3.3V | 1 | $1-2 | 3.3V regulation |
| **Total** | | | **~$100-150** | Excluding shipping |

### Optional Components (Recommended)

| # | Part | Quantity | Estimated Cost | Purpose |
|---|------|----------|---------------|---------|
| 1 | Level Shifter TXB0104E | 1 | $3-5 | 5V ↔ 3.3V conversion |
| 2 | MOSFET IRLML6401 | 1 | $1-2 | Sensor power control |
| 3 | Transistor 2N2222 | 1 | $0.50 | General switching |
| 4 | Fuse Holder + Fuse | 1 | $2-3 | Overcurrent protection |
| 5 | Heat Sink | 1 | $1-2 | For voltage regulator |
| 6 | Enclosure | 1 | $10-20 | Physical protection |

---

## 📚 Additional Resources

- [ESP32-S3 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)
- [AMG8833 Datasheet](https://cdn-shop.adafruit.com/datasheets/AMG8833.pdf)
- [USR-TCP232 User Manual](https://www.usriot.com/products/usr-tcp232)
- [AMS1117 Datasheet](https://www.advanced-monolithic.com/pdf/ds1117.pdf)
- [I2C Pull-Up Resistor Calculator](https://www.analog.com/en/education/education-library/videos/6266319880001.html)

---

**Document Status:** ✅ Active  
**Owner:** Engineering Team  
**Last Updated:** 2026-08-30  
**Version:** 1.1
