"""敌方首领重招的 Veo 法术录像（10-27，用户：「需要的话就用veo 3.1 录制法术动作」「用 Veo 录 6 个首领法术，上限 5 美元」）。
照 make_vfx_pack.py：纯黑底、首帧纯黑，回来按亮度去黑、切成逐帧图集（cut_vfx.py 的 PLAN 加了 boss_* 六个键），重招落地时叠在画稿和墨流上播。
每员首领一条 4 秒，颜色和 drawBossUlt 的 BOSS_FX 一致；不要人物，只录法术本身；简笔大色块，不要满屏小火花。
输出 <输出目录>/bossfx_pack.tar.gz，在 Cloud Shell 里：SHOTS=shots_bossfx.json SECONDS=4 CAP_USD=5 python3 veo_wendao.py
"""
import io, json, sys, tarfile
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
VEO = HERE.parents[2] / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
BASE = "On a pure black background, "
TAIL = (" Locked-off static camera; nothing else in the frame. Hand-painted fantasy game spell effect with bold brush strokes and large soft glowing color shapes, "
        "vivid saturated colors, clean and readable; only a few large sparks, never a dense spray of tiny particles. The background stays pure black the whole time.")
NEG = ("scenery, landscape, ground, floor, sky, clouds, people, person, character, hands, body, armor, weapon held by a person, "
       "gray background, white background, bright background, gradient background, frame, border, dense tiny sparks, glitter, noise, "
       "geometric lines, perfect circles, rings, text, subtitles, watermark, logo, camera movement, zoom, pan")
SHOTS = [
 ('boss_dengmao', "a giant spear-thrust of golden-ochre light shoots straight upward from the bottom edge to near the top of the frame, a long glowing spearhead leading it, "
                  "with a thick trail of golden energy and brown dust behind; at the end it bursts into a big golden flash and a cloud of dust, then fades."),
 ('boss_zhangjiao', "a massive bolt of heavenly lightning strikes from the top edge down to the bottom edge of the frame: a thick zigzag bolt with a white-gold core and a broad violet glow, "
                    "with three or four big bends, no thin branching; it flickers brightly two or three times, and where it hits the bottom it bursts into a violet and gold explosion, then fades."),
 ('boss_huzhen', "two huge crimson-red curved blade slashes cut across the center of the frame from the upper left and upper right, crossing in a big X, "
                 "each a broad crescent of red light with a bright white edge; where they cross they burst into a red-orange flash with a few large embers, then fade."),
 ('boss_huaxiong', "a gigantic steel-blue glaive slash falls from the top edge straight down to the bottom edge of the frame like a falling guillotine of cold blue light with a white-hot edge; "
                   "when it reaches the bottom it smashes into a big explosion of orange fire and black smoke that spreads sideways along the bottom, then fades."),
 ('boss_lijue', "a wide crescent blade of bronze-gold light sweeps horizontally from the left edge to the right edge through the middle of the frame, "
                "leaving a broad trailing arc of golden light and orange fire behind it, then the arc bursts into a few large embers and fades."),
 ('boss_lvbu', "a fiery serpentine dragon made of crimson and violet flame spirals upward from the bottom of the frame, coiling twice, its head roaring at the top, "
               "then the whole dragon bursts into a huge crimson and violet explosion of flame that fills the middle of the frame, then fades."),
]
shots = [{'id': f'fx{i}_{k}', 'ref': 'black', 'prompt': BASE + p + TAIL, 'neg': NEG} for i, (k, p) in enumerate(SHOTS)]
with tarfile.open(out / 'bossfx_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    buf = io.BytesIO(); Image.new('RGB', (1080, 1920), (0, 0, 0)).save(buf, 'JPEG', quality=90); add('ref_black.jpg', buf.getvalue())
    add('shots_bossfx.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'bossfx_pack.tar.gz', (out / 'bossfx_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
