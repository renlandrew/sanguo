"""11-12 讨伐三只怪物的 Veo 动作（用户：「怪物的战斗动作呢」→ 我说逐帧动作要用 Veo、要花钱 → 「做」）。
每只怪物三档形态各录一条 4 秒：先站着喘一秒（待机帧从这里取），再蓄力、出手、收回原样。共 9 条 × 4 秒 × .15 = 5.4 美元，
和第二章敌将同一目录 ~/sanguo_foe6 记账（已用 25.2，上限 32）：SHOTS=shots_hunt.json SECONDS=4 LAST=1 CAP_USD=32 python3 veo_wendao.py
首帧：美术/讨伐/<目录>/form<N>.png（透明底）铺中灰，贴底居中放进 1080×1920。蛟是横图，按宽放。
用法：python3 三国志/工具/veo/make_hunt_pack.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
BASE = ("Locked-off static camera in front of a giant monster on a plain, perfectly uniform mid-gray studio background. "
        "It faces the camera the whole time and stays in the same place. Keep the detailed painted illustration look of the first frame, the same body, colors and markings. ")
TAIL = " Then it returns to exactly the starting pose. The background stays a flat uniform mid-gray the whole time, no ground, no shadow, no scenery."
NEG0 = ("black background, gradient background, dark background, vignette, spotlight, scenery, landscape, ground, floor, shadow, "
        "turning around, back view, extra creatures, people, leaving the frame, walking away, camera movement, zoom, text, subtitles, watermark, logo")
NEG = [NEG0 + ", glow, particles, smoke, mist, fire, lightning, light beams, magic effects", NEG0 + ", smoke, mist, light beams", NEG0 + ", smoke, mist, light beams"]
FX = ['', ' The glowing cracks on its body flicker.', ' The flames and sparks on its body keep burning and flickering.']
MON = {
 'juling': ('黄巾力士', "a towering clay-skinned giant with a yellow turban and a ragged yellow waist cloth tied with a thick rope, bare-chested and hugely muscular",
   "It stands breathing heavily for one second, shifting its weight. Then it raises its right fist high above its head, leaning back, and slams both fists down onto the ground in front of its feet in one huge blow, crouching low."),
 'shanjun': ('山君', "a gigantic tiger crouching low, facing the camera",
   "It crouches breathing for one second, its tail swaying. Then it presses its body even lower with its hindquarters raised, and lunges up and forward toward the camera, swiping with both front paws and roaring with its mouth wide open."),
 'jiao': ('蛟', "a giant hornless river dragon with a long scaled body coiled in big arcs across the frame and its head raised in the middle",
   "It sways its raised head slowly for one second, its coils shifting. Then it rears its head and neck far back with its throat swelling, and snaps its head forward and down toward the camera with its jaws wide open, roaring."),
}
shots = []
with tarfile.open(out / 'hunt_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k, (d, who, motion) in MON.items():
        for n in (1, 2, 3):
            im = Image.open(ROOT / '美术' / '讨伐' / d / f'form{n}.png').convert('RGBA'); im = im.crop(im.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox())
            cv = Image.new('RGBA', (1080, 1920), (128, 128, 128, 255)); s = min(960 / im.width, 1500 / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.Resampling.LANCZOS)
            cv.alpha_composite(im, ((1080 - im.width) // 2, 1760 - im.height)); b = io.BytesIO(); cv.convert('RGB').save(b, 'JPEG', quality=92); data = b.getvalue()
            rk = f'{k}{n}'; add(f'ref_{rk}.jpg', data); (out / f'ref_{rk}.jpg').write_bytes(data)
            shots.append({'id': f'{rk}_act', 'ref': rk, 'prompt': BASE + 'It is ' + who + '. ' + motion + FX[n - 1] + TAIL, 'neg': NEG[n - 1]})
    add('shots_hunt.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'hunt_pack.tar.gz', (out / 'hunt_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
