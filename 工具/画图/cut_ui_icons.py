"""11-18 新皮肤图标：把 draw_ui_icons.sh 画的整张图切成一个个图标 → 原型/img/ui_n_<名>.png。
不按网格硬切（GPT 排的格子不一定准）：先抠底（有透明通道直接用；没有就从四边泛洪抠掉底色），
再把前景膨胀一圈连成块（旗和卷轴、头盔和红缨算一个），取最大的 N 块，按行、列排序后对上名字。
每个图标裁到内容边、四周留 6%、补成正方形、缩到 160 像素。
用法：python3 工具/画图/cut_ui_icons.py
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

R = Path(__file__).resolve().parents[2]
SRC = R / '美术' / '界面' / '新图标'
OUT = R / '原型' / 'img'
SHEETS = {
    'nav_sheet': ['general', 'armory', 'campaign', 'ploy', 'camp', 'sys'],
    'res_sheet': ['精铁', '残页', '体力'],
}
SIZE = 160


def matte(im):
    a = np.asarray(im.convert('RGBA')).copy()
    cor = [a[3, 3, 3], a[3, -4, 3], a[-4, 3, 3], a[-4, -4, 3]]
    if min(cor) < 40:
        return a, '透明'
    rgb = a[..., :3].astype(np.float32)
    edge = np.concatenate([rgb[:4].reshape(-1, 3), rgb[-4:].reshape(-1, 3), rgb[:, :4].reshape(-1, 3), rgb[:, -4:].reshape(-1, 3)])
    bg = np.median(edge, axis=0)
    near = np.sqrt(((rgb - bg) ** 2).sum(axis=2)) < 38
    lab, _ = ndi.label(near)
    ids = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    ids = ids[ids > 0]
    m = np.isin(lab, ids)
    al = Image.fromarray(((~m) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    a[..., 3] = np.minimum(a[..., 3], np.asarray(al))
    return a, '抠底'


for sheet, names in SHEETS.items():
    p = SRC / f'{sheet}.png'
    if not p.exists():
        print('没有', p.name)
        continue
    a, how = matte(Image.open(p))
    H, W = a.shape[:2]
    fg = a[..., 3] > 40
    grow = ndi.binary_dilation(fg, iterations=max(4, int(min(H, W) * .018)))
    lab, n = ndi.label(grow)
    sizes = ndi.sum(fg, lab, range(1, n + 1))
    keep = sorted(np.argsort(sizes)[::-1][:len(names)] + 1)
    boxes = []
    for k in keep:
        ys, xs = np.where((lab == k) & fg)
        boxes.append((ys.min(), xs.min(), ys.max() + 1, xs.max() + 1))
    # 按行再按列排：行高按图标平均高度分桶
    hmean = np.mean([b[2] - b[0] for b in boxes])
    boxes.sort(key=lambda b: (round(((b[0] + b[2]) / 2) / hmean), (b[1] + b[3]) / 2))
    if len(boxes) < len(names):
        print(sheet, f'只找到 {len(boxes)} 块，要 {len(names)} 块')
    for nm, (y0, x0, y1, x1) in zip(names, boxes):
        crop = a[y0:y1, x0:x1].copy()
        # 同一块里别的图标溢进来的碎片清掉：只留这块里最大的连通前景（加一圈膨胀容错）
        f2 = crop[..., 3] > 40
        l2, n2 = ndi.label(ndi.binary_dilation(f2, iterations=3))
        if n2 > 1:
            big = np.argmax(ndi.sum(f2, l2, range(1, n2 + 1))) + 1
            crop[..., 3] = np.where(l2 == big, crop[..., 3], 0)
        h, w = crop.shape[:2]
        s = int(max(h, w) * 1.12)
        sq = np.zeros((s, s, 4), np.uint8)
        oy, ox = (s - h) // 2, (s - w) // 2
        sq[oy:oy + h, ox:ox + w] = crop
        im = Image.fromarray(sq).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        dst = OUT / f'ui_n_{nm}.png'
        im.save(dst, optimize=True)
        print(sheet, how, nm, (x0, y0, x1, y1), dst.name, dst.stat().st_size // 1024, 'KB')
