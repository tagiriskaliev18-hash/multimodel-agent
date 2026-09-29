#!/bin/sh
# AIsktagOS: запасной графический режим для любой видеокарты.
# Wayland (KWin) требует DRM-устройство /dev/dri/card*. Его нет при nomodeset, на очень
# старых/экзотических видеокартах и в некоторых виртуальных машинах. Тогда экран входа
# и сеанс Plasma запускаются в X11 (драйверы vesa/fbdev работают везде).
conf=/etc/sddm.conf.d/zz-aisktagos-display-fallback.conf

# Видеодрайвер может загрузиться чуть позже экрана входа — ждём до 5 секунд
i=0
while [ $i -lt 10 ]; do
    if ls /dev/dri/card* >/dev/null 2>&1; then
        rm -f "$conf"
        exit 0
    fi
    sleep 0.5
    i=$((i + 1))
done

echo "AIsktagOS: нет DRM-устройства, экран входа и Plasma запускаются в X11"
cat > "$conf" <<'EOF'
# Создано автоматически /usr/lib/aisktagos/display-fallback.sh: DRM-устройство не найдено
[General]
DisplayServer=x11
EOF
# Автовход live-сессии (casper) — тоже в X11
if [ -f /etc/sddm.conf ]; then
    sed -i 's/^Session=plasma\.desktop$/Session=plasmax11.desktop/' /etc/sddm.conf
fi
exit 0
