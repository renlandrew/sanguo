#!/bin/zsh
# 看网页试玩版的漏斗（11-09）：zsh 三国志/工具/试玩漏斗.sh [--src 标签] [--lang zh|en] [--days 30]
ssh -o BatchMode=yes BridgeEDU "sudo -n -u sanguo /usr/bin/python3 /opt/sanguo-save/sanguo_save.py funnel --state /var/lib/sanguo-save $*"
