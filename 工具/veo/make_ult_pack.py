"""大招特写的 Veo 包（10-25）：关羽、张飞、刘备的觉醒大招，张角天雷，吕布方天画戟，共 5 条，每条 4 秒。
用户：「要录制一些大招的录像？能占据屏幕的大招？」「录大招特写：关羽、张飞、刘备的觉醒大招加张角天雷、吕布方天画戟，共 5 条，花费上限 6 美元」。
首帧：美术/<名>/大招首帧.jpg（ChatGPT 画，中灰底 2:3，腰以上半身、画面下边裁在腰）。补成 9:16：整张缩到 1080 宽贴底，上面接灰（头顶留给举起的兵器）。
镜头不动、灰底不变，招式里不要光效、雷电、烟——这些在游戏里另加，Veo 加了抠不干净。
输出 <输出目录>/ult_pack.tar.gz = ref_<键>.jpg + shots_ult.json + veo_wendao.py，在 Cloud Shell 里：
  SHOTS=shots_ult.json SECONDS=4 CAP_USD=6 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_ult_pack.py <输出目录>
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
    im = Image.open(src).convert('RGB'); im = im.resize((1080, round(im.height * 1080 / im.width)), Image.Resampling.LANCZOS)
    a = np.asarray(im).astype(np.float32); gray = tuple(int(v) for v in np.median(a[:24].reshape(-1, 3), axis=0))
    c = Image.new('RGB', (1080, 1920), gray); y0 = 1920 - im.height
    m = np.ones((im.height, im.width), np.float32); m[:60] *= np.linspace(0, 1, 60)[:, None]   # 上沿和补的灰揉一下，别留一道线
    c.paste(im, (0, y0), Image.fromarray((m * 255).astype(np.uint8)))
    buf = io.BytesIO(); c.save(buf, 'JPEG', quality=90); return buf.getvalue()

BASE = ("Locked-off static camera, plain perfectly uniform mid-gray studio background. Waist-up shot of a character facing the camera, "
        "keep the detailed painted illustration look of the first frame, the same costume, face and weapon. He performs his ultimate move: ")
TAIL = " Powerful, fast, dramatic motion with a clear wind-up, strike and held final pose. The background stays a flat uniform mid-gray the whole time."
NEG = ("black background, gradient background, dark background, vignette, spotlight, scenery, sky, ground, floor, shadow, "
       "glow, light rays, lightning, sparks, fire, flames, smoke, mist, dust, particles, magic effects, energy, aura, "
       "turning around, back view, extra people, extra weapons, camera movement, zoom, cut, text, subtitles, watermark, logo")
SHOTS = {
    'guan': ('关羽', "in one explosive motion he brings the raised crescent-moon glaive down toward the camera in a huge vertical chop, the blade sweeping through the frame; "
             "his long beard, green headscarf tails and green sleeves whip back in a strong wind; he finishes holding the glaive low and glares into the camera."),
    'zhang': ('张飞', "he draws a deep breath, then roars straight at the camera with all his might, eyes bulging, bristling beard and red headband streaming back as if in a gale; "
              "at the peak of the roar he thrusts the long serpent spear forward toward the camera and holds it there, still roaring."),
    'liu': ('刘备', "from the crossed position he sweeps the twin swords outward in two wide arcs, then brings both swords forward and crosses them again in front of his chest; "
            "his sleeves and blue ribbons flow in the wind; calm, determined gaze; he ends holding the swords crossed, looking into the camera."),
    'zhangjiao': ('张角', "he thrusts the ringed staff high above his head as if calling down heaven's thunder, then swings it down to point straight at the camera while his other hand flings a paper talisman forward; "
                  "his white beard, long hair and yellow robes whip violently in a strong wind; he ends pointing the staff at the camera with a fierce shout."),
    'lvbu': ('吕布', "he swings the Sky Piercer halberd in a huge horizontal sweep across the front of the camera from right to left, the blade passing close to the lens, "
             "then spins it once and plants it upright beside him; his red cape and long pheasant-feather crown whip in the wind; he ends glaring into the camera."),
}
shots = [{'id': f'{k}_ult', 'ref': k, 'prompt': BASE + motion + TAIL, 'neg': NEG} for k, (_, motion) in SHOTS.items()]
with tarfile.open(out / 'ult_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k, (nm, _) in SHOTS.items():
        data = ref(ROOT / '美术' / nm / '大招首帧.jpg'); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_ult.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'ult_pack.tar.gz', (out / 'ult_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
