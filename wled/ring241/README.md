# WLED bundle — Ring241 / "Ali special" 241-LED disc

Drop-in files to make a stock [WLED](https://kno.wled.ge/) ESP drive the round
241-LED AliExpress disc as a 2D display.

| File | What |
|------|------|
| `ledmap0.json` | 2D LED map, 33×33 grid → the 241 physical LEDs (from [MoonModules MM-Effects, Ring241 2D33](https://github.com/MoonModules/MM-Effects/blob/master/Ledmaps/Ring241/Ring241%202D33.json)) |
| `presets.json` | 10 ready presets tuned for a disc (radial/concentric 2D effects) |

## 1. LED settings (WLED UI → Config → LED Preferences)

- **Length: 241**, type WS281x, color order **GRB** (check yours), set your data GPIO.
- **2D / Matrix:** enable, 1 panel, **33 × 33**, serpentine off.
- Save. Then upload `ledmap0.json` (next step) and reselect it under *2D → ledmap*.

## 2. Upload the files

UI: *Config → Security & Update → Manual OTA / file manager* isn't always exposed,
so the reliable way is the built-in editor at `http://wled.local/edit`:

```bash
# 2D ledmap
curl -F "data=@ledmap0.json;filename=/ledmap0.json" http://wled.local/edit

# presets  (⚠ OVERWRITES existing presets — back up /presets.json first if you have any)
curl -o presets-backup.json http://wled.local/presets.json
curl -F "data=@presets.json;filename=/presets.json" http://wled.local/edit
```

Reboot WLED (Config → Security → Reboot, or power cycle). Presets 1–10 appear.

## 3. Presets

1 Ripple rings · 2 Plasma · 3 Colored Bursts · 4 Polar Lights · 5 Black Hole ·
6 Distortion Waves · 7 Pride Spiral · 8 Colorwaves · 9 Rainbow · 10 White test
(low brightness — check wiring/power before turning everything to full white).

All presets are **2D** (they need the ledmap + 33×33 matrix from step 1). The
radial ones (Ripple, Colored Bursts, Black Hole) look best on the disc.

## 1D alternative (no ledmap)

The disc is wired ring-by-ring, so if you *skip* 2D and run it as a plain
241-pixel strip, ordinary 1D effects (Rainbow, Colorwaves, Running, Lake) sweep
along the rings and look like rotating spirals. Either mode works — 2D gives true
concentric/radial patterns, 1D gives spiral sweeps for free.

## Power

241 LEDs at full white ≈ 14 A @ 5 V. Size the PSU with headroom, cap brightness,
and inject 5 V/GND at both ends of the ring. See [../../hardware/HARDWARE.md](../../hardware/HARDWARE.md).
