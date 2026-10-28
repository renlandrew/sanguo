#!/bin/bash
# 10-28 伏兵的两张图（用户：「这个用gpt image，不要这些html」）：令旗按钮 ui_ambush_btn、草丛里的乡勇 ui_ambush_hide。
# 用 codex_draw.sh 画（ChatGPT 自带 image_gen），中灰底，再用 matte_ui.py 抠透明，存 原型/img/。游戏里有图就用图，没图不画。
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"; OUT="$ROOT/美术/重画/codex/ambush"
OUT="$OUT" JOBS="$HERE/jobs_ambush.json" bash "$HERE/codex_draw.sh" || true
for k in ui_ambush_btn:160 ui_ambush_hide:200; do n=${k%%:*}; w=${k##*:}; [ -f "$OUT/$n.png" ] && python3 "$ROOT/工具/matte_ui.py" "$OUT/$n.png" $w $n && echo "装好 $n"; done
