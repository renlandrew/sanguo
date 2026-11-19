#!/bin/bash
# 11-18 第三章画图（用户：「需要画画和veo就自己调」）：Codex 命令行（ChatGPT.app 自带 image_gen，Plus 额度，不另花钱）按 jobs 一张张画。
# 每个 job 可带 ref（原型/img 下的文件名，或 ROOT 起的相对路径）当画风参考；画好的放 OUT/<id>.png，已有的跳过；额度用完（429）就停。
# 用法：JOBS=jobs_ch3_pt.json OUT=美术/第三章/立绘 bash 三国志/工具/画图/draw_ch3.sh [id ...]
C="/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
JOBS="$HERE/${JOBS:-jobs_ch3_pt.json}"; OUT="$ROOT/${OUT:-美术/第三章/立绘}"; mkdir -p "$OUT/log"
IDS=("$@"); [ ${#IDS[@]} -eq 0 ] && IDS=($(python3 -c 'import json,sys;print(" ".join(x["id"] for x in json.load(open(sys.argv[1]))))' "$JOBS"))
for id in "${IDS[@]}"; do
  [ -f "$OUT/$id.png" ] && { echo "have $id"; continue; }
  P=$(python3 -c 'import json,sys;print(next(x["prompt"] for x in json.load(open(sys.argv[1])) if x["id"]==sys.argv[2]))' "$JOBS" "$id")
  REFS=$(python3 -c 'import json,sys;j=next(x for x in json.load(open(sys.argv[1])) if x["id"]==sys.argv[2]);r=j.get("ref");print("\n".join(r if isinstance(r,list) else [r] if r else []))' "$JOBS" "$id")
  ARGS=(); while IFS= read -r r; do [ -z "$r" ] && continue; if [ -f "$ROOT/原型/img/$r" ]; then ARGS+=(-i "$ROOT/原型/img/$r"); elif [ -f "$ROOT/$r" ]; then ARGS+=(-i "$ROOT/$r"); fi; done <<< "$REFS"
  printf "%s" "用内置 image_gen 工具画一张图（只画这一张，不要写代码）。画完把图片文件复制到 $OUT/$id.png 然后结束。附图是参考。
$P" | (cd "$OUT" && "$C" exec --skip-git-repo-check -s workspace-write "${ARGS[@]}" - > "log/$id.txt" 2>&1)
  if [ -f "$OUT/$id.png" ]; then echo "ok $id"; elif grep -q "429\|usage_limit" "$OUT/log/$id.txt"; then echo "额度用完，停在 $id"; exit 1; else echo "没画出 $id（看 log/$id.txt）"; fi
done
