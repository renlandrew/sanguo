#!/bin/bash
# 11-12 讨伐（打不死的怪物，90 秒比伤害）：用 Codex 命令行（ChatGPT.app 自带 image_gen，Plus 额度）画怪物三档形态。
# 先画第一档，后两档附第一档当造型参考。透明底 PNG，放 美术/讨伐/<名>/form<N>.png，已有的跳过。
# 用法：bash 三国志/工具/画图/draw_hunt.sh
C="/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"; OUT="$ROOT/美术/讨伐/黄巾力士"; mkdir -p "$OUT/log"
REF="$ROOT/美术/华雄/正面.png"
COMMON="游戏敌方单位立绘，三国题材手绘厚涂风格（画风照附图的敌将立绘）。正面全身，站姿，脚在画面底部，人物占满画面高度，居中，只画这一个角色。背景必须完全透明（PNG 透明通道），不要地面、不要影子、不要文字、不要边框。竖图。"
draw() { # id 提示词 [追加参考图]
  local id="$1" p="$2" ref2="$3"
  [ -f "$OUT/$id.png" ] && { echo "have $id"; return; }
  printf "%s" "用内置 image_gen 工具画一张图（只画这一张，不要写代码处理图片）。画完把图片文件复制到 $OUT/$id.png 然后结束。第一张附图是画风参考${ref2:+，第二张附图是同一个角色的上一个形态，体型、脸、头巾、装束要认得出是同一个}。
$COMMON
$p" | (cd "$OUT" && "$C" exec --skip-git-repo-check -s workspace-write -i "$REF" ${ref2:+-i "$ref2"} - > "log/$id.txt" 2>&1)
  if [ -f "$OUT/$id.png" ]; then echo "ok $id"; elif grep -q "429\|usage_limit" "$OUT/log/$id.txt"; then echo "额度用完，停在 $id"; exit 1; else echo "没画出 $id（看 log/$id.txt）"; fi
}
draw form1 "角色：黄巾力士——张角用符水召出来的巨人。比常人高大一倍，肩宽背厚、筋肉虬结，赤着上身，皮肤土黄发灰像泥塑；头裹黄巾，脸宽鼻阔、怒目；腰系黄布和粗麻绳，赤脚。胸口、双臂、额头贴着十几张黄纸朱砂符，符纸完整。双手握拳垂在身侧，神情木然。"
draw form2 "角色：黄巾力士的第二形态（被打怒了）。和上一形态同一个巨人，但身上的黄符烧掉了一半，残符边缘带火星；皮肤上裂出一道道发红光的纹路，像烧红的陶；双眼发出橙红的光，咬牙怒吼，双拳举到胸前。" "$OUT/form1.png"
draw form3 "角色：黄巾力士的第三形态（狂暴）。和前面同一个巨人，身上的符纸全部烧尽，只剩几片飘着的灰烬；全身裂纹透出金红色的火光，肩背上腾起金色火焰，头巾在火里翻飞；双眼白炽，仰头咆哮，双拳高举过头要砸下来。体型比前一形态更魁梧。" "$OUT/form1.png"
