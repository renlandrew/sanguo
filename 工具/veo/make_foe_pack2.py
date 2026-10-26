"""第 11–30 关敌人和友军的 Veo 包（10-25）：西凉铁骑、西凉弓骑、并州狼骑、胡轸、华雄、李傕、高顺、吕布、潘凤、武安国，共 31 条。
用户：「可以，先画完剩下的首帧，然后在 Cloud Shell 里录 Veo，约 30 条，花费上限 20 美元」。
首帧：美术/<名>/正面.jpg（ChatGPT 画，中灰底 2:3），补成 9:16 的办法同 make_foe_pack.py（ref 函数直接借它的）。
骑兵和冲锋要原地跑：镜头和人马同速后退，人马在画面里大小、位置都不变。
输出 <输出目录>/foe_pack2.tar.gz = ref_<键>.jpg + shots_foe2.json + veo_wendao.py，在 Cloud Shell 里：
  SHOTS=shots_foe2.json SECONDS=4 CAP_USD=20 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_foe_pack2.py <输出目录>
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
    # 同 make_foe_pack.py：按人物外框缩放、贴底居中，其余接上原图的灰
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
GALLOP = ("gallops straight toward the camera at full speed; the camera dollies backward at exactly the same speed, so the horse and rider stay at the same size "
          "and in the same place in the frame, galloping in place; the horse's legs, mane and tail and the rider's cape move vigorously. Continuous looping gallop.")
RUN = ("charges straight toward the camera on foot at a heavy run; the camera dollies backward at exactly the same speed, so he stays at the same size "
       "and in the same place in the frame, running in place; his arms, cape and armor plates swing with each stride. Continuous looping run.")
FALL = "is knocked off the horse by a heavy blow and falls backward to the floor; the rider lies still."
DIE = "is struck by a heavy blow, staggers back, drops his weapon, sinks to his knees and slowly collapses to the floor."
IDLE = "stands his ground in a fighting stance, breathing heavily and shifting his weight; his cape and tassels flutter in a strong wind. Small, looping motion."
SUMMON = "raises his weapon high and sweeps his free arm forward, roaring a command for unseen troops behind him to charge, then returns to his stance."
SHOTS = {
 'tieqi': ('西凉铁骑', "a Xiliang heavy cavalryman of Dong Zhuo's army in black and dark-red lamellar armor and a round helmet with a red tassel, riding a tall black armored warhorse, holding a long spear pointed forward", [
   ('run', GALLOP),
   ('ram', "reins in the horse, which rears up on its hind legs; the rider stabs the long spear down and forward toward the camera twice, then the horse comes back down."),
   ('die', FALL)]),
 'gongqi': ('西凉弓骑', "a light Xiliang horse archer in leather armor with a flying red cape and a fur hat, riding a dun horse, holding a recurve bow, a quiver of arrows on his back", [
   ('run', GALLOP),
   ('shoot', "keeps galloping in place toward the camera while the camera dollies backward at the same speed; he pulls an arrow from the quiver, nocks it, draws the bow to full and looses it straight toward the camera, then reaches for the next arrow."),
   ('die', FALL)]),
 'langqi': ('并州狼骑', "a Bingzhou wolf rider of Lü Bu's army wearing a whole grey-white wolf pelt with the wolf's head over his helmet, holding a curved saber high, riding a lean, fast blue-grey horse", [
   ('run', GALLOP),
   ('ram', "reins in the horse, which rears up; the rider slashes the curved saber down and forward toward the camera twice in big arcs, then the horse comes back down."),
   ('die', FALL)]),
 'huzhen': ('胡轸', "the Dong Zhuo general Hu Zhen, a fierce middle-aged man with a short brown beard and a bronze helmet, in bronze-brown scale armor with a ragged ochre cape, a ring-pommel sabre in each hand", [
   ('idle', IDLE),
   ('combo', "lunges toward the camera and slashes with both sabres in a fast cross-cut, left then right, then a final double downward chop, and steps back into his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'huaxiong': ('华雄', "the Dong Zhuo general Hua Xiong, a huge bearded warrior in black-and-red heavy armor with a ragged red cape, holding a broad heavy sabre", [
   ('idle', IDLE),
   ('taunt', "points the heavy sabre up at the camera as if at the city wall above, throws his head back and bellows insults, beats his chest with his fist and laughs scornfully."),
   ('heavy', "lifts the broad heavy sabre high over his head with both hands and brings it crashing down toward the camera in one huge chop, then heaves it back up to his shoulder."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'lijue': ('李傕', "the Dong Zhuo general Li Jue, a lean hawk-nosed man with a thin moustache and a sly grin, in silver-grey iron armor over a deep-purple robe with loot pouches on his belt, holding a long-handled broad sabre across his body", [
   ('idle', IDLE),
   ('heavy', "swings his long sabre in one wide horizontal sweep from right to left across the front of the camera, then back to his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'gaoshun': ('高顺', "Lü Bu's general Gao Shun, commander of the Trap-Breaking Camp, a stern square-faced man in dark-silver heavy scale armor with a plain white cape, a tall rectangular iron shield on his left arm and a short halberd in his right hand", [
   ('run', RUN),
   ('ram', "stops, braces, and slams his big shield forward toward the camera twice like a battering ram, then strikes once with his weapon."),
   ('die', DIE)]),
 'lvbu': ('吕布', "the peerless warrior Lü Bu in ornate gold-and-red armor with a long pheasant-feather crown and a flowing red cape, holding the Sky Piercer halberd", [
   ('idle', IDLE),
   ('heavy', "swings the halberd in a huge horizontal sweep across the front of the camera, spins it once over his head and brings it down in a second sweep, then plants it."),
   ('rush', RUN),
   ('die', DIE)]),
 'panfeng': ('潘凤', "the general Pan Feng, a burly laughing man with a full beard and a red-tasselled helmet, in ochre-orange leather armor with a bronze chest mirror, a huge broad battle axe on his shoulder", [
   ('ram', "swings the huge battle axe off his shoulder, raises it high with both hands and chops it down hard toward the camera, then swings it back up and chops again.")]),
 'wuanguo': ('武安国', "the general Wu Anguo, a dark-faced bald man with a grey cloth headband, in dark-brown leather armor with his right arm bare, holding a long-handled eight-sided iron hammer", [
   ('ram', "heaves the long-handled iron hammer up, swings it round in a big arc and smashes it down toward the camera, then heaves it back and smashes again.")]),
}
shots = []
for k, (_, who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + 'He is ' + who + '. He ' + motion + TAIL, 'neg': NEG})
def front(nm):
    return next(p for p in (ROOT / '美术' / nm / '正面.jpg', ROOT / '美术' / nm / '正面.png') if p.exists())
with tarfile.open(out / 'foe_pack2.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k, (nm, _, _) in SHOTS.items():
        data = ref(front(nm)); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_foe2.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'foe_pack2.tar.gz', (out / 'foe_pack2.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
