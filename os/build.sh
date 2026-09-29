#!/usr/bin/env bash
# AIsktagOS — сборка загрузочного ISO (BIOS + UEFI + Secure Boot).
#
#   sudo ./build.sh            полная сборка
#   sudo ./build.sh iso        пересобрать только ISO из готового chroot
#   sudo ./build.sh clean      удалить рабочий каталог
#
# Переменные окружения:
#   WORK_DIR        рабочий каталог (по умолчанию ./work)
#   OUT_DIR         куда положить ISO (по умолчанию ./out)
#   BUILD_CA_CERT   дополнительный CA-сертификат для HTTPS внутри chroot
#                   (нужен только за MITM-прокси; в образ не попадает)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.env
source "$ROOT_DIR/config.env"

WORK_DIR="${WORK_DIR:-$ROOT_DIR/work}"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/out}"
CHROOT="$WORK_DIR/chroot"
ISO_TREE="$WORK_DIR/iso"
ISO_NAME="${OS_ID}-${OS_VERSION}-${ARCH}.iso"
VOLID="$(echo "${OS_NAME}_${OS_VERSION}" | tr '[:lower:].' '[:upper:]_')"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mОшибка: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "запустите через sudo"

mount_chroot() {
    for d in dev dev/pts proc sys run; do
        mkdir -p "$CHROOT/$d"
        mountpoint -q "$CHROOT/$d" && continue
        case "$d" in
            proc) mount -t proc proc "$CHROOT/proc" ;;
            sys)  mount -t sysfs sysfs "$CHROOT/sys" ;;
            run)  mount -t tmpfs tmpfs "$CHROOT/run" ;;
            *)    mount --bind "/$d" "$CHROOT/$d" ;;
        esac
    done
}

umount_chroot() {
    for d in run sys proc dev/pts dev; do
        mountpoint -q "$CHROOT/$d" && umount -l "$CHROOT/$d" || true
    done
}
trap umount_chroot EXIT

check_host() {
    local missing=()
    for c in debootstrap mksquashfs xorriso grub-mkimage mkfs.vfat mcopy; do
        command -v "$c" >/dev/null || missing+=("$c")
    done
    [ -e /usr/lib/grub/i386-pc/boot_hybrid.img ] || missing+=("grub-pc-bin")
    [ ${#missing[@]} -eq 0 ] || die "не хватает: ${missing[*]}
  sudo apt install debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools dosfstools"
    # debootstrap на старых хостах может не знать новый релиз Ubuntu
    local scripts=/usr/share/debootstrap/scripts
    [ -e "$scripts/$UBUNTU_SUITE" ] || ln -s gutsy "$scripts/$UBUNTU_SUITE"
}

stage_bootstrap() {
    if [ -e "$CHROOT/.debootstrap-done" ]; then
        log "Базовая система уже есть, пропускаю debootstrap"
        return
    fi
    log "debootstrap Ubuntu $UBUNTU_SUITE"
    rm -rf "$CHROOT"
    mkdir -p "$CHROOT"
    debootstrap --arch="$ARCH" --components=main,restricted,universe,multiverse \
        --include=ca-certificates,gnupg,curl \
        "$UBUNTU_SUITE" "$CHROOT" "$UBUNTU_MIRROR"
    touch "$CHROOT/.debootstrap-done"
}

stage_system() {
    log "Установка пакетов и настройка системы"
    mount_chroot

    # Пакетный список и скрипты для chroot
    rm -rf "$CHROOT/tmp/aisktagos-build"
    mkdir -p "$CHROOT/tmp/aisktagos-build"
    cp -a "$ROOT_DIR/packages" "$ROOT_DIR/scripts" "$ROOT_DIR/config.env" "$CHROOT/tmp/aisktagos-build/"
    cp -a "$ROOT_DIR/overlay" "$CHROOT/tmp/aisktagos-build/overlay"

    if [ -n "${BUILD_CA_CERT:-}" ]; then
        cp "$BUILD_CA_CERT" "$CHROOT/usr/local/share/ca-certificates/aisktagos-build-ca.crt"
        chroot "$CHROOT" update-ca-certificates >/dev/null
    fi
    cp /etc/resolv.conf "$CHROOT/tmp/aisktagos-build/resolv.conf" 2>/dev/null || true

    chroot "$CHROOT" /usr/bin/env -i \
        HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 \
        http_proxy="${http_proxy:-}" https_proxy="${https_proxy:-}" no_proxy="${no_proxy:-}" \
        bash /tmp/aisktagos-build/scripts/chroot-setup.sh

    if [ -n "${BUILD_CA_CERT:-}" ]; then
        rm -f "$CHROOT/usr/local/share/ca-certificates/aisktagos-build-ca.crt"
        chroot "$CHROOT" update-ca-certificates --fresh >/dev/null
    fi
    rm -rf "$CHROOT/tmp/aisktagos-build"
    umount_chroot
    touch "$CHROOT/.system-done"
}

stage_iso() {
    [ -e "$CHROOT/.system-done" ] || die "chroot не готов — запустите полную сборку"
    log "Подготовка дерева ISO"
    rm -rf "$ISO_TREE"
    mkdir -p "$ISO_TREE"/{casper,.disk,boot/grub,EFI/boot}

    local kver
    kver="$(basename "$(ls -d "$CHROOT"/lib/modules/* | sort -V | tail -1)")"
    cp "$CHROOT/boot/vmlinuz-$kver" "$ISO_TREE/casper/vmlinuz"
    cp "$CHROOT/boot/initrd.img-$kver" "$ISO_TREE/casper/initrd"

    # Список пакетов: полный и тот, что установщик удалит
    chroot "$CHROOT" dpkg-query -W --showformat='${Package} ${Version}\n' > "$ISO_TREE/casper/filesystem.manifest"
    grep -v '^#' "$ROOT_DIR/packages/90-live.list" | sed '/^$/d' > "$ISO_TREE/casper/filesystem.manifest-remove"

    echo "$OS_NAME $OS_VERSION \"$OS_CODENAME\" - $ARCH ($(date -u +%Y%m%d))" > "$ISO_TREE/.disk/info"
    echo "$OS_URL" > "$ISO_TREE/.disk/release_notes_url"
    touch "$ISO_TREE/.disk/base_installable"
    echo "full_cd/single" > "$ISO_TREE/.disk/cd_type"
    touch "$ISO_TREE/$OS_ID"   # метка для поиска корня ISO из GRUB

    log "Сжатие файловой системы ($SQUASHFS_COMP) — это самый долгий шаг"
    local comp_opts=(-comp "$SQUASHFS_COMP")
    [ "$SQUASHFS_COMP" = "xz" ] && comp_opts+=(-Xbcj x86 -b 1M -Xdict-size 100%)
    [ "$SQUASHFS_COMP" = "zstd" ] && comp_opts+=(-Xcompression-level "${ZSTD_LEVEL:-19}" -b 1M)
    mksquashfs "$CHROOT" "$ISO_TREE/casper/filesystem.squashfs" \
        -noappend -wildcards "${comp_opts[@]}" \
        -e 'proc/*' 'sys/*' 'dev/*' 'run/*' 'tmp/*' '.debootstrap-done' '.system-done' \
           'boot/vmlinuz*.old' 'var/cache/apt/archives/*.deb'
    du -sx --block-size=1 "$CHROOT" | cut -f1 > "$ISO_TREE/casper/filesystem.size"

    build_grub
    build_iso_image
}

build_grub() {
    log "Загрузчик GRUB (BIOS + UEFI + Secure Boot)"
    local g="$ISO_TREE/boot/grub"
    sed -e "s/@OS_NAME@/$OS_NAME/g" -e "s/@OS_ID@/$OS_ID/g" -e "s/@OS_VERSION@/$OS_VERSION/g" \
        "$ROOT_DIR/iso/grub.cfg" > "$g/grub.cfg"
    # Подписанный GRUB ищет конфиг в /EFI/ubuntu — даём ему ту же конфигурацию
    mkdir -p "$ISO_TREE/EFI/ubuntu"
    printf 'search --no-floppy --set=root --file /%s\nset prefix=($root)/boot/grub\nconfigfile $prefix/grub.cfg\n' \
        "$OS_ID" > "$ISO_TREE/EFI/ubuntu/grub.cfg"

    mkdir -p "$g/themes/aisktagos"
    cp "$ROOT_DIR"/iso/theme/* "$g/themes/aisktagos/"
    mkdir -p "$g/fonts"
    cp "$CHROOT/usr/share/grub/unicode.pf2" "$g/fonts/unicode.pf2"

    # BIOS: El Torito образ + модули
    mkdir -p "$g/i386-pc"
    cp "$CHROOT"/usr/lib/grub/i386-pc/*.mod "$CHROOT"/usr/lib/grub/i386-pc/*.lst "$g/i386-pc/"
    grub-mkimage -d "$CHROOT/usr/lib/grub/i386-pc" -O i386-pc -p /boot/grub \
        -o "$WORK_DIR/core.img" biosdisk iso9660 part_msdos part_gpt search normal configfile
    cat "$CHROOT/usr/lib/grub/i386-pc/cdboot.img" "$WORK_DIR/core.img" > "$g/i386-pc/eltorito.img"

    # UEFI: shim (подписан Microsoft) -> grub (подписан Canonical)
    # shimx64.efi.signed — ссылка на /etc/alternatives, с хоста она не разрешается
    local shim="" grub_signed mm f
    for f in shimx64.efi.signed.latest shimx64.efi.signed.previous; do
        [ -f "$CHROOT/usr/lib/shim/$f" ] && { shim="$CHROOT/usr/lib/shim/$f"; break; }
    done
    grub_signed="$CHROOT/usr/lib/grub/x86_64-efi-signed/gcdx64.efi.signed"
    mm="$CHROOT/usr/lib/shim/mmx64.efi"
    [ -f "$shim" ] && [ -f "$grub_signed" ] || die "нет подписанных shim/grub в chroot"
    cp "$shim" "$ISO_TREE/EFI/boot/bootx64.efi"
    cp "$grub_signed" "$ISO_TREE/EFI/boot/grubx64.efi"
    [ -f "$mm" ] && cp "$mm" "$ISO_TREE/EFI/boot/mmx64.efi"

    # FAT-раздел ESP для флешек и VMware/UEFI
    local efi_img="$WORK_DIR/efi.img"
    rm -f "$efi_img"
    mkfs.vfat -C -n "${OS_ID^^}_EFI" "$efi_img" 10240 >/dev/null
    mmd -i "$efi_img" ::/EFI ::/EFI/boot ::/EFI/ubuntu
    mcopy -i "$efi_img" "$ISO_TREE"/EFI/boot/* ::/EFI/boot/
    mcopy -i "$efi_img" "$ISO_TREE/EFI/ubuntu/grub.cfg" ::/EFI/ubuntu/grub.cfg
}

build_iso_image() {
    log "Запись ISO"
    mkdir -p "$OUT_DIR"
    (cd "$ISO_TREE" && find . -type f ! -name md5sum.txt ! -path './boot/grub/i386-pc/*' -print0 \
        | xargs -0 md5sum > md5sum.txt)
    xorriso -as mkisofs -r -iso-level 3 -V "$VOLID" -J -joliet-long -l \
        --grub2-mbr "$CHROOT/usr/lib/grub/i386-pc/boot_hybrid.img" \
        --protective-msdos-label -partition_cyl_align off -partition_offset 16 --mbr-force-bootable \
        -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b "$WORK_DIR/efi.img" \
        -appended_part_as_gpt \
        -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \
        -c boot.catalog \
        -b boot/grub/i386-pc/eltorito.img -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info \
        -eltorito-alt-boot -e '--interval:appended_partition_2:all::' -no-emul-boot \
        -o "$OUT_DIR/$ISO_NAME" "$ISO_TREE"
    (cd "$OUT_DIR" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256")
    log "Готово: $OUT_DIR/$ISO_NAME ($(du -h "$OUT_DIR/$ISO_NAME" | cut -f1))"
}

case "${1:-all}" in
    all)   check_host; stage_bootstrap; stage_system; stage_iso ;;
    system) check_host; stage_bootstrap; stage_system ;;
    iso)   check_host; stage_iso ;;
    # для отладки загрузчика: использовать уже сжатую squashfs
    boot)  check_host; build_grub; build_iso_image ;;
    clean) umount_chroot; rm -rf "$WORK_DIR"; log "Рабочий каталог удалён" ;;
    *)     die "неизвестная команда: $1 (all | system | iso | boot | clean)" ;;
esac
