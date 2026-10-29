#!/bin/bash
# 从已使用的 Meshy 奔跑动作渲染背面；正面和战斗数值不变。
set -euo pipefail
cd "$(dirname "$0")/.."
B=/Applications/Blender.app/Contents/MacOS/Blender
SP="${SP:-$(mktemp -d)}"
mkdir -p "$SP"
back() {
  local cn=$1 key=$2 action=$3 height=$4 scale=$5 weapon=$6 carry=$7 color=$8 shield=$9
  local raw="$SP/${key}_raw" col="$SP/${key}_col" model="美术/$cn/v2/动作/animation_glb_url.glb"
  [ -f "$model" ] || { echo "缺模型 $model" >&2; return 1; }
  "$B" -b -t "${THREADS:-6}" -P 工具/blender/render_frames.py -- "$model" "$raw" n=8 size=512 light=lit key=2.8 rim=4 amb=.05 "scale=$scale" "wpn=$weapon" ax=x "shield=$shield" "only=$action" "yaw={\"$action\":180}" "carry={\"$action\":$carry}" > "$SP/${key}.log" 2>&1
  python3 工具/blender/ink_post.py "$raw" "$col" keep=1 vivid=1.05 $color
  python3 工具/pack_sprites.py "$col" "原型/img/${key}_back" "h=$height" "scale=$scale" "$action=run"
}
back 黄巾兵 huangjin Run_02 1.62 2.8 spear '[-0.3,0.2,1]' '' 0
back 黄巾兵 yayi Run_02 1.62 2.8 club '[0.45,-0.15,1]' 'band=ink retint=1' 0
back 黄巾力士 lishi Run_02 1.95 3.4 club '[0.45,-0.15,1]' 'band=red retint=1' 0
back 黄巾弓手 gong RunFast 1.68 2.9 bow '[0,0,1]' '' 0
back 黄巾术士 shushi RunFast 1.75 2.9 none '[0,0,1]' '' 0
back 程远志 cyz Walk_Fight_Forward 1.95 3.6 blade '[0,0,1]' '' 0
back 程远志 dengmao Walk_Fight_Forward 1.95 3.6 spear '[-0.2,0.5,1]' 'band=red retint=1' 0
back 西凉兵 xiliang Run_02 1.75 2.9 saber '[-0.3,0.2,1]' '' 1
back 飞熊军 feixiong Run_02 2.0 3.6 axe '[-0.35,-0.2,1]' '' 0
back 陷阵营 xianzhen Run_02 1.8 3.0 spear '[-0.3,-0.25,1]' '' 0
back 百姓 baixing RunFast 1.65 2.5 none '[0,0,1]' '' 0
