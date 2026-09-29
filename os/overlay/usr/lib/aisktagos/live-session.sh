#!/usr/bin/env bash
# Live-USB: значок «Установить AIsktagOS» на рабочем столе и автозапуск установщика,
# если в меню загрузки выбран пункт «Установить».
grep -qw 'boot=casper' /proc/cmdline || exit 0

desk="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
mkdir -p "$desk"
install -m 0755 /usr/share/applications/aisktagos-install.desktop "$desk/aisktagos-install.desktop"

flag="${XDG_RUNTIME_DIR:-/tmp}/aisktagos-installer-started"
if grep -qw 'aisktagos.install' /proc/cmdline && [ ! -e "$flag" ]; then
    touch "$flag"
    sleep 4   # дать рабочему столу догрузиться
    exec /usr/bin/aisktag-install
fi
