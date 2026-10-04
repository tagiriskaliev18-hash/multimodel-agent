# Навык: Одностраничная витрина в стиле Code and Chill (One-Page Storefront Template Skill)

## Инструкции для агента
Ты выступаешь в роли дизайнера и верстальщика витрин. Ты собираешь одностраничный сайт по раскладке codeandchill.store (снята с живого сайта на 1440px и 390px, в обеих темах): полоса распродажи, липкая шапка из трёх колонок, герой «подложка + полка», шкала «scroll = camera», сетки карточек с живыми превью, коллекции, абзац-объяснение, FAQ и таблица характеристик, строгий подвал. Один `index.html` на чистом HTML/CSS/JS, без JS всё читается. Токены и оболочка из `ui-design-system`, движение из `ui-motion`, компоненты из `ui-components`. Эталонная сборка: `tools/design-kit/index.html`.

Тексты, названия, цены и картинки пиши свои. Чужие логотипы, видео-превью и копирайт не переносить.

### Структура страницы (сверху вниз)
1. **Полоса распродажи** `.sale-strip`: одна строка моно капсом на `--buy-bg`, разделитель «·» (`FLAT SALE · 60% OFF · ENDS OCT 6` как образец формата).
2. **Шапка** `.header` (липкая, полупрозрачная бумага + `blur(10px)`, линия 2px снизу), сетка `1fr auto 1fr`:
   - слева вордмарк (два жирных слова + тонкая акцентная связка);
   - по центру 4–5 ссылок моно капсом, активная: акцентный текст, мягкий акцентный фон и линия 2px снизу (`box-shadow: inset 0 -2px 0 var(--accent)`);
   - справа поле-кнопка поиска `SEARCH ⌘K`, квадрат темы, квадрат корзины со счётчиком.
   На ≤60rem навигация уходит второй строкой с горизонтальным скроллом; на ≤30rem у поиска остаётся только иконка.
3. **Герой** `.hero` (на ≥60rem сетка `20rem | 1fr`):
   - слева `.hero__tray` на подложке с линией сверху: `.display` из 4–5 коротких строк, под ним абзац с цифрами («82 компонента и 40 шаблонов… от $2, навсегда ваши»);
   - под подложкой `.hero__actions`: `.btn--fill` с числом («BROWSE 82») и обычная `.btn` («FREE ONE»);
   - справа `.shelf` — полка 6–8 карточек 9:16 с инерционным перетаскиванием, масштабом по удалённости и бликом (`ui-motion` §2), под ней точки, подсказка «→ drag to spin the shelf» и `1 / 7`.
4. **Шкала прокрутки** `.camera`: `SCROLL = CAMERA`, рельса, `P 0.00` (`ui-motion` §3).
5. **«Most wanted this week»**: заголовок `.title` + ссылка-стрелка `EVERYTHING NEW →` на одной линии; сетка «широкая 16:9 слева + вертикальная справа», флажки соцдоказательства на карточках («6 PEOPLE PICKED IT»).
6. **Коллекции** «Shop by collection»: 4 карточки с мозаикой из 4 превью, заголовок, описание, моно-строка `13 DESIGNS · ALL FOR $56 · SAVE $23.60`.
7. **«What these are — one paragraph»**: подложка во всю ширину, моно-метка и один абзац крупным текстом о том, что это и почему без подписок.
8. **«Featured — hand-picked»**: 4 карточки с флажком `FEATURED` и ссылкой `ALL 82 →`.
9. **«See it running»**: большая рамка 2px, по центру играет одно превью.
10. **Нижний блок**: моно-метка `WHAT'S INCLUDED · FAQ · FOOTER`, два абзаца со ссылками (лицензия, FAQ, changelog).
11. **Подвал**: линия 2px сверху, слева вордмарк и одна фраза о проекте, справа 2 колонки ссылок с моно-заголовками.

Страница продукта (если нужна): заголовок + моно-строка `$3.60 $9 −60% · 8.6 KB GZ · 0 DEPS · UPD. SEP 19, 2026`, справа «тема ◐», «ADD TO CART», `.btn--buy` «BUY · $3.60 →»; ниже две рамки «сцена с превью | QUICK START с кнопкой COPY», ряд кнопок `CODE PEEK ▾ / THEME / ADD TO CART / BUY`, строка `BUNDLE` с предложением набора, затем «WHAT IT DOES» (абзац + список с квадратными акцентными маркерами) и таблица характеристик `.specs` (тип, категория, стек, зависимости, размер, файлы, версия, обновлено, лицензия, обновления). Переход карточка → страница через View Transition `product-stage` (`ui-motion` §5).

### Каркас
```html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f0eee9" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#171615" media="(prefers-color-scheme: dark)">
  <title>Бренд — детали интерфейса, которые держат нагрузку</title>
  <meta name="description" content="…">
  <meta property="og:title" content="…"><meta property="og:image" content="/og.jpg"><meta name="twitter:card" content="summary_large_image">
  <script>/* тема до отрисовки, см. ui-design-system */</script>
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@100..900&family=Architects+Daughter&display=swap" rel="stylesheet">
  <style>/* токены обеих тем → база → шапка → герой/полка → карточки → секции → оверлеи */</style>
</head>
<body>
  <a class="skip-link" href="#main">К содержимому</a>
  <p class="sale-strip">…</p>
  <header class="header"><div class="page header__inner">
    <a class="wordmark header__mark" href="/">Brand<span class="wordmark__and">and</span>Name</a>
    <nav class="header__nav" aria-label="Разделы">…</nav>
    <div class="header__tools"><button class="header__search">…<span class="kbd">⌘K</span></button>
      <button class="icon-btn theme-toggle" aria-label="Переключить тему">…</button>
      <button class="icon-btn" aria-label="Корзина">…<span class="cart-count" hidden>0</span></button></div>
  </div></header>
  <main id="main" class="main"><div class="page">
    <section class="hero">…tray · actions · shelf…</section>
    <div class="camera" aria-hidden="true">…</div>
    <section class="section">…</section>
  </div></main>
  <footer class="footer">…</footer>
  <div class="toasts" aria-live="polite"></div>
  <!-- шторка корзины и палитра ⌘K: hidden до открытия -->
</body>
</html>
```

### Скелетон до загрузки
Если витрина рисуется скриптом, в `#root` заранее лежит `.boot`: строка бренда моно с квадратом акцента и сетка плиток 9:16 на `--tray` с `boot-pulse` (`ui-motion` §13). Ошибка загрузки данных: крупный заголовок («Магазин не отвечает»), строка причины и `.btn--fill` «TRY AGAIN».

### Карточки витрины
- Превью: видео `muted loop playsinline` с постером (`/reels/<slug>.jpg`), подгрузка за 1200px до экрана, игра только в кадре (`ui-motion` §4). Если видео нет, живой компонент в тёмном «кадре»: полоска окна с тремя точками, `NAME — HTML CSS JS` с цветными метками, `localhost / name` справа, сцена, внизу три панели кода `index.html / style.css / app.js` с цветными точками.
- Тело: имя и цена на одной линии, теглайн в одну строку со строчной буквы, моно-метаданные `8.7 KB · 1 DEP · NAVIGATION`.
- Квадратная кнопка корзины в углу, флажок слева сверху, вся карточка — ссылка (`aria-label="Имя — цена"`).
- Фильтры каталога: ряд `.chip` с `aria-pressed`, смена через `document.startViewTransition`.

### Критерии готовности
1. Lighthouse: Performance ≥ 90, Accessibility ≥ 95, без горизонтального скролла на 360px.
2. Обе темы без вспышки, переключатель в шапке, `theme-color` для каждой.
3. Все анимации гаснут при `prefers-reduced-motion`; полка становится обычной сеткой, шкала камеры не рендерится.
4. Без JS видны все секции, ссылки работают, полка листается нативно.
5. Ни одного скругления и размытой тени в оболочке; акцент только в продающих и активных местах.
6. Свои тексты и графика, никаких чужих логотипов, видео и цен.

### Формат вывода
- Готовый `index.html` (при необходимости `styles.css`, `app.js`), карта секций с якорями и список мест, где менять тексты, цены и превью.
