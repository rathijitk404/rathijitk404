"""Post-process Platane/snk SVGs: the snake starts "shocked" by the low streak
(shaking, wide eyes, "!!!" then "??") and only then goes off to eat.
usage: python shock.py file.svg [file.svg ...]"""
import re, sys

HOLD_MS = 2600  # how long the snake stays shocked before it moves

def process(path):
    s = open(path, encoding="utf-8").read()
    if "shock-done" in s:
        return
    olds = set(re.findall(r"\b(\d+)ms\b", s))
    assert len(olds) == 1, f"unexpected durations {olds}"
    old = int(olds.pop()); new = old + HOLD_MS
    H = HOLD_MS / new * 100; k = old / new
    s = re.sub(r"\b\d+ms\b", f"{new}ms", s)
    # shift every keyframe selector so the whole eating run starts after the hold
    s = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)%(?=[,{])",
               lambda m: f"{H + float(m.group(1)) * k:.3f}%", s)

    # room above the snake for the speech bubble
    s = s.replace('viewBox="-16 -32 880 192" width="880" height="192"',
                  'viewBox="-16 -52 880 212" width="880" height="212"')

    # keyframes for the shocked intro, in % of the new (longer) cycle
    a, b, c = H * .45, H * .90, H          # "!!!" until a, "??" until b, then go
    n = 14; step = a / n
    shake = "".join(f"{i*step:.3f}%{{transform:translate({(-1.4 if i%2 else 1.4)}px,{(.6 if i%3==0 else -.6)}px)}}" for i in range(n))
    css = (
        f".shk{{animation:shk {new}ms steps(1) infinite}}"
        f"@keyframes shk{{{shake}{a:.3f}%,100%{{transform:translate(0,0)}}}}"
        f".pup{{transform-box:fill-box;transform-origin:center;animation:pup {new}ms steps(1) infinite}}"
        f"@keyframes pup{{0%{{transform:scale(.45)}}{a:.3f}%,100%{{transform:scale(1)}}}}"
        f".mth{{animation:mth {new}ms steps(1) infinite}}"
        f"@keyframes mth{{0%{{opacity:1}}{a:.3f}%,100%{{opacity:0}}}}"
        f".t1{{animation:t1 {new}ms steps(1) infinite}}"
        f"@keyframes t1{{0%{{opacity:1}}{a:.3f}%,100%{{opacity:0}}}}"
        f".t2{{opacity:0;animation:t2 {new}ms steps(1) infinite}}"
        f"@keyframes t2{{0%{{opacity:0}}{a:.3f}%{{opacity:1}}{b:.3f}%,100%{{opacity:0}}}}"
        ".tx{font:700 15px ui-monospace,Menlo,Consolas,monospace;fill:#fff;stroke:#2563eb;stroke-width:.7px;paint-order:stroke;text-anchor:middle}"
    )
    s = s.replace("</style>", css + "</style>", 1)

    # wrap the snake in the shaking group and give the head a face
    m = re.search(r'(<rect class="s s0".*)</svg>$', s, re.S)
    assert m, "snake rects not found"
    face = (
        '<g class="s s0">'
        '<circle cx="5" cy="6.5" r="2.7" fill="#fff"/><circle cx="11" cy="6.5" r="2.7" fill="#fff"/>'
        '<circle class="pup" cx="5.4" cy="6.8" r="1.2" fill="#0b101e"/><circle class="pup" cx="10.6" cy="6.8" r="1.2" fill="#0b101e"/>'
        '<ellipse class="mth" cx="8" cy="12" rx="1.8" ry="2.2" fill="#0b101e"/></g>'
    )
    bubble = ('<text class="tx t1" x="8" y="-23">!!!</text><text class="tx t2" x="8" y="-23">??</text>'
              '<!--shock-done-->')
    s = s[:m.start()] + '<g class="shk">' + m.group(1) + face + '</g>' + bubble + '</svg>'
    open(path, "w", encoding="utf-8").write(s)

for p in sys.argv[1:]:
    process(p)
