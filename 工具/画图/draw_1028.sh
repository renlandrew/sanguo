#!/bin/bash
# 10-28 剧情改成「怕死、只敢守城、碰巧赢」后补画的两张：第 2 关（关羽闭眼乱抡、指天喊别过来）、第 5 关（张飞摔下城、抱盾惊叫）。
# 提示词在 jobs_1028.json。用 codex_draw.sh 画（ChatGPT.app 自带的 Codex，Plus 额度），画好缩成 720 宽 jpg 换进 原型/img/，旧图备份到 美术/重画/旧/。
# 用法：bash 三国志/工具/画图/draw_1028.sh [story_s2 story_s5]（不给就两张都画；想重画某张，先删掉 美术/重画/codex/1028/<键>.png）
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
OUT="$ROOT/美术/重画/codex/1028" JOBS="$HERE/jobs_1028.json" bash "$HERE/codex_draw.sh" "$@" || true
for k in ${@:-story_s2 story_s5}; do
  png="$ROOT/美术/重画/codex/1028/$k.png"; [ -f "$png" ] || { echo "没有 $k 的新图，跳过"; continue; }
  old="$ROOT/美术/重画/旧/${k}_旧1028.jpg"; [ -f "$old" ] || cp "$ROOT/原型/img/$k.jpg" "$old"
  sips -s format jpeg -s formatOptions 85 --resampleWidth 720 "$png" --out "$ROOT/原型/img/$k.jpg" >/dev/null && cp "$png" "$ROOT/美术/重画/codex/$k.png" && echo "换好 $k（旧图在 美术/重画/旧/${k}_旧1028.jpg）"
done
