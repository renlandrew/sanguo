"""从 Effekseer 样例做一个首领法术的变体（10-27）：关掉不要的节点（比如铺满一整块的 Bloom 灰雾、密集的星星粒子），再用 1.70e 命令行转成网页运行库读的 .efk。
贴图另用 install_tex.py 换成 GPT 画的。
用法：python3 variant.py <样例名，如 MAGICALxSPIRAL/Thunder3> <输出 .efk> [要关掉的节点名 ...]
"""
import re, subprocess, sys, tempfile
from pathlib import Path

PACKS = Path("/Volumes/andrew's SSD/Mistport-worktrees/hero-v4-device/output/shield-effekseer-ref-20261006/packs")
EF = "/Volumes/andrew's SSD/tools-downloads/effekseer170e/Effekseer.app/Contents/Resources/Effekseer"
pack, name = sys.argv[1].split('/'); out = Path(sys.argv[2]).resolve(); hide = set(sys.argv[3:])
src = next((PACKS / pack).rglob(name + '.efkproj'))
xml = src.read_text(encoding='utf-8')
for n in hide:
    xml, k = re.subn(r'<IsRendered>True</IsRendered>(\s*<Name>' + re.escape(n) + r'</Name>)', r'<IsRendered>False</IsRendered>\1', xml)
    print(n, '关掉' if k else '没找到')
tmp = src.parent / ('_v_' + name + '.efkproj')                                # 放在样例旁边，贴图的相对路径不变
tmp.write_text(xml, encoding='utf-8')
try: subprocess.run([EF, '-cui', '-in', str(tmp), '-e', str(out)], check=False, capture_output=True)
finally: tmp.unlink()
print(out, out.exists())
