## DuoOS 1.0 «Genesis»

DuoOS — операционная система для разработчиков. Внешне она похожа на macOS, по устройству ближе к Linux Mint и основана на Ubuntu 26.04 LTS. Работает на любом x86-64 ПК с видеокартой AMD, Intel или NVIDIA.

### Как установить
1. Скачайте `duoos-1.0-amd64.iso`. Если файл разбит на `.part0`, `.part1`, скачайте все части и запустите `join-windows.bat`.
2. **На флешку:** запишите ISO программой [Rufus](https://rufus.ie) (режим «DD-образ») или [balenaEtcher](https://etcher.balena.io). Затем загрузитесь с флешки (F12, F11 или Esc при включении).
3. **В VMware:** создайте новую ВМ, укажите ISO, выберите тип «Ubuntu 64-bit», 4–8 ГБ ОЗУ, диск от 40 ГБ и включите 3D-ускорение.
4. В меню загрузки выберите **«Установить DuoOS»** и пройдите мастер.

Контрольная сумма: `sha256sum -c duoos-1.0-amd64.iso.sha256`.

Подробная инструкция: [os/README.md](https://github.com/tagiriskaliev18-hash/multimodel-agent/blob/main/os/README.md).
