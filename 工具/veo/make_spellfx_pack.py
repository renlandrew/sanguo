"""魔兽风法术 Veo 录像第二批（10-27，用户发了五张魔兽截图：「法术多做这种效果」→「按方案用 Veo 录这 6 个法术，上限 5 美元」）。
照 make_vfx_pack.py：纯黑底、首帧纯黑，回来按亮度去黑、切成逐帧图集（cut_vfx.py 的 PLAN 加了 boss_* 六个键），重招落地时叠在画稿和墨流上播。
每员首领一条 4 秒，颜色和 drawBossUlt 的 BOSS_FX 一致；不要人物，只录法术本身；简笔大色块，不要满屏小火花。
输出 <输出目录>/spellfx_pack.tar.gz，在 Cloud Shell 里：SHOTS=shots_spellfx.json SECONDS=4 CAP_USD=5 python3 veo_wendao.py
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
 ('sp_sigil_purple', "seen from a high angle, a large glowing violet magic circle appears on the ground in the center and slowly rotates: concentric hand-painted rings with irregular glowing rune glyphs between them, "
                     "a soft violet light rising from it; a few large wisps of violet light drift upward, then it fades. The circle is drawn with loose painterly brush strokes, not perfect geometric lines."),
 ('sp_arcs', "two crackling bundles of violet-white electric arcs writhe and flicker in the center of the frame, as if around two raised hands of an invisible caster, "
             "bright white cores with violet glow, short arcs jumping outward and snapping back; flickering continuously, then fading."),
 ('sp_face', "a swirling vortex of violet and magenta energy opens in the center of the frame and a huge glowing orange demonic skull face with wide open fanged jaws and glowing eyes surges forward out of it, "
             "roaring, surrounded by streaming violet energy, then it shatters into violet light and fades."),
 ('sp_dome', "a large translucent dome barrier of shimmering violet-blue energy rises up from the bottom of the frame and covers the lower two thirds, "
             "its surface rippling with soft light, a few large glowing runes floating along its edge; it flashes bright once as if struck, then slowly fades."),
 ('sp_spears', "many glowing blue-white spears of light rain down from the top of the frame at a slight angle and stab into the bottom of the frame one after another, "
               "each impact bursting into a bright white flash and a few large ice-like shards; about eight spears in total, then everything fades."),
 ('sp_sigil_gold', "seen from a high angle, a large glowing golden magic circle with hand-painted irregular rune glyphs appears on the ground in the center, flashes brightly and rotates once, "
                   "golden light and a few peach-blossom petals rising from it, then it fades. Painterly brush strokes, not perfect geometric lines."),
]
shots = [{'id': f'fx{i}_{k}', 'ref': 'black', 'prompt': BASE + p + TAIL, 'neg': NEG} for i, (k, p) in enumerate(SHOTS)]
with tarfile.open(out / 'spellfx_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    buf = io.BytesIO(); Image.new('RGB', (1080, 1920), (0, 0, 0)).save(buf, 'JPEG', quality=90); add('ref_black.jpg', buf.getvalue())
    add('shots_spellfx.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'spellfx_pack.tar.gz', (out / 'spellfx_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
