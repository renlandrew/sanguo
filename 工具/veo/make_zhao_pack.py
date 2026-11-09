"""赵云首录（11-08，用户：「赵云动作报价」→「完整版上限 6 美元」）。
首帧：美术/赵云/back_zhao.png（Codex 画的背影，中灰底 2:3）、ult_zhao.png（正面全身，学招特写用）。补 9:16 的办法照 make_redo_pack / make_ult_pack2。
城头动作 4 条 × 4 秒（待机、普攻突刺、普攻旋枪、招式「七进七出」，背对镜头），学招特写 1 条 × 8 秒（正面）：4 × .6 + 1.2 = 3.6 美元，重录留到 6 美元。
输出 <输出目录>/zhao_pack.tar.gz，Cloud Shell 里（同一目录，spent.json 累计，两次都设 CAP_USD=6）：
  SHOTS=shots_zhao.json SECONDS=4 CAP_USD=6 python3 veo_wendao.py
  SHOTS=shots_zhao_ult.json SECONDS=8 CAP_USD=6 python3 veo_wendao.py
用法：python3 三国志/工具/veo/make_zhao_pack.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
def load(name, cut):
    src = (HERE / name).read_text(encoding='utf-8').split(cut)[0]
    g = {'__file__': str(HERE / name), 'out': out, 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src.replace("out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)", ""), g); return g
R = load('make_redo_pack.py', '\nC = ROOT')                      # HREF、HB、HT、HN（背影）
U = load('make_ult_pack2.py', '\nshots = ')                       # ref、BASE、TAIL、NEG（正面特写）
WHO = ("Zhao Yun, a young beardless general in a silver helmet with a white plume, smooth silver plate armor with a sky-blue sash, a white battle skirt and a long sky-blue cape, "
       "holding a very long straight silver spear with a slim smooth spearhead and a small white tassel (a rigid steel spear, never a halberd or a wavy blade)")
ACTS = [
    ('idle', "stands in a light, alert spearman's stance with knees bent, shifting his weight from foot to foot, the long silver spear held diagonally with its tip circling slowly; his sky-blue cape and white plume ripple in the wind."),
    ('atk', "steps forward into a deep lunge and drives the long spear straight out away from the camera in a lightning-fast thrust, snaps it back and thrusts twice more in quick succession, then springs back to his stance."),
    ('atk2', "whirls the long spear in a full circle around his body without turning to face the camera, sweeps it in a wide horizontal arc in front of him, then stabs forward once with a big step, cape flaring."),
    ('skill', "crouches low, then explodes forward with a big running step and a long charging lunge, thrusting the spear far forward; he pivots on the spot keeping his back to the camera and stabs hard to the left, then to the right, then forward again, and finally plants his feet and raises the spear high, cape billowing."),
]
shots = [{'id': f'zhao{i}_{a}', 'ref': 'zhao', 'prompt': R['HB'] + WHO + ', ' + m + R['HT'], 'neg': R['HN']} for i, (a, m) in enumerate(ACTS)]
ULT = ("Zhao Yun, the young general in silver armor and sky-blue cape, spins the long silver spear once around his body, steps forward and thrusts it straight at the camera "
       "in one lightning-fast strike, then two more quick thrusts, his cape and white plume whipping back. Then he draws the spear back, plants its butt on the floor upright beside him "
       "with his right hand, lifts his chin and looks calmly ahead with a faint confident smile. Hold that pose.")
ult = [{'id': 'zhao_ult2', 'ref': 'u_zhao', 'prompt': U['BASE'] + ULT + U['TAIL'], 'neg': U['NEG']}]
with tarfile.open(out / 'zhao_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    d = R['HREF'](ROOT / '美术' / '赵云' / 'back_zhao.png'); add('ref_zhao.jpg', d); (out / 'ref_zhao.jpg').write_bytes(d)
    d = U['ref'](ROOT / '美术' / '赵云' / 'ult_zhao.png'); add('ref_u_zhao.jpg', d); (out / 'ref_u_zhao.jpg').write_bytes(d)
    add('shots_zhao.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('shots_zhao_ult.json', json.dumps(ult, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', (out / 'zhao_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条 4 秒 +', len(ult), '条 8 秒，约', round(len(shots) * 4 * .15 + len(ult) * 8 * .15, 1), '美元')
