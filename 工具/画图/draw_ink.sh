#!/bin/bash
# 11-14 用户：「打开gpt，把所有图都水墨画一次，先备着」——把现有美术逐张重画成水墨版，存 美术/水墨版/，不动 原型/img。
# 用 Codex 命令行（ChatGPT.app 自带 image_gen，Plus 额度，不另花钱），原图当参考图附进去。已有的跳过；额度用完就停（下次接着跑）。
# 用法：bash 三国志/工具/画图/draw_ink.sh <图…>    例：bash 工具/画图/draw_ink.sh 原型/img/bg_*.jpg
C="/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"; OUT="$ROOT/美术/水墨版"; mkdir -p "$OUT/log"
STYLE="画风：中国水墨画。生宣纸的米白底色和纸纹，墨色由浓到淡的层次，笔锋看得出提按和飞白，大块留白；颜色只用很淡的赭石、花青、藤黄做淡彩渲染，不要鲜艳饱和的颜色，不要厚涂、不要油画感、不要赛璐珞描线、不要 3D 渲染感。远处用淡墨虚化，近处墨色重、笔触实。
要求：保持附图的题材、构图、主体位置和画面比例不变，只换成水墨画法；人物的身份、服饰样式、兵器、姿态都要认得出是同一个。不要添字、不要印章、不要落款、不要边框、不要水印。"
for f in "$@"; do
  b=$(basename "$f"); id="${b%.*}"
  [ -f "$OUT/$id.png" ] && { echo "have $id"; continue; }
  printf "%s" "用内置 image_gen 工具画一张图（只画这一张，不要写代码处理图片）。画完把图片文件复制到 $OUT/$id.png 然后结束。
附图是一张游戏美术，请把它重画成水墨版。
$STYLE" | (cd "$OUT" && "$C" exec --skip-git-repo-check -s workspace-write -i "$ROOT/$f" - > "log/$id.txt" 2>&1)
  if [ -f "$OUT/$id.png" ]; then echo "ok $id"; elif grep -q "429\|usage limit\|usage_limit" "$OUT/log/$id.txt"; then echo "额度用完，停在 $id"; exit 1; else echo "没画出 $id（看 log/$id.txt）"; fi
done
echo DONE
