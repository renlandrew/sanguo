"""11-13 讨伐里武将被打倒的倒地动作（用户截图半透明站着的刘备：「没有倒下的姿势吗？」→ 先用站姿图转倒顶着 → 「录倒地动作」）。
首帧同重录时的背影图（美术/重画/codex/back_<键>.png），刘关张各一条 4 秒：背对镜头，挨一下、踉跄、兵器脱手、跪倒、趴在地上不动。
3 条 × 4 秒 × .15 = 1.8 美元（limingze091 项目赠金）。Cloud Shell：PROJECT=$DEVSHELL_PROJECT_ID SHOTS=shots_fall.json SECONDS=4 CAP_USD=1.8 python3 veo_wendao.py
用法：python3 三国志/工具/veo/make_fall_pack.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
src = (HERE / 'make_pack.py').read_text(encoding='utf-8').split('\nBASE = ')[0]
g = {'__file__': str(HERE / 'make_pack.py'), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src.replace("out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)", ""), g); HREF = g['ref']
HB = ("Locked-off static camera behind and slightly above a Chinese Three Kingdoms general on a plain, perfectly uniform mid-gray studio background. "
      "He keeps his back to the camera and his face is never visible. He stays inside the frame the whole time. Keep the bright painted illustration look of the first frame and the same costume. ")
FALL = ("is hit hard by an unseen heavy blow from the front: his body jerks, he staggers one step back toward the camera, {drop}, his knees buckle, he drops to his knees and then collapses forward, "
        "ending lying face down flat on the ground with his head pointing away from the camera, and stays completely still for the last second.")
HT = " The background stays a flat uniform mid-gray the whole time, no ground texture, no shadow, no smoke, no blood."
HN = ("black background, gradient background, dark background, vignette, scenery, floor texture, shadow, face, turning around, facing the camera, extra people, "
      "blood, gore, glow, particles, smoke, fire, dust, light beams, leaving the frame, camera movement, zoom, pan, text, watermark, getting up, standing up again")
WHO = {'guan': ('Guan Yu, with long black hair and a green headscarf, in a long flowing plain green robe with a brown leather belt, holding a long-shafted crescent glaive', 'the glaive slips from his hands and falls beside him'),
       'zhang': ('Zhang Fei, a burly general with curly black hair and a red headband, in red cloth over black armor, holding a long steel spear', 'the spear slips from his hands and falls beside him'),
       'liu': ('Liu Bei, with a topknot and blue ribbons, in a long white robe with blue trim and a blue sash, holding a straight sword in each hand', 'both swords slip from his hands and fall beside him')}
shots = [{'id': f'{k}_fall', 'ref': k, 'prompt': HB + who + ', ' + FALL.format(drop=drop) + HT, 'neg': HN} for k, (who, drop) in WHO.items()]
C = ROOT / '美术' / '重画' / 'codex'
with tarfile.open(out / 'fall_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k in WHO: d = HREF(C / f'back_{k}.png'); add(f'ref_{k}.jpg', d); (out / f'ref_{k}.jpg').write_bytes(d)
    add('shots_fall.json', json.dumps(shots, ensure_ascii=False, indent=1).encode()); add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'fall_pack.tar.gz', (out / 'fall_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
