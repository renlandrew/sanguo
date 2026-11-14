#!/bin/bash
# 11-14 水墨版重画的清单（按重要性排）：战场底图 → 战役地图 → 主页/剧情大图 → 敌将立绘 → 头像 → 物品 → 卡面 → 怪物立绘
# 动作图集（g_*、各兵种 webp、side_*、monv_*、fx_*、fb/、ui_* 九宫格）是逐帧动画或界面部件，不在这里重画
cd "$(dirname "$0")/../.."
ls 原型/img/bg_*.jpg 原型/img/bg.jpg 2>/dev/null
ls 原型/img/map_*.jpg 2>/dev/null
ls 原型/img/pt_*.png 2>/dev/null
ls 原型/img/p_*.jpg 2>/dev/null
ls 原型/img/item_*.jpg 原型/img/item_*.png 2>/dev/null
ls 原型/img/card_*.jpg 2>/dev/null
ls 原型/img/mon_juling1.webp 原型/img/mon_shanjun1.webp 原型/img/mon_jiao1.webp 2>/dev/null
ls 原型/img/story_*.jpg 2>/dev/null
