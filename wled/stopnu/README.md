# WLED bundle — Bornhack StopNu 405-LED disc

Drop-in files for a stock [WLED](https://kno.wled.ge/) ESP driving the 405-LED
StopNu disc as a 2D display.

| File | What |
|------|------|
| `ledmap0.json` | 2D LED map, **37×37** grid → the 405 physical LEDs (rasterised from the real PCB coords, 0 collisions) |
| `presets.json` | 10 disc-tuned presets (same set as the Ring241 bundle) |

## Load

```bash
# 1. LED prefs: Length 405, WS281x, GRB, your data pin; 2D matrix 37x37, serpentine off
# 2. upload the files to the ESP filesystem:
curl -F "data=@ledmap0.json;filename=/ledmap0.json" http://wled.local/edit
curl -o presets-backup.json http://wled.local/presets.json          # ⚠ back up first
curl -F "data=@presets.json;filename=/presets.json"  http://wled.local/edit
# 3. reboot. In 2D settings, select the ledmap.
```

Presets 1–10: Ripple rings · Plasma · Colored Bursts · Polar Lights · Black Hole ·
Distortion Waves · Pride Spiral · Colorwaves · Rainbow · White test.

The StopNu is wired centre→out as a spiral, so even in plain 1D mode (no ledmap)
ordinary 1D effects sweep the rings as spirals. 2D mode gives true radial patterns.

Power: 405 LEDs full white ≈ **24 A @ 5 V** — size the PSU, cap brightness, inject
5 V/GND at both ends. See [../../hardware/HARDWARE.md](../../hardware/HARDWARE.md).
