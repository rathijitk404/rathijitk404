"""Build banner.svg = the animated bus stop scene with live GitHub numbers attached under it.
usage: python banner.py bus-stop.svg user.json out.svg   (user.json = `gh api users/<name>`)"""
import datetime, json, re, sys

src, user_json, out = sys.argv[1:4]
u = json.load(open(user_json))
repos = int(u["public_repos"])
created = datetime.datetime.fromisoformat(u["created_at"].replace("Z", "+00:00"))
days = (datetime.datetime.now(datetime.timezone.utc) - created).days

scene = open(src, encoding="utf-8").read()
# turn the scene into a nested <svg> placed at the top of a taller canvas
scene = re.sub(r'width="960"', 'x="0" y="0" width="320" height="180"', scene, count=1)
assert 'height="180"' in scene

stats = f'''<rect y="180" width="320" height="64" fill="#0b0e17"/>
<line x1="160" y1="192" x2="160" y2="232" stroke="#1e293b" stroke-width=".6"/>
<g font-family="Inter,'Segoe UI',system-ui,-apple-system,sans-serif" text-anchor="middle">
<text x="80" y="217" font-size="30" font-weight="800" fill="#3b82f6">{repos}</text>
<text x="80" y="233" font-size="8.5" fill="#94a3b8">Public repositories</text>
<text x="240" y="217" font-size="30" font-weight="800" fill="#3b82f6">{days:,}</text>
<text x="240" y="233" font-size="8.5" fill="#94a3b8">Days on GitHub</text>
</g>'''
open(out, "w", encoding="utf-8").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 244" width="960">{scene}{stats}</svg>')
