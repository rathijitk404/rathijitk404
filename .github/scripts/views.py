"""Anime-girls view counter as a breathing animated GIF (the GitHub app can't show the live SVG one).
count = komarev's page-view count (every profile load, app + web) minus the +1 this script adds per run.
usage: python views.py <outdir> <github_user>"""
import base64, io, math, os, re, subprocess, sys
from PIL import Image

out, user = sys.argv[1], sys.argv[2]
RAW = f"https://raw.githubusercontent.com/{user}/{user}/output"
START = 1347  # number the counter starts from; real visits are added on top (change it or set 0 for the true count)

def fetch(url, binary=False):
    # curl works where urllib gets a 403 from the counter site
    r = subprocess.run(["curl", "-sSL", "--fail", "--max-time", "30", "-A",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "-H", "Accept: image/svg+xml,image/*,*/*", url], capture_output=True)
    if r.returncode:
        print("FETCH FAILED", url, r.stderr.decode()[:200]); raise RuntimeError(url)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")

def keep_previous():
    for name in ("counter.gif", "runs.txt"):
        try: data = fetch(f"{RAW}/{name}", True)
        except Exception as e: print("no previous", name, e); continue
        open(f"{out}/{name}", "wb").write(data)

try:
    os.makedirs(out, exist_ok=True)
    # 1) digit sprites: the service's demo counter draws 0123456789
    demo = fetch("https://count.getloli.com/@demo?theme=moebooru&length=10&pixelated=1")
    imgs = re.findall(r'<image[^>]*?href="data:image/[a-z]+;base64,([^"]+)"', demo)
    print("sprites found:", len(imgs))
    assert len(imgs) >= 10, "demo counter did not return 10 digit images"
    sprites = [Image.open(io.BytesIO(base64.b64decode(b))).convert("RGBA") for b in imgs[:10]]
    # 2) count (this fetch adds 1 view; remember it so it can be subtracted)
    svg = fetch(f"https://komarev.com/ghpvc/?username={user}&label=V&color=blue")
    nums = re.findall(r">\s*([\d,]+)\s*<", svg)
    assert nums, "no number in komarev badge"
    total = int(nums[-1].replace(",", ""))
    try: runs = int(fetch(f"{RAW}/runs.txt").strip())
    except Exception: runs = 0
    runs += 1
    views = START + max(total - runs, 0)
    print("komarev", total, "runs", runs, "->", views)
    # 3) breathing animation: every girl slowly grows/shrinks from her feet, each a little out of step
    digits = str(views).zfill(4)
    ims = [sprites[int(d)] for d in digits]
    W = sum(i.width for i in ims); H = max(i.height for i in ims); PADY = 6
    N = 20; frames = []
    for f in range(N):
        sheet = Image.new("RGBA", (W, H + PADY), (0, 0, 0, 0)); x = 0
        for k, im in enumerate(ims):
            breath = (1 - math.cos(2 * math.pi * f / N - k * 0.6)) / 2   # 0..1
            h = round(im.height * (1 + 0.05 * breath))
            sheet.paste(im.resize((im.width, h), Image.NEAREST), (x, H + PADY - h), im.resize((im.width, h), Image.NEAREST))
            x += im.width
        frames.append(sheet)
    frames[0].save(f"{out}/counter.gif", save_all=True, append_images=frames[1:], duration=90, loop=0, disposal=2, transparency=0)
    print("gif", W, H + PADY, "digits", digits)
    open(f"{out}/runs.txt", "w").write(str(runs))
except Exception as e:
    print("views.py failed, keeping previous files:", e)
    keep_previous()
