#!/usr/bin/env bash
# Снимок Timeshift перед установкой/обновлением пакетов.
# Не чаще раза в час; снимки помечены как «ежедневные», поэтому Timeshift сам удаляет старые.
conf=/etc/timeshift/timeshift.json
[ -f "$conf" ] || exit 0
grep -q '"btrfs_mode" : "true"' "$conf" || exit 0
command -v timeshift >/dev/null || exit 0
[ -d /run/systemd/system ] || exit 0          # не в chroot и не в установщике

stamp=/var/lib/aisktagos/last-apt-snapshot
mkdir -p /var/lib/aisktagos
if [ -f "$stamp" ] && [ $(( $(date +%s) - $(stat -c %Y "$stamp") )) -lt 3600 ]; then
    exit 0
fi
touch "$stamp"
echo "AIsktagOS: создаю снимок системы перед изменением пакетов…"
timeout 180 timeshift --create --scripted --tags D --comments "Перед обновлением пакетов" >/dev/null 2>&1 || true
exit 0
