#!/bin/bash
# 10-28 敌人「纸片感」对比测试（不花 Meshy 点数）：拿已有的黄巾兵模型，跑步动作用三种方式各渲一遍，拼成一张对比图
#   A 现在用的：Workbench 柔光 + 描边，256
#   B Eevee 真光照（主光 + 轮廓光 + 环境光遮蔽 + 软阴影），256
#   C 同 B，384 大一号（手机上更细）
# 用法：bash 三国志/工具/test_lit.sh [兵种=黄巾兵] → 出 美术/对比_立体化_<兵种>.png
cd "$(dirname "$0")/.."; CN="${1:-黄巾兵}"; B=/Applications/Blender.app/Contents/MacOS/Blender
G="美术/$CN/v2/动作/animation_glb_url.glb"; [ -f "$G" ] || { echo "没找到 $G"; exit 1; }
T=$(mktemp -d); W="wpn=spear ax=x 'carry={\"Run_02\": [0.3, -0.2, 1]}' scale=2.8 only=Run_02"
for v in "A light=studio size=256" "B light=lit size=256" "C light=lit size=384"; do set -- $v; k=$1; shift
  eval "$B -b -P 工具/blender/render_frames.py -- \"$G\" \"$T/$k\" n=8 $* $W" 2>&1 | grep -E "渲完|rror" ; done
python3 - "$T" "美术/对比_立体化_$CN.png" <<'PY'
import sys, os
from PIL import Image, ImageDraw
T, out = sys.argv[1], sys.argv[2]; rows = []
for k, name in (('A', 'A 现在：平涂柔光+描边'), ('B', 'B 真光照'), ('C', 'C 真光照·大一号')):
    fs = sorted(f for f in os.listdir(os.path.join(T, k)) if f.endswith('.png'))[:4]
    ims = [Image.open(os.path.join(T, k, f)).convert('RGBA').resize((256, 256)) for f in fs]
    row = Image.new('RGBA', (256 * len(ims), 290), (196, 170, 120, 255)); d = ImageDraw.Draw(row); d.text((8, 4), name, fill=(40, 20, 10, 255))
    for i, im in enumerate(ims): row.alpha_composite(im, (256 * i, 34))
    rows.append(row)
sheet = Image.new('RGBA', (max(r.width for r in rows), sum(r.height for r in rows))); y = 0
for r in rows: sheet.paste(r, (0, y)); y += r.height
sheet.save(out); print('对比图', out)
PY
