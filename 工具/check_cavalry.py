# 骑兵交付检查：八方向、帧数、闭环、脚底、透明底、网页体积和模型三角面数。
import json, struct
from pathlib import Path
from PIL import Image, ImageChops
root = Path(__file__).resolve().parents[1]; total = 0
for d in range(8):
    base = root / ('原型/img/enemy_qibing_%d' % d)
    meta = json.loads(base.with_suffix('.json').read_text()); atlas = Image.open(base.with_suffix('.png')).convert('RGBA')
    assert meta['direction'] == d and meta['light'] == 'lit'
    assert max(atlas.size) <= 4096 and atlas.getextrema()[3][0] == 0
    run = meta['anims']['run']; assert len(run['rects']) == 8
    images = []
    for x, y, w, h in run['rects']:
        assert x >= 0 and y >= 0 and x+w <= atlas.width and y+h <= atlas.height
        im = atlas.crop((x,y,x+w,y+h)); images.append(im)
        assert im.getbbox()[3] == run['anchor'][1], (d, '蹄底未对齐')
    assert ImageChops.difference(images[0], images[-1]).getbbox() is None, (d, '首尾不一致')
    assert any(ImageChops.difference(images[0], im).getbbox() for im in images[1:-1]), (d, '没有动作')
    for key in ['ram', 'hit', 'die', 'fly']: assert meta['anims'][key]['rects']
    total += base.with_suffix('.png').stat().st_size
assert total <= 2_000_000, total
with open(root / '素材/3d/qibing.glb', 'rb') as f:
    magic, version, length = struct.unpack('<III', f.read(12)); n, kind = struct.unpack('<II', f.read(8)); gltf = json.loads(f.read(n))
assert magic == 0x46546c67 and version == 2
triangles = sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives'])
assert triangles <= 30000 and gltf.get('animations') and gltf.get('skins')
print('通过：8 方向 × 8 帧，逐帧蹄底同线、首尾一致、有动作、透明底；图集 %d 字节；模型 %d 三角面。' % (total, triangles))
