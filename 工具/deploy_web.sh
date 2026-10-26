#!/bin/zsh
# 三国志守关原型上网（10-26 用户：「做到jieyunqiudao.com/sanguo」）：把 原型/ 同步到 EC2 BridgeEDU 的 /var/www/sanguo/，链接 https://jieyunqiudao.com/sanguo/。
# 单独一个目录：劫云的 修仙/网页/deploy.sh 对 /var/www/jieyun/ 带 --delete，放进去会被它删掉。nginx 在 jieyunqiudao.com 那个 server 里加了 location /sanguo/（alias），同机法语站、pixta 不动。
# 存档在玩家浏览器 localStorage（sgz.proto.*），和劫云的 jywd-web: 不冲突；没有云存档。
# 用法：zsh 三国志/工具/deploy_web.sh
set -e
cd "${0:A:h}/../原型"
SSH=(ssh -o BatchMode=yes)
RS=(rsync -az --rsync-path="sudo -n rsync" -e "${SSH[*]}")
"${SSH[@]}" BridgeEDU 'sudo -n mkdir -p /var/www/sanguo'
# 先传图、音乐、脚本，最后换页面，再删旧文件——上传中途有人打开，拿到的还是一套完整的旧版
"${RS[@]}" --exclude .DS_Store img music 墨流.js BridgeEDU:/var/www/sanguo/
"${RS[@]}" 守关.html BridgeEDU:/var/www/sanguo/index.html
"${RS[@]}" 守关.html BridgeEDU:/var/www/sanguo/
"${RS[@]}" --delete --exclude .DS_Store --exclude index.html --exclude 动作.html --exclude 墨流试样.html ./ BridgeEDU:/var/www/sanguo/
"${SSH[@]}" BridgeEDU 'sudo -n rm -f /var/www/sanguo/动作.html /var/www/sanguo/墨流试样.html; sudo -n chown -R root:root /var/www/sanguo && sudo -n chmod -R u=rwX,go=rX /var/www/sanguo && du -sh /var/www/sanguo'
curl -s -o /dev/null -w "线上 /sanguo/ %{http_code}\n" https://jieyunqiudao.com/sanguo/
