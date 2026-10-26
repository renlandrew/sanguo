"""刘关张招式特效的 Veo 包（10-25）。

用户：「现在做法术效果，参考雾港，但不能抄，要绚丽」，看了程序画的第一版说「太假」——平涂的矢量形状放在厚涂的人物和背景旁边很廉价。
所以改录真实的特效：Veo 在纯黑底上录，回来把黑底按亮度转成透明（亮的地方不透明、颜色还原），切成逐帧图集，游戏里按位置、方向、大小播放。
首帧给一张纯黑图（特效从黑里长出来，背景也更容易保持纯黑）。飞行的（刀气、剑气、飞剑）要原地循环，命中和招式是一次性的。
输出 <输出目录>/vfx_pack.tar.gz = ref_black.jpg + shots_vfx.json + veo_wendao.py，在 Cloud Shell 里：
  SHOTS=shots_vfx.json SECONDS=4 CAP_USD=6 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_vfx_pack.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
VEO = HERE.parents[2] / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)

BASE = "On a pure black background, "
TAIL = (" Locked-off static camera, seen slightly from above; nothing else in the frame. "
        "High-quality fantasy video game visual effect, vivid glowing colors, crisp detail. The background stays pure black the whole time.")
NEG = ("scenery, landscape, ground, floor, sky, people, person, character, hands, body, armor, "
       "gray background, white background, bright background, gradient background, frame, border, "
       "text, subtitles, watermark, logo, camera movement, zoom, pan")
SHOTS = [
 # 关羽
 ('blade', "a glowing crescent-shaped energy blade of jade-green light appears in the center of the frame, curved like the edge of a Chinese guandao glaive, "
           "with a bright white-hot cutting edge on its convex upper side and flowing translucent green energy wisps and tiny golden sparks streaming downward behind it. "
           "It hovers in place and pulses, its energy rippling and flickering continuously, never leaving the center."),
 ('bladehit', "a quick burst of jade-green energy in the center of the frame: a diagonal slash of green-white light flashes and shatters into glowing jade shards "
              "and golden sparks that scatter outward in all directions and fade away."),
 ('dragon', "a translucent Chinese dragon made of glowing jade-green energy, with shimmering scales, golden whiskers, golden horns and a flowing golden mane, "
            "bursts in from the left edge and swoops in a wide upward arc across the frame to the right edge, its long serpentine body leaving a sweeping crescent trail of green light; "
            "then the trail bursts into green and golden sparks and dragon scales that scatter and fade."),
 # 张飞
 ('spear', "a spear-thrust streak shoots straight upward from the bottom edge to the center of the frame: a dark iron core wrapped in a wavy serpent-shaped blade of fiery red-orange light; "
           "at the tip it bursts into a spray of red-orange sparks and glowing embers, then the streak retracts and fades."),
 ('roar', "a massive shockwave bursts outward from the bottom center of the frame: a broad expanding semicircular wave front of orange-red fiery energy with swirling dust, "
          "followed by two more fainter wave fronts, glowing orange cracks and flying sparks and debris spreading upward across the whole frame, then fading away."),
 # 刘备
 ('twinqi', "two slender streaks of sword light, one azure blue and one gold, spiral tightly around each other like a double helix, pointing straight upward in the center of the frame, "
            "with a few pink peach blossom petals swirling around them; the light flows and shimmers continuously while they stay in place."),
 ('flysword', "a glowing Chinese straight double-edged sword wreathed in azure-blue light points straight upward in the center of the frame, its blade shining white and blue, "
              "a stream of blue light and pink peach blossom petals trailing below it; it hovers in place, gently shimmering."),
 ('cross', "two glowing sword slashes, one azure blue and one gold, cut across the center of the frame in a crossing X, bursting with white light, "
           "sparks and pink peach blossom petals that scatter outward, then fade away."),
]
shots = [{'id': f'fx{i}_{k}', 'ref': 'black', 'prompt': BASE + p + TAIL, 'neg': NEG} for i, (k, p) in enumerate(SHOTS)]
with tarfile.open(out / 'vfx_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    buf = io.BytesIO(); Image.new('RGB', (1080, 1920), (0, 0, 0)).save(buf, 'JPEG', quality=90); add('ref_black.jpg', buf.getvalue())
    add('shots_vfx.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'vfx_pack.tar.gz', (out / 'vfx_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条')
