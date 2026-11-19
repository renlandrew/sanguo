#!/bin/bash
# 11-18 第三章：立绘之外的一串（兵器、图标、官阶头像、底图、地图），一个接一个画；额度用完就停
cd "$(dirname "$0")/../.."
JOBS=jobs_ch3_wpn.json OUT=美术/第三章/兵器 bash 工具/画图/draw_ch3.sh || exit 1
JOBS=jobs_ch3_icon.json OUT=美术/第三章/图标 bash 工具/画图/draw_ch3.sh || exit 1
for h in guan zhang liu; do for r in 10 11 12; do JOBS=jobs_ch3_rank.json OUT=美术/第三章/官阶 bash 工具/画图/draw_ch3.sh rank_${h}_$r || exit 1; done; done
JOBS=jobs_ch3_bg.json OUT=美术/第三章/底图 bash 工具/画图/draw_ch3.sh || exit 1
JOBS=jobs_ch3_map.json OUT=美术/第三章/地图 bash 工具/画图/draw_ch3.sh || exit 1
