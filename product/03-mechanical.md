# Mechanical Design – Consumer Node

## Form Factor
- Overall: 85 × 85 × 28 mm (or circular Ø90 × 28 mm)
- Mounting: 
  - Keyhole slots for wall screws
  - Optional magnetic plate for metal surfaces
  - Ceiling mount variant with simple twist-lock plate
- Sensor window: thin IR-transmissive plastic or open aperture with recessed AMG8833
- LED light pipe for status (soft green / amber / red)

## Thermal Considerations
- AMG8833 must have clear field of view (recommended 60–90° downward or into the room)
- Avoid placing the sensor behind thick plastic
- Small vent slots for the ESP32 if enclosed tightly
- Keep LDO and ESP32 heat away from the thermal sensor

## Assembly
1. PCB populated (SMT preferred for volume)
2. AMG8833 either:
   - Directly reflowed, or
   - On a small secondary board connected by short flex / pins (easier FOV adjustment)
3. Press-fit or screw into lower housing
4. Upper housing snaps or screws on
5. Functional test via USB-C before final seal

## Manufacturing Notes
- 2-layer PCB is sufficient
- Keep I2C traces short and away from Wi-Fi antenna
- Provide test points for 3.3 V, SDA, SCL, TX, RX, EN, GPIO0
- Consider a small programming jig that pogo-pins the test points for volume programming
