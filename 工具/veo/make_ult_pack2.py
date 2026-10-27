"""刘关张学招特写重录（10-27，用户：「学习到技能的录像要完整一点，比如关羽做完动作要捋须」「用 Veo 录刘关张学招特写，上限 5 美元」）。
首帧：美术/重画/codex/ult_<键>.png（Codex 画的新画风正面全身，中灰底 2:3），补 9:16 同 make_ult_pack.py（缩到 1080 宽贴底，上面接灰）。
每条 8 秒：起势 → 出招 → 收招 → 收尾的人物动作（关羽捋须、张飞拄矛大笑、刘备收剑点头），镜头不动、灰底不变、不要光效。
3 条 × 8 秒 × .15 美元 ≈ 3.6 美元。输出 <输出目录>/ult2_pack.tar.gz，Cloud Shell 里：SHOTS=shots_ult2.json SECONDS=8 CAP_USD=5 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_ult_pack2.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
src = (HERE / 'make_ult_pack.py').read_text(encoding='utf-8').split('\nBASE = ')[0]
g = {'__file__': str(HERE / 'make_ult_pack.py'), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src.replace("out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)", ""), g); ref = g['ref']

BASE = ("Locked-off static camera, plain perfectly uniform mid-gray studio background. Full-body shot of a Chinese Three Kingdoms general facing the camera, "
        "keep the bright painted illustration look of the first frame, the same costume, face and weapon; the weapon stays rigid steel. "
        "He performs one complete martial move with a clear beginning, middle and end, then a calm finishing gesture held to the last frame: ")
TAIL = (" Strong, dramatic, weighty motion; every limb moves naturally; two arms, two hands. He stays inside the frame and ends near his starting spot. "
        "The background stays a flat uniform mid-gray the whole time.")
NEG = ("black background, gradient background, dark background, vignette, spotlight, scenery, sky, ground, floor, shadow, "
       "glow, light rays, lightning, sparks, fire, flames, smoke, mist, dust, particles, magic effects, energy, aura, "
       "turning around, back view, extra people, extra weapons, extra arms, extra hands, bending weapon, morphing weapon, snake, "
       "camera movement, zoom, cut, jump cut, scene cut, sudden change of pose, teleporting, text, subtitles, watermark, logo, leaving the frame")
SHOTS = {
    'guan': "Guan Yu lifts the long crescent glaive high, spins it once over his head, then steps forward and cleaves it down diagonally in one huge chop toward the camera, "
            "his green robe and headscarf whipping back. He straightens up, plants the glaive upright beside him with his right hand, "
            "and with his left hand slowly strokes his long black beard downward from chin to chest, calm and proud, eyes half-closed. Hold that pose.",
    'zhang': "Zhang Fei brings the raised spear down, swings it in a big horizontal sweep across the front of the camera, then stamps one foot and thrusts the spear straight at the camera, "
             "roaring with his mouth wide open, red cloth blasting back. Then, in the same continuous motion, he slowly pulls the spear back, straightens up, "
             "stands the spear upright beside him in his right hand, plants his left fist on his hip, throws his head back and laughs heartily, shoulders shaking. Hold that pose. "
             "One single continuous take, every movement flows smoothly into the next.",   # 10-27 第一版从蹲着跳切到叉腰站立，用户：「重新录」
    'liu': "Liu Bei sweeps the two crossed swords outward in two wide arcs, steps forward and thrusts both swords toward the camera in a fast crossing X, "
           "white sleeves and blue ribbons flowing. Then he draws the swords back, lowers both blades to point down at his sides, "
           "stands tall and gives a slow, dignified nod toward the camera with a gentle, determined smile. Hold that pose.",
}
shots = [{'id': f'{k}_ult2', 'ref': f'u_{k}', 'prompt': BASE + m + TAIL, 'neg': NEG} for k, m in SHOTS.items()]
with tarfile.open(out / 'ult2_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k in SHOTS:
        d = ref(ROOT / '美术' / '重画' / 'codex' / f'ult_{k}.png'); add(f'ref_u_{k}.jpg', d); (out / f'ref_u_{k}.jpg').write_bytes(d)
    add('shots_ult2.json', json.dumps(shots, ensure_ascii=False, indent=1).encode()); add('veo_wendao.py', VEO.read_bytes())
print('包', (out / 'ult2_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 8 * .15, 1), '美元')
