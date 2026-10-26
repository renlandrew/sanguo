"""城头武将动作的 Veo 包（10-24，用户：「meshy不行，还是录像吧，用veo 3.1」「刘关张不同招数动作要不一样」）。

首帧：美术/<关羽|张飞|刘备>/背影.png（ChatGPT 画的背影，中灰底 2:3），补成 9:16 1080×1920：
人物连兵器的外框缩到 1100 像素高、居中贴近底部，四周接上灰，挥刀、甩披风时不出画。
每人三条 4 秒：待机（来回播）、普攻、招式。提示词每条都写明背对镜头、灰底不变。
第二版（10-24 用户：「刘关张动作要夸张点，现在身子和脚似乎都不动的。需要的话重新制作」）：第一版只有手在动、脚钉在原地，
改成全身大动作——弓步、拧腰、跳劈、跺脚，反向提示词去掉「走动、上步」、加上「站着不动、僵硬、慢动作」；受击不录（城头武将不挨打）。
在 Cloud Shell 新开 ~/sanguo2 跑，视频传 gs://hero-takes-2000f509/sanguo2/。动作确实大了，但关羽横扫时转身露了正脸、张飞的蛇矛变成了一条真蛇。
第三版（10-24 用户：「用这个图吧，风格可以改一下，不要那么水墨」）：首帧换成新画风的背影 美术/<名>/背影2.png（照 美术/刘关张/桃园三英_透明.png 画），
服装按新图写；提示词加「拧腰也始终背对镜头」「蛇矛是一杆硬钢矛、波浪刃」，反向提示词加蛇、弯矛。~/sanguo3、gs://…/sanguo3/，帧图 美术/武将动作/帧图v3/。
输出 <输出目录>/sanguo_pack.tar.gz = ref_<键>.jpg + shots_sanguo.json + veo_wendao.py（劫云问道那份，原样用），在 Cloud Shell 里：
  SHOTS=shots_sanguo.json SECONDS=4 CAP_USD=12 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_pack.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)

def ref(src):
    # 按人物（含兵器）的外框缩放：外框高 1100 像素（画面 57%），底边离画面底 80 像素、左右居中，其余接上原图的灰
    im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(np.float32)
    rows = np.median(np.concatenate([a[:, :24], a[:, -24:]], axis=1), axis=1)
    diff = np.abs(a - rows[:, None, :]).max(axis=2) > 22; ys, xs = np.where(diff)
    y0b, y1b, x0b, x1b = ys.min(), ys.max(), xs.min(), xs.max()
    k = 1100 / (y1b - y0b); w, h = round(im.width * k), round(im.height * k)
    x0 = round(540 - (x0b + x1b) / 2 * k); y0 = round(1840 - y1b * k)
    gray = np.median(rows, axis=0)
    c = Image.new('RGB', (1080, 1920), tuple(int(v) for v in gray))
    m = np.ones((h, w), np.float32); f = 60; ramp = np.minimum(1, np.arange(max(w, h)) / f)
    m *= ramp[:w][None, :] * ramp[:w][::-1][None, :]; m *= ramp[:h][:, None] * ramp[:h][::-1][:, None]
    c.paste(im.resize((w, h), Image.Resampling.LANCZOS), (x0, y0), Image.fromarray((m * 255).astype(np.uint8)))
    buf = io.BytesIO(); c.save(buf, 'JPEG', quality=88); return buf.getvalue()

BASE = ("Locked-off static camera behind and slightly above a Chinese Three Kingdoms general on a plain, perfectly uniform mid-gray studio background. "
        "He always keeps his back to the camera and his face is never visible. "
        "Exaggerated, dynamic, powerful wuxia action-movie choreography: his legs, feet, hips and torso all move clearly, with deep stances, "
        "big steps and strong weight shifts. He stays inside the frame and ends back on his starting spot. "
        "Even when he twists his torso or swings his weapon, his back stays toward the camera; he never turns his head or body to face the camera. "
        "Keep the detailed painted illustration look of the first frame, the same costume, the same armor and the same weapon; the weapon stays rigid steel. ")
TAIL = " Fast, snappy, forceful timing. The background stays a flat uniform mid-gray the whole time, no ground, no shadow, no smoke."
NEG = ("black background, gradient background, dark background, vignette, spotlight, scenery, landscape, ground, floor, shadow, "
       "face, turning around, facing the camera, profile view, extra weapon, extra people, glow, particles, smoke, mist, fire, dust, "
       "light beams, walking away, leaving the frame, camera movement, zoom, pan, text, subtitles, watermark, logo, "
       "standing still, stiff pose, feet planted, slow motion, front view, face visible, snake, serpent creature, bending spear, rubbery weapon, morphing weapon")
SHOTS = {
 'guan': ('Guan Yu, with long black hair, a green headscarf and a long flowing green robe over ornate bronze-and-steel armor, holding the Green Dragon crescent glaive with a red tassel', [
   ('idle', "sinks into a deep wide horse stance and rocks his weight heavily from his left leg to his right leg and back, knees bending deeply, the long crescent glaive swinging in a slow figure-eight beside him; his long green robe and the tails of his headscarf whip in a strong wind; his broad shoulders heave."),
   ('atk', "coils his whole body, twisting his torso far to the right and dropping into a crouch, then explodes into a big lunge with his left foot stepping far forward and sweeps the long crescent glaive in a huge horizontal arc in front of him, away from the camera, from his right to his left, hips and shoulders twisting hard but his back always toward the camera, the green robe whipping around; then he springs back to his stance."),
   ('skill', "takes two running steps forward and leaps high off both feet, lifting the glaive high over his head with both hands, then crashes down into a deep crouch chopping the crescent glaive straight down in a giant overhead strike in front of him; his green robe billows up behind him; he rises back up.")]),
 'zhang': ('Zhang Fei, a burly general with a topknot and a red headband, in dark steel scale armor with a red sash and ragged red-and-black cloth, holding the Serpent Spear: a long rigid steel spear with a wavy steel blade (a weapon, never a snake)', [
   ('idle', "bounces restlessly on the balls of his feet in a wide brawler's stance, stamping his right foot, rolling his huge shoulders and swinging the long steel spear from side to side; his red sash and ragged cloth flap wildly."),
   ('atk', "drops into a low front lunge with a big step forward and drives the rigid steel spear straight out away from the camera with his whole body behind it, twice in quick succession, his back leg straightening and his hips punching forward on each thrust; then he hops back to his guard."),
   ('skill', "jumps and stamps both feet down hard, slams the butt of the steel spear down beside his feet, throws both arms wide, arches his back and roars forward away from the camera with his whole body shaking; his red sash and ragged cloth are blasted straight back; he stamps once more and settles.")]),
 'liu': ('Liu Bei, with a gold crown on his topknot and pale blue ribbons, in a long white-and-blue robe with ornate steel shoulder armor, holding a straight double-edged sword in each hand', [
   ('idle', "shifts lightly and quickly from foot to foot in a nimble swordsman's stance, knees bent, both straight swords held low and circling at his wrists; his white-and-blue robe and ribbons ripple."),
   ('atk', "springs forward with a quick skipping step and slashes both swords upward and forward in a fast crossing X, his torso twisting and his back foot kicking up behind him, then skips back to his stance."),
   ('skill', "twists hard to the left and then to the right, sweeping both swords in two huge circles around his body like a whirlwind without ever turning to face the camera, the white robe flaring out, then bounds one long step forward and thrusts both swords together far forward.")]),
}
NAME = {'guan': '关羽', 'zhang': '张飞', 'liu': '刘备'}
shots = []
for k, (who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + who + ', ' + motion + TAIL, 'neg': NEG})
with tarfile.open(out / 'sanguo_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k in SHOTS:
        data = ref(ROOT / '美术' / NAME[k] / '背影2.png'); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_sanguo.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'sanguo_pack.tar.gz', (out / 'sanguo_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条')
