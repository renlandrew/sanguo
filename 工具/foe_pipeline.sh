#!/bin/bash
# 一个兵种从三视图到带动作的 glb（10-24）：切图 → Meshy 多图建模 → 绑骨 → 套动作。约 50 点。
# 用法：MESHY_KEY=… 工具/foe_pipeline.sh <兵种目录（里面有 三视图.jpg）> <身高米> <动作号,逗号分开>
set -e
D="$1"; HT="$2"; ACTS="$3"; HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/split_turn.py" "$D/三视图.jpg" "$D"
T=$(python3 "$HERE/meshy.py" multi "$D/正面.png" "$D/侧面.png" "$D/背面.png"); echo "建模 $T"
python3 "$HERE/meshy.py" wait multi-image-to-3d "$T" "$D/模型" | tail -3
R=$(python3 "$HERE/meshy.py" rig "$T" "$HT"); echo "绑骨 $R"
python3 "$HERE/meshy.py" wait rigging "$R" "$D/绑骨" | tail -1
A=$(python3 "$HERE/meshy.py" anims "$R" "$ACTS"); echo "动作 $A"
python3 "$HERE/meshy.py" wait animations "$A" "$D/动作" | tail -3
