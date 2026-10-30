#!/bin/zsh
# 三国志云存档上 EC2 BridgeEDU（10-30 用户：「不是接了ec2吗，你做一个数据库啊，如同劫云」「服务器跑在ec2 比较好吧？」）
# 照劫云 jieyun-save 的样子另起一个：/opt/sanguo-save、用户 sanguo、库在 /var/lib/sanguo-save、本机 127.0.0.1:8094；
# nginx 在 jieyunqiudao.com 那个 server 里加 location /sanguo/api/（改前备份），劫云的 /api/、8093、法语站、pixta 不动。
# 用法：zsh 三国志/server/deploy_save.sh   （再跑一遍只更新代码并重启）
set -e
cd "${0:A:h}"
SSH=(ssh -o BatchMode=yes BridgeEDU)
python3 test_save.py >/dev/null
"${SSH[@]}" "sudo -n mkdir -p /opt/sanguo-save"
rsync -az --rsync-path="sudo -n rsync" -e "ssh -o BatchMode=yes" sanguo_save.py BridgeEDU:/opt/sanguo-save/
"${SSH[@]}" 'sudo -n bash -s' <<'REMOTE'
set -e
id sanguo >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin sanguo
mkdir -p /var/lib/sanguo-save /var/backups/sanguo-save
chown sanguo:sanguo /var/lib/sanguo-save /var/backups/sanguo-save; chmod 750 /var/lib/sanguo-save
chown -R root:root /opt/sanguo-save; chmod 755 /opt/sanguo-save; chmod 644 /opt/sanguo-save/sanguo_save.py
cat > /etc/systemd/system/sanguo-save.service <<'UNIT'
# 三国志守关 · 云存档（匿名凭证 + 存档码 + 数值合理性检查），源码在本机 三国志/server/sanguo_save.py。nginx 把 jieyunqiudao.com/sanguo/api/ 转到这里。10-30。
[Unit]
Description=Sanguo save service
After=network.target

[Service]
User=sanguo
Group=sanguo
ExecStart=/usr/bin/python3 /opt/sanguo-save/sanguo_save.py serve --host 127.0.0.1 --port 8094 --state /var/lib/sanguo-save
Restart=always
RestartSec=3
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/var/lib/sanguo-save

[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/cron.d/sanguo-save <<'CRON'
# 三国志存档每天备份（单个 .sqlite 文件），留 14 份
10 4 * * * sanguo /usr/bin/python3 /opt/sanguo-save/sanguo_save.py backup --state /var/lib/sanguo-save --to /var/backups/sanguo-save --keep 14 >> /var/lib/sanguo-save/backup.log 2>&1
CRON
systemctl daemon-reload; systemctl enable --now sanguo-save; systemctl restart sanguo-save
CONF=/etc/nginx/sites-available/jieyunqiudao.com
if ! grep -q 'location /sanguo/api/' $CONF; then
  cp -a $CONF /root/jieyunqiudao.com.bak-$(date +%Y%m%d%H%M%S)
  python3 - $CONF <<'PY'
import sys; p = sys.argv[1]; s = open(p).read()
block = '''    # 三国志云存档（10-30）：转到本机 sanguo-save 服务（前缀比 /sanguo/ 长，nginx 先匹配它）
    location /sanguo/api/ {
        proxy_pass http://127.0.0.1:8094/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 256k;
    }
'''
anchor = '    location = /sanguo { return 301 /sanguo/; }\n'
assert s.count(anchor) == 1; open(p, 'w').write(s.replace(anchor, block + anchor))
PY
  nginx -t && systemctl reload nginx
fi
sleep 1; systemctl is-active sanguo-save jieyun-save
REMOTE
curl -s https://jieyunqiudao.com/sanguo/api/ping; echo
curl -s -o /dev/null -w "劫云 /api/ping %{http_code}\n" https://jieyunqiudao.com/api/ping
