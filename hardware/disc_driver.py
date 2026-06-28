#!/usr/bin/env python3
"""
disc_driver.py — drive a round WS2812 LED disc (StopNu / Ring241 / any coords) on
real hardware, using the SAME geometry the browser simulator uses.

It reads a coords CSV (wled_index,nx,ny,r — export it from ring241-sim.html, or use
the ones in ../data/), renders per-LED colours in chain order (index 0..N-1) for a
geometry effect or a projected image/GIF, and pushes frames over one of:

  --out ddp        WLED realtime DDP        (UDP :4048)   <- best for live animation
  --out dnrgb      WLED native realtime     (UDP :21324)  <- DNRGB, <=489 leds/packet
  --out wled-json  WLED JSON API per frame  (HTTP /json/state)  <- slow, fine for stills
  --out spi        direct WS2812 via hardware SPI (Raspberry Pi, neopixel_spi)
  --out preview    render frames to PNGs    (no hardware, for checking)

Examples
  # live rainbow rings to a WLED at wled.local over DDP
  python3 disc_driver.py --coords ../data/coords_stopnu.csv --effect rings --out ddp --host wled.local

  # project an animated GIF onto the disc, drive WS2812 straight off a Pi's SPI
  python3 disc_driver.py --coords ../data/coords_stopnu.csv --image nyan.gif --out spi

  # one static frame via curl-style JSON API
  python3 disc_driver.py --coords ../data/coords_stopnu.csv --effect conic --out wled-json --host wled.local --frames 1
"""
import argparse, csv, math, socket, struct, sys, time, urllib.request

import numpy as np

# ---------------------------------------------------------------- model ----
def load_coords(path):
    idx, nx, ny, r = [], [], [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            idx.append(int(float(row["wled_index"]))); nx.append(float(row["nx"]))
            ny.append(float(row["ny"]));               r.append(float(row["r"]))
    n = max(idx) + 1
    NX = np.zeros(n); NY = np.zeros(n); R = np.zeros(n)
    for i, x, y, rr in zip(idx, nx, ny, r):
        NX[i] = x; NY[i] = y; R[i] = rr
    A = np.arctan2(NY, NX) % (2 * math.pi)               # 0..2pi, matches the sim
    # spiral rank: bucket by ring (round r / mean-nearest-neighbour), then by angle
    pts = np.stack([NX, NY], 1)
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(2))
    np.fill_diagonal(d, np.inf)
    step = d.min(1).mean() or 0.1                          # mean LED spacing (normalised)
    ring = np.round(R / step).astype(int)
    order = sorted(range(n), key=lambda i: (ring[i], A[i]))
    rank = np.zeros(n)
    for k, i in enumerate(order):
        rank[i] = k / max(1, n - 1)
    return dict(n=n, nx=NX, ny=NY, r=R, a=A, rank=rank, pitch=step)

# --------------------------------------------------------------- colour ----
def hsl2rgb(h, s, l):                                   # arrays in deg,%,% -> Nx3 0..255
    h = (h % 360) / 360.0; s = s / 100.0; l = l / 100.0
    def f(nn):
        k = (nn + h * 12) % 12
        a = s * np.minimum(l, 1 - l)
        return l - a * np.clip(np.minimum.reduce([k - 3, 9 - k, np.ones_like(k)]), -1, 1)
    return (np.stack([f(0), f(8), f(4)], 1) * 255).clip(0, 255).astype(np.uint8)

# --------------------------------------------------------------- effects ---
def fx_spiral(m, t):
    p = (m["rank"] - t * 0.3) % 1.0
    b = (1 - p) ** 3
    return hsl2rgb(m["rank"] * 320 + t * 50, np.full(m["n"], 95.0), 8 + b * 54)

def fx_rings(m, t):
    w = np.sin(m["r"] * math.pi * 6 - t * 3) * 0.5 + 0.5
    return hsl2rgb(m["r"] * 300 + t * 30, np.full(m["n"], 90.0), 8 + w * w * 54)

def fx_conic(m, t):
    return hsl2rgb(m["a"] / (2 * math.pi) * 360 + t * 60,
                   np.full(m["n"], 95.0), np.full(m["n"], 52.0))

EFFECTS = {"spiral": fx_spiral, "rings": fx_rings, "conic": fx_conic}

# ----------------------------------------------------------- image source --
class ImageSource:
    """Project an image / animated GIF onto the disc (planar cover, +y up).

    filt: 'nearest' (1 source pixel per LED — aliases on a sparse disc),
          'bilinear' (sub-pixel 4-tap), or 'area' (gaussian pre-blur sized to the
          LED footprint, then bilinear — proper anti-aliased downsample)."""
    def __init__(self, path, filt="area"):
        from PIL import Image
        self.im = Image.open(path); self.frames = getattr(self.im, "n_frames", 1)
        self.filt = filt

    def colours(self, m, fno):
        from PIL import Image, ImageFilter
        self.im.seek(fno % self.frames)
        fr = self.im.convert("RGB"); W, H = fr.size
        if self.filt == "area":                          # blur to the per-LED footprint first
            foot = max(0.5, m["pitch"] * W * 0.5)
            fr = fr.filter(ImageFilter.GaussianBlur(foot))
        px = np.asarray(fr).astype(np.float32)
        asp = W / H
        u = (m["nx"] * 0.5 + 0.5)
        v = (m["ny"] / asp * 0.5 + 0.5)                  # ny already screen-down, matches sim
        X = np.clip(u * (W - 1), 0, W - 1); Y = np.clip(v * (H - 1), 0, H - 1)
        if self.filt == "nearest":
            return px[np.round(Y).astype(int), np.round(X).astype(int)].astype(np.uint8)
        x0 = np.floor(X).astype(int); y0 = np.floor(Y).astype(int)       # bilinear
        x1 = np.clip(x0 + 1, 0, W - 1); y1 = np.clip(y0 + 1, 0, H - 1)
        fx = (X - x0)[:, None]; fy = (Y - y0)[:, None]
        a = px[y0, x0]; b = px[y0, x1]; c = px[y1, x0]; d = px[y1, x1]
        out = (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
        return out.clip(0, 255).astype(np.uint8)

# -------------------------------------------------------------- backends ---
def send_ddp(sock, host, rgb):
    data = rgb.tobytes()
    off = 0; mtu = 1440
    while off < len(data):
        chunk = data[off:off + mtu]; last = off + len(chunk) >= len(data)
        flags = 0x40 | (0x01 if last else 0)            # v1 + push on final
        hdr = struct.pack(">BBBBIH", flags, 0, 0, 1, off, len(chunk))
        sock.sendto(hdr + chunk, (host, 4048)); off += len(chunk)

def send_dnrgb(sock, host, rgb):                        # WLED native realtime, port 21324
    n = len(rgb); start = 0
    while start < n:
        block = rgb[start:start + 489]
        pkt = bytes([4, 2]) + struct.pack(">H", start) + block.tobytes()
        sock.sendto(pkt, (host, 21324)); start += len(block)

def send_wled_json(host, rgb):
    i = []
    for c in rgb:
        i.append("%02X%02X%02X" % (int(c[0]), int(c[1]), int(c[2])))
    body = ('{"seg":[{"i":[' + ",".join('"%s"' % c for c in i) + "]}]}").encode()
    req = urllib.request.Request("http://%s/json/state" % host, data=body,
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=3).read()

def save_preview(m, rgb, path):
    from PIL import Image, ImageDraw
    S = 720; im = Image.new("RGB", (S, S), (0, 0, 0)); dr = ImageDraw.Draw(im)
    Rpx = S / 2 - 24; cx = cy = S / 2; dot = max(2, Rpx * 0.045)
    for i in range(m["n"]):
        x = cx + m["nx"][i] * Rpx; y = cy + m["ny"][i] * Rpx
        c = tuple(int(v) for v in rgb[i])
        dr.ellipse([x - dot, y - dot, x + dot, y + dot], fill=c)
    im.save(path)

# ----------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser(description="Drive a round WS2812 disc from disc coords.")
    ap.add_argument("--coords", required=True)
    ap.add_argument("--effect", choices=list(EFFECTS))
    ap.add_argument("--image", help="image or animated GIF to project")
    ap.add_argument("--filter", choices=["nearest", "bilinear", "area"], default="area",
                    help="image sampling: area = anti-aliased downsample (default)")
    ap.add_argument("--out", required=True,
                    choices=["ddp", "dnrgb", "wled-json", "spi", "preview"])
    ap.add_argument("--host", default="wled.local")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--frames", type=int, default=0, help="0 = loop forever")
    ap.add_argument("--brightness", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=None,
                    help="gamma for 8-bit WS2812 output; default 2.2 for spi/preview, "
                         "1.0 for WLED backends (WLED applies its own). Use 1 to disable.")
    ap.add_argument("--dither", action="store_true",
                    help="temporal error-diffusion dither — smooths low-brightness banding")
    ap.add_argument("--preview-dir", default="preview_frames")
    a = ap.parse_args()
    if not a.effect and not a.image:
        ap.error("give --effect or --image")
    if a.gamma is None:
        a.gamma = 2.2 if a.out in ("spi", "preview") else 1.0
    if a.gamma != 1.0 and a.out in ("ddp", "dnrgb", "wled-json"):
        print("note: applying gamma %.2f AND WLED may gamma too (double). "
              "Pass --gamma 1, or disable gamma in WLED." % a.gamma, file=sys.stderr)
    glut = (np.linspace(0, 1, 256) ** a.gamma) * 255.0      # 8-bit gamma LUT
    residual = None                                          # temporal dither carry

    m = load_coords(a.coords)
    src = ImageSource(a.image, a.filter) if a.image else None
    print("disc: %d leds from %s" % (m["n"], a.coords), file=sys.stderr)

    sock = None
    if a.out in ("ddp", "dnrgb"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pixels = None
    if a.out == "spi":
        import board, neopixel_spi                       # pip install adafruit-circuitpython-neopixel-spi
        pixels = neopixel_spi.NeoPixel_SPI(board.SPI(), m["n"], pixel_order=neopixel_spi.GRB,
                                           auto_write=False)

    t0 = time.time(); fno = 0
    try:
        while a.frames == 0 or fno < a.frames:
            t = time.time() - t0
            rgb = src.colours(m, fno) if src else EFFECTS[a.effect](m, t)
            lin = glut[rgb] * a.brightness                  # gamma-correct, then brightness
            if a.dither:
                if residual is None:
                    residual = np.zeros_like(lin)
                lin = lin + residual
                rgb = np.floor(lin).clip(0, 255)
                residual = lin - rgb
                rgb = rgb.astype(np.uint8)
            else:
                rgb = np.round(lin).clip(0, 255).astype(np.uint8)
            if a.out == "ddp":        send_ddp(sock, a.host, rgb)
            elif a.out == "dnrgb":    send_dnrgb(sock, a.host, rgb)
            elif a.out == "wled-json":send_wled_json(a.host, rgb)
            elif a.out == "spi":
                for i in range(m["n"]):
                    pixels[i] = (int(rgb[i][0]), int(rgb[i][1]), int(rgb[i][2]))
                pixels.show()
            elif a.out == "preview":
                import os; os.makedirs(a.preview_dir, exist_ok=True)
                save_preview(m, rgb, "%s/f%04d.png" % (a.preview_dir, fno))
            fno += 1
            dt = (1.0 / a.fps) - ((time.time() - t0) - t)
            if dt > 0: time.sleep(dt)
    except KeyboardInterrupt:
        pass
    print("sent %d frames" % fno, file=sys.stderr)

if __name__ == "__main__":
    main()
