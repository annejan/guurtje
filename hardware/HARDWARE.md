# Driving a real disc

Two ways to get the simulation onto physical WS2812 LEDs: **through WLED**, or
**straight off a microcontroller/Pi via hardware SPI**. Both use the LED *chain
order* = `wled_index` 0..N-1 (for StopNu that is centre → spiral outward).

`disc_driver.py` does all of it from a coords CSV (`../data/coords_stopnu.csv`,
`../data/coords_ring241.csv`, or one exported from the simulator):

| `--out` | Transport | Use for |
|---------|-----------|---------|
| `ddp` | WLED realtime **DDP**, UDP :4048 | live animation (best) |
| `dnrgb` | WLED native realtime **DNRGB**, UDP :21324 | live animation, ≤489 leds/packet |
| `wled-json` | WLED **JSON API** `POST /json/state` | a single static frame |
| `spi` | **hardware SPI** WS2812 (Pi) | no WLED at all |
| `preview` | PNGs to disk | checking, no hardware |

```bash
# live rainbow rings to a WLED over DDP
python3 disc_driver.py --coords ../data/coords_stopnu.csv --effect rings --out ddp --host wled.local
# project an animated GIF, drive WS2812 straight off a Pi's SPI
python3 disc_driver.py --coords ../data/coords_stopnu.csv --image nyan.gif --out spi
```

Effects: `spiral`, `rings`, `conic` (identical maths to the browser sim). Or
`--image file.png|file.gif` to project/animate any picture.

## Route A — WLED

WS2812 on an ESP running [WLED](https://kno.wled.ge/). Wire **one** data line to
the configured pin, set the LED count, done.

**1. Upload the 2D ledmap once** (export it from the simulator — StopNu = 37×37,
0 collisions):

```bash
curl -F "data=@ledmap_stopnu_37x37.json;filename=/ledmap0.json" http://wled.local/edit
```

Then in WLED: *Config → LED Preferences → 2D* → enable, pick the ledmap. Now any
2D effect, or the **WLED-MM** image/GIF effect, plays on the disc shape.

**2. One static frame via curl** (per-LED, hex colours, index order):

```bash
curl -X POST http://wled.local/json/state \
  -d '{"seg":[{"i":["FF0000","00FF00","0000FF", ...405 entries... ]}]}'
```

`disc_driver.py --out wled-json --frames 1` builds exactly this for you.

**3. Live animation** — HTTP is too slow; use realtime UDP. Enable *Sync →
Realtime* in WLED (it auto-listens for DDP/DNRGB), then `--out ddp` (or `dnrgb`).
Frames stream at `--fps`.

## Route B — direct hardware SPI (no WLED)

WS2812 is not real SPI, but a Pi's SPI peripheral can clock it: each WS2812 bit
is sent as a few SPI bits at ~2.4–3.2 MHz. `neopixel_spi` handles the encoding.

```bash
sudo raspi-config        # Interface Options → SPI → enable, reboot
pip install adafruit-circuitpython-neopixel-spi adafruit-blinka
python3 disc_driver.py --coords ../data/coords_stopnu.csv --effect spiral --out spi
```

Wiring (Raspberry Pi):
- **GPIO10 / MOSI** (pin 19) → disc **DIN**. (SPI0; no root needed, unlike PWM.)
- Pi **GND** → disc **GND** (and PSU GND — common ground is mandatory).
- 5 V **PSU** → disc 5 V, **not** from the Pi.
- 3.3 V→5 V data: a level shifter (74AHCT125) is the safe option; short runs often
  work direct. ESP32 alternative: its RMT/SPI peripheral + the same `--out` over wifi.

## Colour depth — these are 24-bit LEDs

WS2812 are **24-bit, 8/8/8, GRB** — 16.7M colours but only **256 steps per
channel**. Two things follow:

- **Gamma.** The LED PWM is linear, your eye is not. Without gamma correction,
  mid-tones look too bright and dim fades band. `disc_driver.py` applies a gamma
  LUT — default **2.2 for `spi`/`preview`**, **1.0 for the WLED backends** (WLED
  does its own brightness + optional gamma; don't double it). Override with
  `--gamma`.
- **Low end.** Below ~10/255 WS2812 have few distinct levels and shift colour.
  `--dither` adds temporal error-diffusion: a target of 5.4/255 is sent as a
  5/6/5/6… sequence that *averages* to 5.4, recovering sub-LSB brightness and
  killing visible steps in slow dim fades. Costs nothing, needs a steady frame
  rate.

```bash
# Pi/SPI: gamma-correct + dither for smooth dim gradients
python3 disc_driver.py --coords ../data/coords_stopnu.csv --effect rings --out spi --dither
# DDP to WLED: let WLED do gamma, so keep it linear here
python3 disc_driver.py --coords ../data/coords_stopnu.csv --effect rings --out ddp --host wled.local --gamma 1
```

The browser sim has its own **gamma** slider (and brightness/glow) so you can
preview roughly how a fade lands before wiring.

## Power (read this)

WS2812 ≈ 60 mA/LED at full white:
- **StopNu 405 leds → ~24 A @ 5 V** worst case · Ring241 241 → ~14 A.
- Real animations draw far less, but size the PSU for headroom and cap brightness
  (`--brightness 0.4`, or WLED's auto-limit).
- Inject 5 V/GND at **both** the start and the far side of the ring for ≥~150 leds,
  or the outer ring browns/reddens.
