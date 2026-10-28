#!/bin/bash
# 10-28 伏兵的两张图（用户：「这个用gpt image，不要这些html」）：令旗按钮 ui_ambush_btn、草丛里的乡勇 ui_ambush_hide。
# 用 codex_draw.sh 画（ChatGPT 自带 image_gen），提示词直接要透明背景；画出来已经透明就只裁边缩放（sips），万一不透明才用 matte_ui.py 抠。存 原型/img/。
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"; OUT="$ROOT/美术/重画/codex/ambush"
OUT="$OUT" JOBS="$HERE/jobs_ambush.json" bash "$HERE/codex_draw.sh" || true
for k in ui_ambush_btn:160 ui_ambush_hide:200; do n=${k%%:*}; w=${k##*:}; f="$OUT/$n.png"; [ -f "$f" ] || { echo "没有 $n"; continue; }
  if [ "$(sips -g hasAlpha "$f" | awk '/hasAlpha/{print $2}')" = "yes" ]; then sips --resampleWidth $w "$f" --out "$ROOT/原型/img/$n.png" >/dev/null && echo "装好 $n（原本就透明）"
  else python3 "$ROOT/工具/matte_ui.py" "$f" $w $n && echo "装好 $n（抠了底）"; fi; done
