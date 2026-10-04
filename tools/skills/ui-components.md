# Навык: Анимированные компоненты, которые держат нагрузку (UI Components Skill)

## Инструкции для агента
Ты выступаешь в роли инженера компонентов уровня каталога codeandchill.store: «interface parts that behave under pressure». Каждая деталь — маленькая папка чистого HTML, CSS и JS без зависимостей, у которой есть одна яркая идея движения и при этом она корректна: клавиатура, экранный диктор, спам кликами, длинный текст, медленная сеть, reduced motion. Токены и оболочка из `ui-design-system`, правила движения из `ui-motion`. Все рецепты ниже работают в `tools/design-kit/index.html` (раздел «Компоненты вживую»), бери код оттуда целиком.

### Как придумывать компонент в этом стиле
1. **Одна метафора, доведённая до конца.** Кнопка удаления не исчезает, а корзина «ест» её ярлык; кнопка загрузки наполняется как стакан; кнопка отправки складывается в бумажный самолётик; код из SMS сплавляется в печать. Метафора объясняет состояние.
2. **Элемент не меняется на другой, а превращается.** Одна пилюля, один контур, одна иконка: свёртывается в диск, разворачивается в ответ. Никаких подмен «спиннер вместо кнопки».
3. **Ожидание = реальная работа.** Фаза «в процессе» длится ровно столько, сколько запрос; прогресс берётся из настоящих байтов (`ReadableStream`), отмена работает.
4. **Измеряй, а не угадывай.** Если есть видео-референс, снимай тайминги покадрово и подбирай кривую (`cubic-bezier`) под траекторию. Записывай числа в комментарии.
5. **Скины через три токена.** Цвет заливки, цвет текста, цвет обводки в CSS-переменных; светлая и тёмная версия без правки кода.
6. **Только `transform`/`opacity`/`clip-path`.** Ширину пилюли меняй через `clip-path: inset(... round 999px)`, а не `width`.

### Стресс-тест каждого компонента (обязателен)
1. 20 быстрых кликов: состояние-машина `data-state="idle|busy|done"` игнорирует клики не в `idle`, таймеры не копятся.
2. Ярлык в 3 раза длиннее и слово без пробелов: ничего не вылезает (`min-width: 0`, `overflow-wrap: anywhere`).
3. Только клавиатура: Tab, Enter, Space, стрелки, Esc; видимый `:focus-visible`.
4. Диктор: `aria-label` у кнопки с разрезанным на буквы ярлыком (буквы `aria-hidden`), `aria-busy` в процессе, `role="status"`/`aria-live` для итога, нативные `radio`/`input` внутри стилизованных элементов.
5. 320px ширины и масштаб 200%.
6. `prefers-reduced-motion`: фазы проходят мгновенно, логика и итог те же.
7. Ошибка: ветка `error` с понятным сообщением и возвратом в `idle` (пример — «0000» в Seal).

### 1. Furl: кнопка загрузки, чей контур и есть прогресс
Пилюля сворачивается в диск (`clip-path` за 640 мс на `cubic-bezier(.72,0,.33,.95)`), по ободу SVG-кольцо с `pathLength="1"` заполняется прогрессом, стрелка капает внутри, затем диск разворачивается в «Сохранено».
```html
<button class="furl" type="button" data-state="idle" aria-live="polite">
  <span class="furl__body"></span>
  <svg class="furl__ring" viewBox="0 0 62 62" aria-hidden="true"><circle class="furl__track" cx="31" cy="31" r="28"/><circle class="furl__bar" cx="31" cy="31" r="28" pathLength="1"/></svg>
  <span class="furl__drop" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 5v14M6 13l6 6 6-6"/></svg></span>
  <span class="furl__face furl__idle"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v12M6 10l6 6 6-6M5 20h14"/></svg>Скачать отчёт</span>
  <span class="furl__face furl__done"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 5 5 9-10"/></svg>Сохранено</span>
</button>
```
```css
.furl { --w: 12rem; --h: 3.25rem; --c: #2fd39a; position: relative; width: var(--w); height: var(--h); border: 0; padding: 0; background: none; cursor: pointer; color: #08130e; font-weight: 700; }
.furl__body { position: absolute; inset: 0; border-radius: 999px; background: var(--c); clip-path: inset(0 round 999px);
  transition: clip-path .64s cubic-bezier(.72, 0, .33, .95), background var(--beat) var(--ease); }
.furl[data-state="busy"] .furl__body { clip-path: inset(0 calc(50% - var(--h) / 2) round 999px); background: #12201a; }
.furl__face { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: .5rem; transition: opacity .2s var(--ease), transform .4s var(--ease); }
.furl__done { opacity: 0; transform: translateY(.6rem); }
.furl[data-state="busy"] .furl__idle { opacity: 0; transform: scale(.6); }
.furl[data-state="done"] .furl__idle { opacity: 0; transform: translateY(-.6rem); }
.furl[data-state="done"] .furl__done { opacity: 1; transform: none; }
.furl__ring { position: absolute; left: 50%; top: 50%; width: calc(var(--h) + 10px); aspect-ratio: 1; translate: -50% -50%; rotate: -90deg; opacity: 0; transition: opacity .25s; }
.furl__ring circle { fill: none; stroke-width: 3; }
.furl__track { stroke: color-mix(in srgb, var(--c) 25%, transparent); }
.furl__bar { stroke: var(--c); stroke-linecap: round; stroke-dasharray: 1; stroke-dashoffset: 1; }
.furl[data-state="busy"] .furl__ring { opacity: 1; transition-delay: .4s; }   /* кольцо появляется, когда диск уже свернулся */
```
```js
async function furl(btn, transfer /* async (onProgress) => void */) {
  if (btn.dataset.state !== "idle") return;
  const bar = btn.querySelector(".furl__bar");
  btn.dataset.state = "busy"; btn.setAttribute("aria-busy", "true");
  try { await transfer(p => bar.style.strokeDashoffset = 1 - p); btn.dataset.state = "done"; }
  catch { btn.dataset.state = "idle"; /* показать ошибку */ return; }
  finally { btn.removeAttribute("aria-busy"); }
  setTimeout(() => { btn.dataset.state = "idle"; bar.style.strokeDashoffset = 1; }, 2200);
}
// Реальный прогресс: fetch → reader, total из content-length
async function download(url, onProgress, signal) {
  const res = await fetch(url, { signal }); const total = +res.headers.get("content-length") || 0;
  const reader = res.body.getReader(); let got = 0; const chunks = [];
  for (;;) { const { done, value } = await reader.read(); if (done) break; chunks.push(value); got += value.length; if (total) onProgress(got / total); }
  return new Blob(chunks);
}
```
Вариации из каталога: бусина едет по ободу, а диск наполняется жидкостью; кольцо разматывается в полосу-верёвку, а стрелка спускается на парашюте; иконка становится сосудом и уровень поднимается с байтами.

### 2. Seal: код, который запечатывает себя
Четыре поля, автопереход, вставка всего кода, Backspace назад. На четвёртой цифре клетки слетаются к центру (`translateX((1.5 - i) * (box + gap))`), поворачиваются и сплавляются в плитку, в которой рисуется галочка (`stroke-dashoffset`). Неверный код трясёт ряд.
```css
.seal__row { --box: 3rem; --gap: .6rem; position: relative; display: flex; gap: var(--gap); }
.seal__box { width: var(--box); height: 3.6rem; border-radius: .7rem; text-align: center; font: 700 1.4rem var(--font-mono);
  transition: border-color .2s, transform .55s cubic-bezier(.65, 0, .35, 1), opacity .3s; }
.seal[data-state="sealing"] .seal__box, .seal[data-state="sealed"] .seal__box {
  transform: translateX(calc((1.5 - var(--i)) * (var(--box) + var(--gap)))) rotate(calc(var(--i) * 90deg - 135deg)) scale(.85);
  transition-delay: calc(var(--i) * 50ms); }
.seal[data-state="sealed"] .seal__box { opacity: 0; }
.seal__mark { position: absolute; left: 50%; top: 50%; translate: -50% -50%; scale: 0; transition: scale .45s cubic-bezier(.34, 1.56, .64, 1); }
.seal[data-state="sealed"] .seal__mark { scale: 1; transition-delay: .5s; }
.seal[data-state="error"] .seal__row { animation: shake .4s var(--ease); }
```
```js
boxes.forEach((box, i) => {
  box.addEventListener("input", () => { box.value = box.value.replace(/\D/g, "").slice(-1); if (box.value) boxes[i + 1]?.focus(); check(); });
  box.addEventListener("keydown", e => { if (e.key === "Backspace" && !box.value && boxes[i - 1]) { boxes[i - 1].focus(); boxes[i - 1].value = ""; } });
  box.addEventListener("paste", e => { e.preventDefault(); const d = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 4);
    [...d].forEach((ch, j) => boxes[j].value = ch); boxes[Math.min(d.length, 3)].focus(); check(); });
});
```
Первое поле с `autocomplete="one-time-code"`, все с `inputmode="numeric"`, группа `role="group" aria-label="Код из SMS"`, итог в `role="status"`. Вариации: ряд сворачивается на орбиту и ввинчивается; клетки раздаются веером как карты и складываются в колоду; цифры выдавлены в поверхности.

### 3. Decant: переключатель наливается, а не загорается
Нативная радиогруппа; у каждой пилюли слой жидкости `clip-path: circle()` из точки нажатия. Новая наполняется, прежняя стекает в ту точку, откуда её налили (координаты остаются в её `--px/--py`).
```css
.decant label { position: relative; overflow: hidden; isolation: isolate; border-radius: 999px; backdrop-filter: blur(8px); }
.decant input { position: absolute; opacity: 0; }
.decant label::before { content: ""; position: absolute; inset: 0; z-index: -1; background: var(--fill);
  clip-path: circle(0 at var(--px, 50%) var(--py, 50%)); transition: clip-path .55s cubic-bezier(.65, 0, .35, 1); }
.decant label:has(input:checked)::before { clip-path: circle(150% at var(--px, 50%) var(--py, 50%)); }
.decant label:has(input:focus-visible) { outline: 2px solid var(--accent); outline-offset: 3px; }
```
```js
label.addEventListener("pointerdown", e => { const r = label.getBoundingClientRect();
  label.style.setProperty("--px", `${e.clientX - r.left}px`); label.style.setProperty("--py", `${e.clientY - r.top}px`); });
```
С клавиатуры (стрелки) налив идёт из центра. Усиление: поверхность на `<canvas>`, колеблющаяся со скоростью пружины.

### 4. Twin: вкладки на двух пружинах
Код пружин в `ui-motion` §8. Обязательно: `role="tablist"`, у вкладок `aria-selected` и роving tabindex (`tabIndex = 0` только у активной), стрелки переключают, панель `role="tabpanel"`, при reduced motion индикатор ставится сразу, пересчёт на `resize` и после `document.fonts.ready`.

### 5. Gulp: удаление, которое съедает свой ярлык
Фазы `eating → furl → burst → done → idle`. Ярлык режется на буквы, каждой задаётся `--to` — расстояние до центра корзины; буквы с задержкой `i * 55ms` летят в корзину (`translate(var(--to), .6rem) scale(.15) rotate(-40deg)`), крышка открыта. Затем пилюля сворачивается в диск вокруг корзины, корзина наполняется (`scaleY` прямоугольника внутри SVG), всё лопается восемью искрами, остаётся «Удалено ✓».
```js
const b = bin.getBoundingClientRect(), r = btn.getBoundingClientRect();
letters.forEach(s => { const sr = s.getBoundingClientRect(); s.style.setProperty("--to", `${b.left + b.width / 2 - (sr.left + sr.width / 2)}px`); });
btn.style.setProperty("--disc", `${b.right - r.left + 14}px`);   /* ширина диска для clip-path пилюли */
btn.dataset.state = "eating"; await wait(450 + text.length * 55);
btn.dataset.state = "furl";   await wait(900);                   /* здесь ждём реальный DELETE */
btn.dataset.state = "burst";  await wait(600);
btn.dataset.state = "done";   await wait(1800); btn.dataset.state = "idle";
```
```css
.gulp__label span { display: inline-block; transition: transform .45s cubic-bezier(.55, 0, .7, .3), opacity .45s; transition-delay: calc(var(--i) * 55ms); }
.gulp[data-state="eating"] .gulp__label span { transform: translate(var(--to), .6rem) scale(.15) rotate(-40deg); opacity: 0; }
.gulp[data-state="furl"] .gulp__pill { clip-path: inset(0 calc(100% - var(--disc)) 0 0 round 999px); }
.gulp__spark { animation: spark .6s var(--ease) forwards; } /* rotate(var(--a)) translateY(-2.6rem) */
```
Вариации: корзина «зумится» до размера больше кнопки и ярлык переваливается через край; буквы растворяются в едком свете; бумажка падает и выходит снизу полосками шредера.

### 6. Glyph: двигается сам ярлык
Код в `ui-motion` §7. Три эффекта на `data-fx`: `up` (буквы уходят вверх и возвращаются снизу), `flip` (поворот по X с акцентным цветом в середине), `shake`. Направление волны — откуда пришёл курсор; фокус с клавиатуры и тап дают ту же волну.

### 7. Lumen: тема выливается кругом из кнопки
```js
btn.addEventListener("click", () => {
  const root = document.documentElement, next = root.dataset.theme === "dark" ? "light" : "dark";
  const apply = () => { root.dataset.theme = next; root.style.colorScheme = next; localStorage.setItem("ui:theme", next); };
  if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) return apply();
  const r = btn.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  root.style.setProperty("--lx", `${x}px`); root.style.setProperty("--ly", `${y}px`);
  root.style.setProperty("--lr", `${Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))}px`);
  document.startViewTransition(apply);
});
```
```css
::view-transition-old(root), ::view-transition-new(root) { animation: none; mix-blend-mode: normal; }
::view-transition-new(root) { animation: lumen .42s cubic-bezier(.52, .33, .46, .25) both; }  /* в референсе 240 мс */
@keyframes lumen { from { clip-path: circle(0 at var(--lx) var(--ly)); } to { clip-path: circle(var(--lr) at var(--lx) var(--ly)); } }
.theme-toggle svg { animation: half-turn .28s var(--ease); }   /* иконка солнца/луны делает пол-оборота при появлении */
@keyframes half-turn { 0% { transform: rotate(-180deg); } }
```

### 8. Nudge: пилюля, которую толкнули
Отклонение от курсора (код в `ui-motion` §11) + по клику фон заливается из точки статуса (`clip-path: circle(0 → 150% at 1.4rem 50%)`), строка «Написать нам» уезжает вверх, снизу приходит «Не стесняйтесь →». Точка статуса пульсирует кольцом `ping`.

### 9. Beads: лоадер из бусин без JS
Двенадцать бусин по кругу (`rotate(calc(var(--i) * 30deg))` с `transform-origin` в центре кольца), прозрачность растёт с индексом, весь круг вращается `steps(12)`: каждая треть секунды хвост «перепрыгивает» вперёд. Контейнер `role="img" aria-label="Загрузка"`. Правило 300 мс: показывай лоадер, только если ожидание дольше 300 мс.

### 10. Корзина: кнопка на карточке, тост с таймером, шторка
- Квадратная кнопка 2.5rem в правом верхнем углу карточки, `aria-pressed`, в корзине заливается акцентом; при hover карточки едет вверх на 4px вместе с ней.
- Счётчик в шапке — кружок акцента, при изменении `bump` (scale 1.35 на 40%).
- Тост: миниатюра, моно-заголовок «ДОБАВЛЕНО В КОРЗИНУ» цветом `--accent-ink`, имя + цена, крестик 2.75rem, кнопка «Открыть корзину» на всю ширину, полоса-таймер 3px снизу; пауза при наведении, не больше 3 тостов в стеке.
- Шторка: подложка `color-mix(in srgb, var(--ink) 32%, transparent)` с `fade .16s`, панель `slide-in .24s` справа шириной `min(100%, 28rem)`, `role="dialog" aria-modal="true"`, фокус на «закрыть», Esc и клик по подложке закрывают, фокус возвращается.

### 11. Палитра команд ⌘K
Кнопка поиска в шапке выглядит как поле (`SEARCH` + `⌘K`), открывает диалог `rise .2s`: поле без рамки, список с группами, активный пункт подсвечен `--accent-soft`, подвал с подсказками клавиш. ⌘K/Ctrl+K открывает и закрывает, ↑↓ двигают, Enter выполняет, Esc закрывает. В списке и компоненты, и действия («Сменить тему», «Открыть корзину»).

### Банк идей (техники из каталога, для новых компонентов)
- Кнопка «Купить» пакует товар, превращается в грузовичок и уезжает, оставляя «Ordered ✓».
- Кнопка отправки: самолётик пролетает сквозь ярлык, его след заливает кнопку и пишет «SENT».
- Индикатор вкладок — капля жидкости под краем панели, отрывающая каплю в иконку.
- Стеклянная панель, у которой край реально преломляет фон (SVG `feDisplacementMap` в `backdrop-filter`).
- Слайдер громкости, показывающий, чему равен уровень (наушник → трафик → турбина).
- Pull-to-refresh как рогатка: лента тянется, истончается, выстреливает запрос.
- Кнопка копирования как ксерокс: полоса света, копия выезжает в лоток; настоящая запись в буфер с фолбэком.
- Шкала острого перца: перец краснеет, потеет, трескается и загорается, назад — «разгорает».
- Аватары-ковёрфлоу: центральный в цвете, соседи в ч/б.

### Формат вывода
- Папка компонента: `index.html` (демо), `style.css`, `app.js`, короткий README (что делает, как подключить, токены скина, поведение при reduced motion).
- Отчёт по стресс-тесту: 7 пунктов, что проверено и как.
