#!/bin/bash
# 用 Codex 命令行（ChatGPT.app 自带，内置 image_gen，用的是 Plus 账号的出图额度）按 jobs_v2.json 一张张画（10-26）。
# 第 5 关剧情图（美术/重画/story_s5.jpg）当画风参考附上。画好的放 美术/重画/codex/<id>.png，已有的跳过；额度用完（429）就停。
# 用法：bash 三国志/工具/画图/codex_draw.sh [id ...]
C="/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"; OUT="$ROOT/美术/重画/codex"; mkdir -p "$OUT/log"
REF="$ROOT/美术/重画/画风参考_雷劈.jpg"
IDS=("$@"); [ ${#IDS[@]} -eq 0 ] && IDS=($(python3 -c 'import json,sys;print(" ".join(x["id"] for x in json.load(open(sys.argv[1]))))' "$HERE/jobs_v2.json"))   # 路径里有 andrew's 的撇号：一律走 argv，别拼进 python 字符串
for id in "${IDS[@]}"; do
  [ -f "$OUT/$id.png" ] && continue
  P=$(python3 -c 'import json,sys;print(next(x["prompt"] for x in json.load(open(sys.argv[1])) if x["id"]==sys.argv[2]))' "$HERE/jobs_v2.json" "$id")
  [ -z "$P" ] && { echo "读不到 $id 的 prompt，停"; exit 1; }
  printf "%s" "用内置 image_gen 工具画一张图（只画这一张，不要写代码）。画完把图片文件复制到 $OUT/$id.png 然后结束。附图是画风参考。
$P" | (cd "$OUT" && "$C" exec --skip-git-repo-check -s workspace-write -i "$REF" $([[ $id == *zoujing* ]] && echo -i "$ROOT/美术/重画/邹靖造型参考.webp") - > "log/$id.txt" 2>&1)
  if [ -f "$OUT/$id.png" ]; then echo "ok $id"; elif grep -q "429\|usage_limit" "$OUT/log/$id.txt"; then echo "额度用完，停在 $id"; exit 1; else echo "没画出 $id（看 log/$id.txt）"; fi
done
