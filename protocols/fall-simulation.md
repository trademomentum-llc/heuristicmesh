# Fall Simulation Production Protocol

## Mode A – Body-cam Volume (Current)
- Portable, any location
- Body cameras only
- Goal: diversity of body type, clothing, mannerism
- Log with scripts/bodycam_session_log_template.csv

## Mode B – Multi-modal (Later)
- Requires co-located ESP32 + AMG8833 + Jetson
- Higher value for Framework 2/3 training

## Priority Scenarios
- S01 Forward trip
- S02 Sit-to-stand failure
- S03 Lateral slip
- S06 Slow syncope / collapse (highest value)
- S10 Controlled descent vs true fall (negative class)

## Execution Rules
- Actor remains still 4–6 seconds after landing
- Continuous recording preferred over start/stop
- Note clothing, shoes/socks, carrying object, fatigue
- Use mat for higher-risk trials
