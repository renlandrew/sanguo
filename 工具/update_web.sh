#!/bin/zsh
# 从 GitHub 拉最新、传到 jieyunqiudao.com/sanguo、再把本机提交推回 GitHub（10-28 用户：「给我一个命令，以后我自己拉下来更新网页」）
set -e
cd "${0:A:h}/.."
git pull --rebase
zsh 工具/deploy_web.sh
git push
echo "完成：https://jieyunqiudao.com/sanguo/"
