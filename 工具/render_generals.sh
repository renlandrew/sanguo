#!/bin/bash
# 城头三位武将：每人四段动作从背后渲（立体光、512 像素、披风布料），着色（留八成原色、粗墨线、纸色光晕），打图集进原型（10-24）。
# 用法：工具/render_generals.sh <临时目录> [guan zhang liu]
set -e
TMP="$1"; shift; WHO="${@:-guan zhang liu}"; HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$HERE/.."; B=/Applications/Blender.app/Contents/MacOS/Blender
for g in $WHO; do
  case $g in
    guan)  GLB=美术/关羽/动作/animation_glb_url.glb; ACTS="Combat_Stance Right_Hand_Sword_Slash Charged_Slash Hit_Reaction"; ARGS="wpn=glaive ax=x cape=0.11,0.30,0.22 edge=0.55,0.42,0.15 scale=4.4"; CARRY='{"Combat_Stance": [0.18, 0.12, 1]}'; H=1.79; SC=4.4; KEYS="Combat_Stance=idle Right_Hand_Sword_Slash=atk Charged_Slash=skill Hit_Reaction=hit";;
    zhang) GLB=美术/张飞/动作/animation_glb_url.glb; ACTS="Combat_Stance Thrust_Slash Shouting_Angrily Hit_Reaction"; ARGS="wpn=snake ax=x cape=0.07,0.06,0.06 edge=0.62,0.1,0.07 scale=4.6"; CARRY='{"Combat_Stance": [0.18, 0.12, 1]}'; H=1.75; SC=4.6; KEYS="Combat_Stance=idle Thrust_Slash=atk Shouting_Angrily=skill Hit_Reaction=hit";;
    liu)   GLB=美术/刘备/动作/animation_glb_url.glb; ACTS="Combat_Stance Right_Hand_Sword_Slash Double_Blade_Spin Hit_Reaction"; ARGS="wpn=twin ax=x lax=-x cape=0.9,0.88,0.82 edge=0.24,0.43,0.53 scale=3.8"; CARRY='{"Combat_Stance": [0.55, -0.2, -1]}'; H=1.7; SC=3.8; KEYS="Combat_Stance=idle Right_Hand_Sword_Slash=atk Double_Blade_Spin=skill Hit_Reaction=hit";;
  esac
  rm -rf "${TMP:?}/${g}_raw" "${TMP:?}/${g}_ink"
  for a in $ACTS; do (cd "$ROOT" && $B -b -P 工具/blender/render_general.py -- $GLB "$TMP/${g}_raw" act=$a $ARGS n=8 size=512 light=studio "carry=$CARRY" 2>&1 | grep -E "渲完|rror"); done
  python3 "$HERE/blender/ink_post.py" "$TMP/${g}_raw" "$TMP/${g}_ink" keep=0.8 line=5 halo=5
  (cd "$ROOT" && python3 工具/pack_sprites.py "$TMP/${g}_ink" 原型/img/g_$g h=$H scale=$SC $KEYS)
done
