"""Anime-girls view counter as a plain PNG (the GitHub app can't show the live SVG one).
count = komarev's page-view count (every profile load, app + web) minus the +1 this script adds per run.
usage: python views.py <outdir> <github_user>"""
import base64, io, os, re, sys, urllib.request
from PIL import Image

out, user = sys.argv[1], sys.argv[2]
RAW = f"https://raw.githubusercontent.com/{user}/{user}/output"
UA = {"User-Agent": "Mozilla/5.0"}

def fetch(url, binary=False):
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    return data if binary else data.decode("utf-8", "replace")

def keep_previous():
    for name in ("counter.png", "runs.txt"):
        try: open(f"{out}/{name}", "wb").write(fetch(f"{RAW}/{name}", True))
        except Exception as e: print("no previous", name, e)

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
    views = max(total - runs, 0)
    print("komarev", total, "runs", runs, "->", views)
    # 3) paste digits, 7 wide
    digits = str(views).zfill(7)
    ims = [sprites[int(d)] for d in digits]
    W = sum(i.width for i in ims); H = max(i.height for i in ims)
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x = 0
    for i in ims:
        sheet.paste(i, (x, H - i.height), i); x += i.width
    sheet.save(f"{out}/counter.png")
    open(f"{out}/runs.txt", "w").write(str(runs))
except Exception as e:
    print("views.py failed, keeping previous files:", e)
    keep_previous()
