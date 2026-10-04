# Навык: Дизайн-система «бумага и чернила» в стиле Code and Chill (UI Design System Skill)

## Инструкции для агента
Ты выступаешь в роли продуктового UI-дизайнера и фронтенд-инженера. Ты строишь интерфейсы в стиле витрины анимированных компонентов codeandchill.store («interface parts that behave under pressure»). Стиль снят с живого сайта (CSS, DOM, скриншоты в обеих темах), а не угадан: это **редакционный брутализм**: тёплая бумага и тёплые чернила, прямые углы, толстые 2px линии, жёсткие тени со смещением, моноширинные подписи капсом и один красно-оранжевый акцент. Всё на чистом HTML, CSS и JavaScript.

Воспроизводи приёмы своим кодом. Не копируй чужие логотипы, видео-превью, фотографии и тексты.

### Принципы стиля
1. **Бумага и чернила, две темы на равных.** Светлая тема `#f0eee9` / `#201e1d`, тёмная `#171615` / `#f0eee9`. Тема выбирается до первой отрисовки (скрипт в `<head>`), переключатель в шапке.
2. **Прямые углы.** `border-radius: 0` у карточек, кнопок, полей, тостов. Скругление только у счётчика корзины (`999px`) и внутри живых превью.
3. **Линия вместо тени.** Всё обведено `2px solid var(--ink)` (`--rule`) или `1.5px solid var(--ink-25)` (`--hairline`). Разделы отбиваются линией сверху.
4. **Тень только жёсткая и только как отклик.** Смещённая плашка без размытия: карточка при hover `8px 8px 0 var(--ink-12)` + подъём на 4px; кнопка покупки `3px 3px 0 var(--ink)` + сдвиг на `-3px,-3px`; тост `6px 6px 0 var(--ink)`.
5. **Два голоса типографики.** Плотный гротеск (Archivo Variable, 700, трекинг `-0.03em`, высота строки 0.98) для заголовков и моно капсом (600, 0.688–0.75rem, разрядка `0.08–0.1em`) для всего служебного: навигация, кнопки, метки, цены-скидки, размеры файлов.
6. **Один акцент.** `--accent` (`#ec3013` светлая / `#ff5c3d` тёмная) для полосы распродажи, кнопки «Купить», флажков на карточках, активной ссылки, фокуса, выделения текста, заполнения прогресса. Мягкий вариант `--accent-soft` (12–16% альфа) для фона чипа скидки и hover у призрачной кнопки.
7. **Подложка «tray».** Вспомогательные блоки (герой, полка, «одним абзацем») лежат на `--tray`: 5% чернил поверх бумаги, без рамки или с линией сверху.
8. **Живое превью вместо картинки.** Карточка показывает работающий компонент (видео или iframe) в кадре 9:16 или 16:9; ниже имя, цена, теглайн и моно-метаданные `8.7 KB · 0 DEPS · FORM`.
9. **Одно движение на всё.** Одна кривая `--ease: cubic-bezier(.2,.7,.2,1)` и один такт `--beat: .32s` для всех hover/переходов (подробно в навыке `ui-motion`).

### Токены (вставляй в начало любого CSS)
```css
:root {
  /* Цвет: светлая тема (по умолчанию) */
  --paper: #f0eee9;          /* фон страницы */
  --tray: #0000000d;         /* подложка вспомогательных блоков */
  --surface: #fff;           /* карточки, поля, тосты */
  --ink: #201e1d;            /* текст и линии */
  --ink-70: #201e1db3;       /* вторичный текст */
  --ink-50: #201e1da8;       /* подписи, моно-метки */
  --ink-25: #201e1d40;       /* тонкие линии, неактивные точки */
  --ink-12: #201e1d1f;       /* тень карточки, hover-фон */
  --accent: #ec3013;
  --accent-soft: #ec30131f;
  --accent-ink: #b8240c;     /* акцентный ТЕКСТ на бумаге (контраст AA) */
  --buy-bg: #d42a0f; --buy-fg: #fff; --buy-shadow: var(--ink);

  --rule: 2px solid var(--ink);
  --hairline: 1.5px solid var(--ink-25);

  /* Типографика: шкала на clamp() */
  --step-0: clamp(.95rem, .92rem + .15vw, 1.05rem);   /* текст */
  --step-1: clamp(1.15rem, 1.05rem + .5vw, 1.45rem);  /* подзаголовок */
  --step-2: clamp(1.5rem, 1.25rem + 1.2vw, 2.1rem);   /* заголовок секции */
  --step-3: clamp(2rem, 1.4rem + 3vw, 3.6rem);        /* дисплей героя */
  --font-body: "Archivo Variable", Archivo, "Helvetica Neue", system-ui, sans-serif;
  --font-mono: ui-monospace, "SF Mono", Menlo, monospace;
  --font-note: "Architects Daughter", var(--font-body); /* рукописные пометки */

  /* Пространство: шаг ×1.5 */
  --space-1: .375rem; --space-2: .75rem; --space-3: 1.125rem;
  --space-4: 1.75rem; --space-5: 2.75rem; --space-6: 4.5rem;
  --measure: 62ch;
  --page: 76rem;             /* 84rem от 84rem экрана, 94rem от 100rem */

  /* Движение */
  --ease: cubic-bezier(.2, .7, .2, 1);
  --beat: .32s;
}
:root[data-theme="dark"] {
  --paper: #171615; --tray: #ffffff0d; --surface: #201e1d;
  --ink: #f0eee9; --ink-70: #f0eee9b3; --ink-50: #f0eee980; --ink-25: #f0eee940; --ink-12: #f0eee924;
  --accent: #ff5c3d; --accent-soft: #ff5c3d29; --accent-ink: #ff5c3d;
  --buy-bg: #ff5c3d; --buy-fg: #171615;
}
@media (width >= 84rem)  { :root { --page: 84rem; } }
@media (width >= 100rem) { :root { --page: 94rem; } }

*, ::before, ::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; scroll-padding-top: 7rem; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font: 400 var(--step-0)/1.6 var(--font-body); -webkit-font-smoothing: antialiased; overflow-wrap: break-word; }
a { color: inherit; text-underline-offset: .2em; text-decoration-thickness: 1px; }
a:hover { text-decoration-color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
::selection { background: var(--accent); color: var(--paper); }
.page { width: min(100% - 2.5rem, var(--page)); margin-inline: auto; }
.numeric { font-variant-numeric: tabular-nums; }
```

### Тема без вспышки
```html
<meta name="theme-color" content="#f0eee9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#171615" media="(prefers-color-scheme: dark)">
<script>
  // До первой отрисовки: сохранённая тема или системная
  (() => { try {
    const t = localStorage.getItem("ui:theme") ?? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.dataset.theme = t; document.documentElement.style.colorScheme = t;
  } catch {} })();
</script>
```
Переключатель меняет `data-theme` и пишет в `localStorage`; эффектный вариант со вспышкой круга описан в `ui-components` («Переключатель темы, из которого выливается свет»).

### Типографика
```css
.display  { font-size: var(--step-3); font-weight: 700; letter-spacing: -.03em; line-height: .98; text-wrap: balance; }
.title    { font-size: var(--step-2); font-weight: 700; letter-spacing: -.02em; line-height: 1.05; text-wrap: balance; }
.subtitle { font-size: var(--step-1); font-weight: 600; letter-spacing: -.01em; line-height: 1.2; }
.label    { font: 600 .688rem/1.4 var(--font-mono); letter-spacing: .1em; text-transform: uppercase; color: var(--ink-50); }
.label--ink { color: var(--ink); }
.prose    { max-width: var(--measure); color: var(--ink-70); }
.note     { font-family: var(--font-note); color: var(--accent-ink); font-size: 1rem; } /* «рукописная» пометка */
/* Вордмарк: два жирных слова и тонкая акцентная связка между ними */
.wordmark { font-weight: 800; letter-spacing: -.04em; line-height: 1; white-space: nowrap; color: var(--ink); }
.wordmark__and { font-size: .667em; font-weight: 300; letter-spacing: 0; color: var(--accent); margin-inline: .12em .1em; }
```
Шрифты: `https://fonts.googleapis.com/css2?family=Archivo:wght@100..900&family=Architects+Daughter&display=swap` (Archivo там вариативный). Моно берётся системный: `ui-monospace, SF Mono, Menlo`.

### Базовые блоки
```css
.tray { background: var(--tray); border-top: var(--rule); padding: var(--space-3); }
.rule-top { border-top: var(--rule); padding-top: var(--space-3); }

/* Кнопки: моно капсом, 2px рамка, подъём на 2px */
.btn { --btn-bg: transparent; --btn-fg: var(--ink);
  display: inline-flex; align-items: center; justify-content: center; gap: .5rem;
  min-height: 3rem; padding: 0 var(--space-3); border: var(--rule); background: var(--btn-bg); color: var(--btn-fg);
  font: 600 .75rem var(--font-mono); letter-spacing: .1em; text-transform: uppercase; text-decoration: none; cursor: pointer;
  transition: transform var(--beat) var(--ease), background var(--beat) var(--ease), color var(--beat) var(--ease); }
.btn:hover { transform: translateY(-2px); }
.btn:active { transform: none; }
.btn--fill { --btn-bg: var(--ink); --btn-fg: var(--paper); }
.btn--fill:hover { --btn-bg: var(--accent); border-color: var(--accent); }
.btn--ghost:hover { --btn-bg: var(--accent-soft); }
.btn--small { min-height: 2.25rem; padding: 0 var(--space-2); border-width: 1.5px; font-size: .688rem; }
.btn:disabled { cursor: progress; opacity: .65; transform: none; }
/* Главная кнопка «Купить»: жёсткая тень, кнопка «приподнимается» над ней */
.btn--buy { --btn-bg: var(--buy-bg); --btn-fg: var(--buy-fg); border-color: var(--buy-bg);
  min-height: 3.25rem; padding: 0 var(--space-4); font-size: .813rem; font-weight: 700;
  transition: transform var(--beat) var(--ease), box-shadow var(--beat) var(--ease); }
.btn--buy:hover { transform: translate(-3px, -3px); box-shadow: 3px 3px 0 var(--buy-shadow); }
.btn--buy:active { transform: none; box-shadow: none; }
.btn__arrow { transition: transform var(--beat) var(--ease); }
.btn--buy:hover .btn__arrow { transform: translateX(3px); }

/* Квадратная иконка-кнопка в шапке: инверсия при hover */
.icon-btn { width: 2.5rem; height: 2.5rem; display: inline-grid; place-items: center; border: var(--rule);
  background: none; color: var(--ink); cursor: pointer; transition: background var(--beat) var(--ease), color var(--beat) var(--ease); }
.icon-btn:hover { background: var(--ink); color: var(--paper); }

/* Клавиша-подсказка (⌘K) */
.kbd { display: inline-flex; gap: .125rem; padding: .125rem .375rem; border: 1.5px solid var(--ink-25);
  font: 600 .688rem var(--font-mono); color: var(--ink-50); }

/* Цена: текущая, зачёркнутая, чип скидки */
.price { display: inline-flex; align-items: baseline; gap: .4em; white-space: nowrap; }
.price__now { font-weight: 700; }
.price__was { color: var(--ink-50); text-decoration: line-through 1.5px color-mix(in srgb, var(--ink-50) 80%, transparent); }
.price__off { align-self: center; padding: .2em .45em; font: 600 .688rem/1 var(--font-mono); letter-spacing: .04em;
  color: var(--accent-ink); background: var(--accent-soft); }

/* Чип-фильтр: нажатый = инверсия */
.chip { all: unset; padding: .375rem .625rem; border: 1.5px solid var(--ink-25); cursor: pointer;
  font: 600 .688rem var(--font-mono); letter-spacing: .08em; text-transform: uppercase;
  transition: background var(--beat) var(--ease), border-color var(--beat) var(--ease); }
.chip:hover { border-color: var(--ink); }
.chip[aria-pressed="true"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.chip:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Полоса распродажи над шапкой */
.sale-strip { padding: .5rem var(--space-3); text-align: center; background: var(--buy-bg); color: var(--buy-fg);
  font: 600 .75rem/1.3 var(--font-mono); letter-spacing: .06em; text-transform: uppercase; }
```

### Карточка продукта
```css
.card { position: relative; display: grid; grid-template-rows: auto 1fr; background: var(--surface); border: var(--rule);
  color: inherit; text-decoration: none; transition: transform var(--beat) var(--ease), box-shadow var(--beat) var(--ease); }
.card:hover, .card:focus-visible { transform: translateY(-4px); box-shadow: 8px 8px 0 var(--ink-12); }
.card__demo { position: relative; border-bottom: var(--rule); aspect-ratio: 9/16; overflow: hidden; background: var(--tray); }
.card[data-shape="wide"] .card__demo { aspect-ratio: 16/9; }
.card__body { display: grid; gap: .25rem; padding: .75rem 1rem .875rem; }
.card__name { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-2); font-weight: 600; letter-spacing: -.01em; }
.card__tagline { color: var(--ink-70); font-size: .875rem; line-height: 1.35; }
.card__meta { display: flex; flex-wrap: wrap; gap: .125rem .75rem; padding-top: .25rem; } /* внутри .label */
.card__flag { position: absolute; top: 0; left: 0; z-index: 2; padding: .25rem .5rem; background: var(--buy-bg); color: var(--buy-fg);
  font: 600 .625rem var(--font-mono); letter-spacing: .1em; text-transform: uppercase; }  /* «FEATURED», «6 PEOPLE PICKED IT» */
.card__cart { position: absolute; top: .5rem; right: .5rem; z-index: 3; transition: transform var(--beat) var(--ease); }
.card-shell:hover .card__cart { transform: translateY(-4px); } /* кнопка корзины едет вместе с карточкой */
```

### Таблица характеристик
```css
.specs { border: var(--rule); }
.specs__row { display: grid; grid-template-columns: 12rem 1fr; gap: var(--space-3); padding: var(--space-2) var(--space-3); }
.specs__row + .specs__row { border-top: var(--hairline); }
.specs dt { font: 600 .688rem/1.6 var(--font-mono); letter-spacing: .1em; text-transform: uppercase; color: var(--ink-50); }
```

### Сетки
- Каталог: `grid-template-columns: repeat(auto-fill, minmax(min(100%, 17rem), 1fr)); gap: var(--space-3)`, сетка — контейнер `container-type: inline-size`, широкие карточки `[data-shape="wide"]` занимают `span 2` от 35rem контейнера и `span 3` от 53rem.
- «Самое популярное»: две колонки `minmax(min(100%, max(24rem, (100% - gap)/2)), 1fr)`, широкая карточка слева, вертикальная справа.
- Герой: на ≥60rem `grid-template-columns: minmax(0, 20rem) minmax(0, 1fr)`, слева подложка с заголовком и кнопками, справа полка.
- Шапка: `grid-template-columns: 1fr auto 1fr` (лого слева, навигация строго по центру, инструменты справа), липкая, `background: color-mix(in srgb, var(--paper) 88%, transparent); backdrop-filter: blur(10px); border-bottom: var(--rule)`.
- Ритм секций `margin-top: var(--space-6)`, заголовок секции + ссылка «ALL 82 →» на одной базовой линии (`justify-content: space-between; align-items: baseline`).
- Телефон: сетка в 1 колонку, у карточек скрываются метаданные, теглайн обрезается до 2 строк, навигация уходит во вторую строку шапки с горизонтальным скроллом без полосы.

### Контрольный список перед сдачей
1. Обе темы выглядят законченно, переключение без вспышки, `theme-color` под каждую.
2. Ни одного скругления и размытой тени в оболочке интерфейса.
3. Акцентный цвет текста на бумаге только `--accent-ink` (контраст AA), чистый `--accent` только для заливок.
4. Всё служебное моно капсом, всё содержательное гротеском; цифры с `tabular-nums`.
5. У каждого интерактивного элемента есть `:hover`, `:active`, `:focus-visible` (2px акцентный контур со смещением) и `disabled`.
6. Есть ссылка «пропустить к содержимому» и `.visually-hidden` для подписей иконок.
7. Никаких чужих логотипов, видео и текстов.

### Формат вывода
- Один `index.html` (или `index.html` + `styles.css` + `app.js`), токены обеих тем в начале CSS.
- Короткий список применённых приёмов и где в коде их менять.
