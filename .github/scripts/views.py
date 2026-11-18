"""Anime-girls view counter as a breathing, blinking animated GIF (the GitHub app can't show the live SVG one).
count = START + komarev's page-view count (every profile load, app + web) minus the +1 this script adds per run.
usage: python views.py <outdir> <github_user>"""
import base64, io, math, os, re, subprocess, sys
from PIL import Image

START = 1347  # starting number; real visits are added on top (set 0 for the true count)
N = 24        # frames per loop (90 ms each)
# per digit sprite: (which pixels are "eye", [eye boxes x0,y0,x1,y1]) and the row under which the head ends (sway)
EYES = {0: ("blue", [(15, 19, 22, 23), (25, 19, 32, 23)]), 1: ("red", [(18, 16, 25, 24), (26, 16, 32, 24)]),
        2: ("dark", [(13, 18, 20, 23), (21, 18, 28, 23)]), 3: ("blue", [(13, 21, 20, 26), (24, 21, 31, 26)]),
        4: ("blue", [(13, 19, 18, 26), (22, 19, 28, 26)]), 5: ("blue", [(18, 19, 24, 26), (26, 19, 32, 26)]),
        6: ("blue", [(11, 17, 18, 24), (22, 18, 29, 24)]), 7: ("dark", [(15, 42, 20, 46), (23, 42, 28, 46)]),
        8: ("blue", [(21, 34, 32, 42)]), 9: ("blue", [(13, 42, 19, 49), (22, 42, 30, 49)])}
HEAD = {0: 30, 1: 28, 2: 28, 3: 34, 4: 34, 5: 34, 6: 30, 7: 52, 8: 44, 9: 54}  # rows above this sway with the head

def is_eye(c, kind):
    r, g, b, a = c
    if not a or (r, g, b) == (0, 0, 0): return False  # keep the black outline
    if kind == "red": return r > 150 and g < 110 and b < 110
    if kind == "dark": return (r + g + b) / 3 < 130
    return b > r + 25 and b > 90 or (r + g + b) / 3 < 75  # blue iris or dark pupil

def blink(im, d):
    """close the eyes: paint the iris pixels with the cheek colour and draw a thin lash line"""
    kind, boxes = EYES[d]; px = im.load()
    for x0, y0, x1, y1 in boxes:
        cheek = [px[x, y] for y in range(y1, min(y1 + 3, im.height)) for x in range(x0, x1) if px[x, y][3] and px[x, y][:3] != (0, 0, 0)]
        if not cheek: continue
        skin = max(set(cheek), key=cheek.count)
        eye = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if is_eye(px[x, y], kind)]
        if not eye: continue
        for x, y in eye: px[x, y] = skin
        low = max(y for _, y in eye)
        for x in range(min(x for x, _ in eye), max(x for x, _ in eye) + 1): px[x, low] = (60, 50, 75, 255)
    return im

def sway(im, d, t):
    """head/ear sway (rows above the head line shift up to ~1px) + tail swing for the girls that have one"""
    src = im.copy(); out = Image.new("RGBA", im.size, (0, 0, 0, 0)); hb = HEAD[d]
    for y in range(im.height):
        dx = round(1.4 * math.sin(t) * (hb - y) / hb) if y < hb else 0
        if d == 2 and 45 <= y < 64: dx = round(1.6 * math.sin(t - 1) * (y - 45) / 19)  # tail hangs on the right
        out.paste(src.crop((0, y, im.width, y + 1)), (dx, y))
    if d == 1:  # tail on the lower left: tip swings up/down, root stays put
        for x in range(2, 16):
            dy = round(2 * math.sin(t - 1) * (16 - x) / 14)
            col = src.crop((x, 58, x + 1, 76)); out.paste((0, 0, 0, 0), (x, 58, x + 1, 76)); out.paste(col, (x, 58 + dy))
    return out

def animate(sprites, digits, path):
    W = sum(s.width for s in sprites[:1]) * len(digits); H = max(s.height for s in sprites) + 6
    frames = []
    for f in range(N):
        sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x = 0
        for k, ch in enumerate(digits):
            d = int(ch); im = sprites[d].copy()
            if (f - 5 * k) % N in (0, 1): im = blink(im, d)     # each girl blinks 2 frames per loop, out of step
            im = sway(im, d, 2 * math.pi * f / N + k * 0.7)
            breath = (1 - math.cos(2 * math.pi * f / N - k * 0.6)) / 2
            h = round(im.height * (1 + 0.05 * breath)); im = im.resize((im.width, h), Image.NEAREST)
            sheet.paste(im, (x, H - h), im); x += im.width
        frames.append(sheet)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=90, loop=0, disposal=2, transparency=0)

def fetch(url, binary=False):
    # curl works where urllib gets a 403 from the counter site
    r = subprocess.run(["curl", "-sSL", "--fail", "--max-time", "30", "-A",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "-H", "Accept: image/svg+xml,image/*,*/*", url], capture_output=True)
    if r.returncode:
        print("FETCH FAILED", url, r.stderr.decode()[:200]); raise RuntimeError(url)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")

if __name__ == "__main__":
    out, user = sys.argv[1], sys.argv[2]
    RAW = f"https://raw.githubusercontent.com/{user}/{user}/output"
    try:
        os.makedirs(out, exist_ok=True)
        demo = fetch("https://count.getloli.com/@demo?theme=moebooru&length=10&pixelated=1")  # draws 0123456789
        imgs = re.findall(r'<image[^>]*?href="data:image/[a-z]+;base64,([^"]+)"', demo)
        assert len(imgs) >= 10, "demo counter did not return 10 digit images"
        sprites = [Image.open(io.BytesIO(base64.b64decode(b))).convert("RGBA") for b in imgs[:10]]
        svg = fetch(f"https://komarev.com/ghpvc/?username={user}&label=V&color=blue")  # this fetch adds 1 view
        total = int(re.findall(r">\s*([\d,]+)\s*<", svg)[-1].replace(",", ""))
        try: runs = int(fetch(f"{RAW}/runs.txt").strip())
        except Exception: runs = 0
        runs += 1
        views = START + max(total - runs, 0)
        digits = str(views).zfill(7)
        print("komarev", total, "runs", runs, "->", digits)
        animate(sprites, digits, f"{out}/counter.gif")
        open(f"{out}/runs.txt", "w").write(str(runs))
    except Exception as e:
        print("views.py failed, keeping previous files:", e)
        for name in ("counter.gif", "runs.txt"):
            try: data = fetch(f"{RAW}/{name}", True)
            except Exception: continue
            open(f"{out}/{name}", "wb").write(data)
