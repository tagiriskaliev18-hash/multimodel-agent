# Chevrolet Camaro — промо-сайт (Three.js)

Одностраничный сайт с реальной 3D-моделью Camaro: въезд машины, облёт камеры по скроллу,
раздел «Поехали» (удерживайте кнопку газа), конфигуратор цвета/полос и 5 комплектаций
(1LT, 3LT, LT1, SS, ZL1), которые отличаются диски, посадкой, обвесом, спойлером и капотом.

## Запуск
Нужен любой статический сервер (используется fetch/XHR):

    cd sites/camaro && python3 -m http.server 8000

Откройте http://localhost:8000. Three.js подгружается с cdn.jsdelivr.net, шрифты — с Google Fonts.

## Хостинг
Ветка `gh-pages` содержит ту же папку. GitHub Pages: Settings → Pages → Deploy from a branch → `gh-pages` / root.

## Лицензии и ссылки
- 3D-модель «Chevrolet Camaro» — GregX (Sketchfab), CC BY 4.0.
- Панорама Alps field (Andreas Mischok) и текстура asphalt_07 — Poly Haven, CC0.
- Three.js — MIT.
