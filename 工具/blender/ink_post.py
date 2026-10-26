# 水墨着色（10-24）：把 render_frames.py 渲出的平涂帧变成墨色——明暗按灰度映到墨和纸之间，
# 只留黄巾（赭黄）和红缨（朱红）的颜色，外面加一圈墨线。
# 用法：python3 ink_post.py <输入目录> <输出目录> [band=ochre|red] [keep=0.5] [line=3] [halo=0]
#   band=red：头巾染成朱红（力士用，10-24 用户要和黄巾兵分开）
#   line：墨线粗细（滤镜边长，奇数）；halo：人物外面一圈纸色光晕的宽度（像素，城头武将用，把人从城砖上托出来）
#   vivid：颜色饱和度倍数（10-26 起兵种都用 keep=1 vivid=1.7，不再水墨）
#   keep：留多少原来的颜色（城头武将用，关羽的绿、张飞的黑红、刘备的白蓝要认得出），0 就是全墨色
import os, sys
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageMath
VIVID = 0; RETINT = 0

INK, PAPER, OCHRE, CINN = (29, 26, 23), (238, 230, 214), (214, 160, 40), (178, 63, 42)
BANDS = {'ochre': OCHRE, 'red': (196, 52, 34), 'ink': (52, 46, 40)}          # ink：头巾染黑（衙役）


def lut(c0, c1, gamma=1.0, lo=24, hi=226):
    return [round(c0 + (c1 - c0) * min(1, max(0, (v - lo) / (hi - lo))) ** gamma) for v in range(256)]


def mask(fn, r, g, b):
    return ImageMath.lambda_eval(lambda e: fn(e['r'], e['g'], e['b']) * 255, r=r, g=g, b=b).convert('L')


def ink(im, band='ochre', keep=0.0, line=3, halo=0):
    im = im.convert('RGBA'); r, g, b, a = im.split(); L = im.convert('L')
    base = Image.merge('RGB', [L.point(lut(INK[i], PAPER[i], 1.35, 34, 205)) for i in range(3)])     # 反差拉大：亮处留纸，暗处成墨
    yel = mask(lambda r, g, b: (g > 130) & ((g - b) > 45) & ((r - g) < 55), r, g, b).filter(ImageFilter.GaussianBlur(.6))   # 黄巾约 (192,176,120)、赭黄披风偏红一点；皮肤 (176,144,128) 绿蓝差不够
    red = mask(lambda r, g, b: (r > 100) & (g < 80) & (b < 70) & ((r - g) > 45), r, g, b)
    BC = BANDS[band]
    ych = Image.merge('RGB', [L.point(lut(int(BC[i] * .5), BC[i], .8, 40, 230)) for i in range(3)])
    base = Image.composite(ych, base, yel)
    base = Image.composite(Image.new('RGB', im.size, CINN), base, red)
    if keep > 0: base = Image.blend(base, im.convert('RGB'), keep)
    if VIVID: base = ImageEnhance.Contrast(ImageEnhance.Color(base).enhance(VIVID)).enhance(1.12)
    if VIVID and RETINT: base = Image.composite(ych, base, yel)                           # retint=1：全彩之上把头巾再染成 band 色（邓茂、力士红巾，衙役黑巾），同一个模型的兵种分得开   # vivid=1.7：颜色拉鲜、反差加一点，大色块（10-26 用户：「不要水墨风格了」）
    body = base.copy(); body.putalpha(a)
    big = a.filter(ImageFilter.MaxFilter(line))
    edge = ImageChops.subtract(big, a).filter(ImageFilter.GaussianBlur(.4))
    ln = Image.new('RGBA', im.size, INK + (0,)); ln.putalpha(edge.point(lambda v: int(v * .9)))
    out = Image.alpha_composite(ln, body)
    if halo:
        g = big.filter(ImageFilter.MaxFilter(halo * 2 + 1)).filter(ImageFilter.GaussianBlur(halo * .8))
        hl = Image.new('RGBA', im.size, (246, 240, 226, 0)); hl.putalpha(g.point(lambda v: int(v * .55)))
        out = Image.alpha_composite(hl, out)
    return out


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
    kv = dict(a.split('=', 1) for a in sys.argv[3:]); band = kv.get('band', 'ochre'); keep = float(kv.get('keep', 0)); line = int(kv.get('line', 3)); halo = int(kv.get('halo', 0)); VIVID = float(kv.get('vivid', 0)); RETINT = int(kv.get('retint', 0))
    fs = sorted(f for f in os.listdir(src) if f.endswith('.png'))
    for f in fs: ink(Image.open(os.path.join(src, f)), band, keep, line, halo).save(os.path.join(dst, f))
    print('着色', len(fs), '帧 →', dst)
