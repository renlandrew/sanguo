#!/bin/bash
# 11-12 用户：「怪物的战斗动作呢」——讨伐三只怪物每个形态补两张姿势：a 蓄力、b 出手。附该形态的立绘当造型参考，大小、位置不变，游戏里攻击时切换。
# Codex 命令行出图（Plus 额度），透明底 PNG，放 美术/讨伐/<名>/form<N>_a.png、_b.png，已有的跳过。用法：bash 三国志/工具/画图/draw_hunt_act.sh
C="/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
draw() { # 目录 形态 a|b 姿势
  local OUT="$ROOT/美术/讨伐/$1" id="form$2_$3" ref="$ROOT/美术/讨伐/$1/form$2.png"
  [ -f "$ref" ] || { echo "缺 $1 form$2"; return; }
  [ -f "$OUT/$id.png" ] && { echo "have $1 $id"; return; }
  printf "%s" "用内置 image_gen 工具画一张图（只画这一张，不要写代码处理图片）。画完把图片文件复制到 $OUT/$id.png 然后结束。
附图是游戏里一只怪物的立绘。画同一只怪物的另一个战斗姿势：造型、配色、花纹、身上的火光或电光、画风、精细度和附图完全一样，认得出是同一只、同一个形态；画幅比例和附图一样，怪物在画面里的大小和附图一样，脚（或身子着地的地方）落在画面里同样的位置。正面朝向观众，只画这一只。背景必须完全透明（PNG 透明通道），不要地面、不要影子、不要文字、不要边框。
新姿势：$4" | (cd "$OUT" && "$C" exec --skip-git-repo-check -s workspace-write -i "$ref" - > "log/$id.txt" 2>&1)
  if [ -f "$OUT/$id.png" ]; then echo "ok $1 $id"; elif grep -q "429\|usage_limit" "$OUT/log/$id.txt"; then echo "额度用完，停在 $1 $id"; exit 1; else echo "没画出 $1 $id（看 log/$id.txt）"; fi
}
for n in 1 2 3; do
  draw 黄巾力士 $n a "蓄力——右拳高高举过头顶，左臂护在胸前，上身向后仰、拧腰，咬牙瞪眼，准备往下砸。"
  draw 黄巾力士 $n b "出手——双拳并在一起狠狠砸向脚前的地面，上身前倾、屈膝下蹲，拳头落在画面下方正中，头低着向前冲。"
  draw 山君 $n a "蓄力——身子压得极低贴近地面，后腿弓起、臀部抬高，前爪扣地，头压低、双眼死死盯着前方，准备扑出去。"
  draw 山君 $n b "出手——腾空向观众扑来，两只前爪张开伸向前方、爪尖全露，血盆大口张开露出獠牙，后腿蹬直。"
  draw 蛟 $n a "蓄力——盘着的身子不变，头颈向后高高仰起，喉咙和下颌鼓胀发亮，嘴紧闭，准备喷吐。"
  draw 蛟 $n b "出手——盘着的身子不变，头颈向前向下猛探、冲着观众张开大嘴，嘴里喷出一道粗壮的青白色水柱直冲画面下方。"
done
