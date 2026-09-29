#!/usr/bin/env bash
# AIsktagOS: финальная настройка после установки. Запускается установщиком внутри новой системы.
set -u
export DEBIAN_FRONTEND=noninteractive

log() { echo "[aisktagos-post] $*"; }

# 1. Убрать остатки live-системы
apt-get -y autoremove --purge || true
rm -f /etc/casper.conf /etc/xdg/autostart/aisktagos-live.desktop /usr/share/applications/aisktagos-install.desktop

# 2. Корневая ФС из fstab (внутри установщика findmnt видит не ту систему)
read -r root_spec root_type < <(awk '$1 !~ /^#/ && $2 == "/" { print $1, $3; exit }' /etc/fstab)
root_uuid="${root_spec#UUID=}"
log "корень: $root_spec ($root_type)"

# 3. Timeshift: ежедневные снимки Btrfs (откат системы как в Linux Mint)
if [ "$root_type" = "btrfs" ] && [ -n "$root_uuid" ]; then
    mkdir -p /etc/timeshift
    cat > /etc/timeshift/timeshift.json <<EOF
{
  "backup_device_uuid" : "$root_uuid",
  "parent_device_uuid" : "",
  "do_first_run" : "false",
  "btrfs_mode" : "true",
  "include_btrfs_home_for_backup" : "false",
  "include_btrfs_home_for_restore" : "false",
  "stop_cron_emails" : "true",
  "schedule_monthly" : "false",
  "schedule_weekly" : "true",
  "schedule_daily" : "true",
  "schedule_hourly" : "false",
  "schedule_boot" : "false",
  "count_monthly" : "2",
  "count_weekly" : "3",
  "count_daily" : "7",
  "count_hourly" : "6",
  "count_boot" : "5",
  "date_format" : "%Y-%m-%d %H:%M:%S",
  "exclude" : [],
  "exclude-apps" : []
}
EOF
    log "Timeshift настроен"
fi

# 4. BIOS: запомнить диск для обновлений GRUB (иначе apt спросит при обновлении grub-pc)
if [ ! -d /sys/firmware/efi ] && dpkg -s grub-pc >/dev/null 2>&1; then
    part="$(blkid -U "$root_uuid" 2>/dev/null || true)"
    disk="$(lsblk -no pkname "$part" 2>/dev/null | head -1)"
    if [ -n "$disk" ]; then
        byid="$(find /dev/disk/by-id -lname "*/$disk" 2>/dev/null | grep -v -e '-part' -e 'wwn-' | head -1)"
        echo "grub-pc grub-pc/install_devices multiselect ${byid:-/dev/$disk}" | debconf-set-selections
        log "grub-pc: ${byid:-/dev/$disk}"
    fi
fi

# 5. Приветствие при первом входе нового пользователя
for home in /home/*; do
    [ -d "$home" ] || continue
    rm -f "$home/.config/aisktagos/welcome-done"
done

exit 0
