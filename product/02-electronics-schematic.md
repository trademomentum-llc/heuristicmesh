# Electronics Schematic – Consumer Node

## Block Diagram

```
USB-C 5V ──► 3.3V LDO (AMS1117-3.3 or better) ──► ESP32-WROOM-32
                                      │
                                      ├── AMG8833 (I2C 0x69)
                                      │     SDA ── GPIO21
                                      │     SCL ── GPIO22
                                      │     4.7k pull-ups to 3.3V
                                      │
                                      ├── Status LED (GPIO2, active low)
                                      │
                                      └── Optional: reset button, boot button
```

## Power
- Input: USB-C 5 V (dedicated data+power cable or wall adapter)
- Regulation: 3.3 V LDO, ≥ 500 mA capability
- Decoupling: 10 µF + 100 nF on 3.3 V rail close to ESP32 and AMG8833
- Optional reverse-polarity and TVS protection on 5 V input for robustness

## AMG8833 Interface
- Power: 3.3 V
- I2C: 400 kHz
- Pull-ups: 4.7 kΩ on SDA and SCL to 3.3 V (mandatory)
- Address: 0x69 (default)
- INT pin left unconnected in v1 (can be used later for motion wake)

## ESP32
- Module: ESP32-WROOM-32 (or ESP32-WROOM-32E)
- Flash: 4 MB minimum
- Antenna: onboard PCB antenna is sufficient for home use
- Programming: during manufacturing via test pads or USB-UART bridge (CP2102N preferred)

## Minimal Bill of Materials (electronics only)

| Item                    | Qty | Example Part              | Est. Cost (1k) |
|-------------------------|-----|---------------------------|----------------|
| ESP32-WROOM-32          | 1   | Espressif                 | $1.80–2.40     |
| AMG8833                 | 1   | Panasonic / equivalent    | $8.50–12.00    |
| 3.3V LDO                | 1   | AMS1117-3.3 or AP2112     | $0.15          |
| USB-C receptacle        | 1   | 16-pin mid-mount          | $0.25          |
| 4.7kΩ 0402/0603         | 2   | -                         | $0.02          |
| 10µF + 100nF ceramics   | 4–6 | -                         | $0.10          |
| Status LED + resistor   | 1   | -                         | $0.05          |
| PCB (2-layer, 50×50mm)  | 1   | -                         | $0.60–1.00     |
| Misc (headers, buttons) | -   | -                         | $0.30          |
| **Electronics total**   |     |                           | **~$12–17**    |

## Enclosure & Assembly Cost Target
- Injection-molded ABS or PC/ABS housing: $1.50–2.50
- Screws / adhesive / labeling: $0.40
- Test & packaging: $1.50
- **Fully assembled unit cost target (1k qty): $18–25**
