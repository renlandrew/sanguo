"""敌人（正面朝城墙冲来）的 Veo 包（10-24）：张角（斗将大战）和黄巾骑兵，Meshy 绑不了马、张角要施法召兵，所以和城头武将一样用 Veo 录。

画风照用户定的新版（10-24：「用这个图吧，风格可以改一下，不要那么水墨，已经画好的士兵就算了」）：美术/<名>/正面.png（ChatGPT 画，中灰底 2:3）。
首帧照 make_pack.py 的办法补成 9:16（人物连兵器外框缩到 1100 像素高、贴近底部、四周接上灰）。
骑兵冲锋要原地跑：提示词写镜头和马同速后退，人马在画面里大小、位置都不变（灰底看不出镜头在动）。
输出 <输出目录>/foe_pack.tar.gz = ref_<键>.jpg + shots_foe.json + veo_wendao.py，在 Cloud Shell 里：
  SHOTS=shots_foe.json SECONDS=4 CAP_USD=5 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_foe_pack.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)

def ref(src, height=1100):
    # 同 make_pack.py：按人物外框缩放、贴底居中，其余接上原图的灰
    im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(np.float32)
    rows = np.median(np.concatenate([a[:, :24], a[:, -24:]], axis=1), axis=1)
    diff = np.abs(a - rows[:, None, :]).max(axis=2) > 22; ys, xs = np.where(diff)
    y0b, y1b, x0b, x1b = ys.min(), ys.max(), xs.min(), xs.max()
    k = min(height / (y1b - y0b), 960 / (x1b - x0b)); w, h = round(im.width * k), round(im.height * k)
    x0 = round(540 - (x0b + x1b) / 2 * k); y0 = round(1840 - y1b * k)
    gray = np.median(rows, axis=0)
    c = Image.new('RGB', (1080, 1920), tuple(int(v) for v in gray))
    m = np.ones((h, w), np.float32); f = 60; ramp = np.minimum(1, np.arange(max(w, h)) / f)
    m *= ramp[:w][None, :] * ramp[:w][::-1][None, :]; m *= ramp[:h][:, None] * ramp[:h][::-1][:, None]
    c.paste(im.resize((w, h), Image.Resampling.LANCZOS), (x0, y0), Image.fromarray((m * 255).astype(np.uint8)))
    buf = io.BytesIO(); c.save(buf, 'JPEG', quality=88); return buf.getvalue()

BASE = ("Locked-off static camera in front of and slightly above a character on a plain, perfectly uniform mid-gray studio background. "
        "He faces the camera the whole time. Keep the detailed painted illustration look of the first frame, the same costume and the same props. ")
TAIL = " The background stays a flat uniform mid-gray the whole time, no ground, no shadow, no scenery."
NEG = ("black background, gradient background, dark background, vignette, spotlight, scenery, landscape, ground, floor, shadow, "
       "turning around, back view, extra people, extra horses, glow, particles, smoke, mist, fire, lightning, light beams, magic effects, "
       "leaving the frame, zoom, text, subtitles, watermark, logo")
SHOTS = {
 'zhangjiao': ('the Yellow Turban leader Zhang Jiao, an old Taoist sorcerer with a long white beard, a yellow Taoist crown and yellow headband, '
               'a wide bright-yellow robe with red talisman patterns, holding a nine-section staff hung with bronze bells in his left hand and a paper talisman in his right hand', [
   ('idle', "stands his ground swaying slightly and mutters an incantation; his yellow robe, wide sleeves and the paper talismans flutter in a strong wind; the bells on his staff swing. Small, looping motion."),
   ('cast', "raises the nine-section staff high above his head and thrusts the paper talisman forward toward the camera, chanting fiercely; his robe, sleeves and beard whip upward as if in a storm; then he lowers the staff again."),
   ('summon', "spreads both arms wide and sweeps them up to the sky, then stamps the butt of the staff down hard beside his feet and throws both hands forward, commanding unseen troops to charge; his sleeves billow."),
   ('die', "is struck by a heavy blow, staggers back, drops the staff, sinks to his knees and slowly collapses to the floor.")]),
 'qibing': ('a Yellow Turban cavalryman with a yellow headscarf and leather armor, riding a chestnut horse, holding a long spear', [
   ('run', "gallops straight toward the camera at full speed; the camera dollies backward at exactly the same speed, so the horse and rider stay at the same size and in the same place in the frame, galloping in place; the horse's legs, mane and the rider's scarf move vigorously. Continuous looping gallop."),
   ('ram', "reins in the horse, which rears up on its hind legs; the rider stabs the long spear down and forward toward the camera twice, then the horse comes back down."),
   ('die', "is knocked off the horse by a heavy blow and falls backward to the floor; the rider lies still.")]),
}
NAME = {'zhangjiao': '张角', 'qibing': '黄巾骑兵'}
shots = []
for k, (who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + 'He is ' + who + '. He ' + motion + TAIL, 'neg': NEG})
with tarfile.open(out / 'foe_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k in SHOTS:
        data = ref(ROOT / '美术' / NAME[k] / '正面.png'); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_foe.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'foe_pack.tar.gz', (out / 'foe_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条')
