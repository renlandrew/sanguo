#!/bin/bash
# 10-26 新模型（美术/<兵种>/v2/动作）→ 渲染 → 全彩 → 打包进 原型/img/<键>
# 10-28 改成 Eevee 真光照（light=lit key=2.8 rim=4 amb=.05，对比图 C）+ 512 大图（用户：「很模糊」「像纸片」）；调色 vivid 1.25→1.05（真光照本身够鲜）
cd "$(dirname "$0")/.."; SP="${SP:-$(mktemp -d)}"
B=/Applications/Blender.app/Contents/MacOS/Blender
r() { cn=$1; key=$2; opts=$3; col=$4; pack=$5; g="美术/$cn/v2/动作/animation_glb_url.glb"; [ -f "美术/$cn/v2/动作/done" ] || { echo "skip $key (模型没好)"; return; }
  [ -f "$SP/v2_$key.done" ] && return; rm -rf "$SP/v2_${key}_raw" "$SP/v2_${key}_col"
  eval "$B -b -P 工具/blender/render_frames.py -- \"$g\" \"$SP/v2_${key}_raw\" n=8 size=512 light=lit key=2.8 rim=4 amb=.05 $opts" 2>&1 | grep -E "渲完|rror"
  python3 工具/blender/ink_post.py "$SP/v2_${key}_raw" "$SP/v2_${key}_col" keep=1 vivid=1.05 $col | tail -1
  python3 工具/pack_sprites.py "$SP/v2_${key}_col" 原型/img/$key $pack | tail -1 && touch "$SP/v2_$key.done"; }
r 黄巾兵 huangjin "wpn=spear ax=x 'carry={\"Run_02\": [0.3, -0.2, 1], \"Thrust_Slash\": [0.15, -0.9, 0.35], \"Hit_Reaction\": [0.3, -0.2, 1]}' scale=2.8" "" "h=1.62 scale=2.8 Run_02=run Thrust_Slash=ram BeHit_FlyUp=fly Shot_and_Fall_Backward=die Hit_Reaction=hit"
r 黄巾兵 yayi "wpn=club ax=x 'carry={\"Run_02\": [-0.45, 0.15, 1]}' scale=2.8" "band=ink retint=1" "h=1.62 scale=2.8 Run_02=run Thrust_Slash=ram BeHit_FlyUp=fly Shot_and_Fall_Backward=die Hit_Reaction=hit"
r 黄巾力士 lishi "wpn=club ax=x 'carry={\"Run_02\": [-0.45, 0.15, 1]}' scale=3.4" "band=red retint=1" "h=1.95 scale=3.4 Run_02=run Heavy_Hammer_Swing=ram BeHit_FlyUp=fly Knock_Down=die Hit_Reaction=hit"
r 黄巾弓手 gong "wpn=bow ax=z 'yaw={\"Archery_Shot\": -60}' scale=2.9" "" "h=1.68 scale=2.9 RunFast=run Archery_Shot=shoot BeHit_FlyUp=fly Shot_and_Fall_Backward=die Hit_Reaction=hit"
r 黄巾术士 shushi "wpn=none scale=2.9" "" "h=1.75 scale=2.9 RunFast=run Charged_Spell_Cast=ram BeHit_FlyUp=fly Shot_and_Fall_Backward=die Hit_Reaction=hit"
r 程远志 cyz "wpn=blade ax=x scale=3.6" "" "h=1.95 scale=3.6 Walk_Fight_Forward=run Double_Combo_Attack=ram BeHit_FlyUp=fly dying_backwards=die Hit_Reaction=hit"
r 程远志 dengmao "wpn=spear ax=z 'carry={\"Walk_Fight_Forward\": [0.2, -0.5, 1]}' scale=3.6" "band=red retint=1" "h=1.95 scale=3.6 Walk_Fight_Forward=run Double_Combo_Attack=ram BeHit_FlyUp=fly dying_backwards=die Hit_Reaction=hit"
r 西凉兵 xiliang "wpn=saber ax=x shield=1 'carry={\"Run_02\": [0.3, -0.2, 1]}' scale=2.9" "" "h=1.75 scale=2.9 Run_02=run Right_Hand_Sword_Slash=ram BeHit_FlyUp=fly Shot_and_Fall_Backward=die Hit_Reaction=hit"
r 飞熊军 feixiong "wpn=axe ax=x 'carry={\"Run_02\": [0.35, 0.2, 1]}' scale=3.6" "" "h=2.0 scale=3.6 Run_02=run Charged_Axe_Chop=ram BeHit_FlyUp=fly Knock_Down=die Hit_Reaction=hit"
r 陷阵营 xianzhen "wpn=spear ax=x 'carry={\"Run_02\": [0.3, 0.25, 1], \"Thrust_Slash\": [0.15, -0.9, 0.35]}' scale=3.0" "" "h=1.8 scale=3.0 Run_02=run Thrust_Slash=ram BeHit_FlyUp=fly Shot_and_Fall_Backward=die Hit_Reaction=hit"
r 百姓 baixing "wpn=none scale=2.5" "" "h=1.65 scale=2.5 RunFast=run RunFast=ram BeHit_FlyUp=fly Shot_and_Fall_Backward=die Hit_Reaction=hit"
echo render pass done
