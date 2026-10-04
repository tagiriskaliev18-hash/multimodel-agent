# Навык: Движение и «фишки» в стиле Code and Chill (UI Motion & Effects Skill)

## Инструкции для агента
Ты выступаешь в роли motion-дизайнера и фронтенд-инженера. Ты добавляешь движение так, как это сделано на codeandchill.store (снято с живого сайта: CSS, бандл JS, поведение в Chromium) и в его каталоге компонентов: оболочка двигается сдержанно и одинаково, а сами компоненты рассказывают состояние через одну непрерывную трансформацию. Только чистый CSS и ванильный JS, без GSAP и Lottie, 60 fps, тач и `prefers-reduced-motion`.

### Правила движения
1. **Одна кривая, один такт.** Вся оболочка (hover, раскрытие, смена темы) идёт на `--ease: cubic-bezier(.2,.7,.2,1)` и `--beat: .32s`. Открытия быстрее: подложка 0.16s, палитра 0.2s, шторка 0.24s, тост 0.26s, общий переход страницы 0.42s.
2. **Ключевые кадры только «откуда».** Пиши `@keyframes rise { 0% { opacity:0; transform: translateY(-8px) } }` без `to`: конечное состояние берётся из CSS элемента.
3. **Только `transform` и `opacity`** (точечно `clip-path`, `scale`, `filter`). Описания лучших компонентов прямо хвалятся «transform and opacity only».
4. **Состояние, а не украшение.** Кнопка не крутит спиннер, а превращается в индикатор своего процесса: контур становится полосой прогресса, иконка становится уровнем жидкости, ярлык «съедается». Длительность фазы ожидания равна реальной длительности запроса.
5. **Анимация тянется за реальными данными.** Прогресс скачивания из настоящего потока байтов, скорость ряби от скорости передачи, наклон желоба от скорости перетаскивания.
6. **Слушатели через rAF.** Скролл и указатель: `{ passive: true }`, вычисления в `requestAnimationFrame`, отмена предыдущего кадра.
7. **Видео и петли только в кадре.** `IntersectionObserver` с запасом 120px запускает и ставит на паузу; при `prefers-reduced-motion` или `navigator.connection.saveData` петли не стартуют.
8. **Reduced motion.** Глобально гасим длительности, но логика та же; отдельные виджеты (полоса «scroll = camera», таймер тоста) просто не рендерятся; полка превращается в обычную сетку.
```css
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, ::before, ::after { transition-duration: .001ms !important; animation-duration: .001ms !important; animation-iteration-count: 1 !important; }
}
```
```js
const RM = "(prefers-reduced-motion: reduce)";
const reduceMotion = () => matchMedia(RM).matches;
const saveData = () => navigator.connection?.saveData === true;
```

### 1. Библиотека ключевых кадров оболочки
```css
@keyframes fade      { 0% { opacity: 0 } }
@keyframes rise      { 0% { opacity: 0; transform: translateY(-8px) } }      /* палитра команд */
@keyframes slide-in  { 0% { transform: translateX(100%) } }                 /* шторка корзины */
@keyframes toast-in  { 0% { opacity: 0; transform: translateY(12px) } }
@keyframes toast-timer { to { transform: scaleX(0) } }
@keyframes boot-pulse { to { opacity: .45 } }                              /* скелетон, alternate */
@keyframes drift   { 0%, to { transform: translateY(0) }    50% { transform: translateY(-9px) } }
@keyframes drift-b { 0%, to { transform: translateY(-6px) } 50% { transform: translateY(4px) } }
@keyframes spec    { 0% { transform: translateX(-120%) } to { transform: translateX(400%) } } /* блик */
@keyframes hint    { 0%, to { opacity: .55; transform: none } 50% { opacity: 1; transform: translateX(10px) } }
```

### 2. Полка, которую «крутят» (drag-карусель с инерцией)
Горизонтальная лента карточек со `scroll-snap`. Мышью её тащат, отпущенная лента катится по инерции (скорость ×0.94 за кадр). Карточки «дышат» (`drift` с разными периодами), активная получает блик, соседние уменьшаются и тускнеют по расстоянию от активной (`data-rack` 0/1/2). Внизу точки-штрихи, подсказка «→ drag to spin the shelf» дважды «кивает» и счётчик `1 / 7`.
```css
.shelf__track { display: flex; gap: var(--space-2); overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; cursor: grab; }
.shelf__track[data-dragging="true"] { cursor: grabbing; scroll-snap-type: none; }
.shelf__track > * { flex: none; scroll-snap-align: start; width: min(70vw, 17rem); }
.drift { animation: drift 6.5s var(--ease) infinite; }
.drift:nth-child(2n) { animation: drift-b 7.5s var(--ease) infinite; }
.drift:nth-child(3n) { animation-duration: 8.5s; animation-delay: -2.4s; }
.shelf__track[data-dragging="true"] .drift { animation-play-state: paused; }
.card[data-rack] { transform-origin: bottom; transition: scale var(--beat) var(--ease), border-color var(--beat) var(--ease); }
.card[data-rack="1"] { scale: .9;  border-color: var(--ink-25); } .card[data-rack="1"] .card__demo { opacity: .5; }
.card[data-rack="2"] { scale: .81; border-color: var(--ink-12); } .card[data-rack="2"] .card__demo { opacity: .26; }
.card[data-rack="0"] .card__demo::after { content: ""; position: absolute; inset: 0 auto 0 0; width: 26%; pointer-events: none;
  background: linear-gradient(90deg, transparent, var(--accent-soft), transparent); animation: spec 5s var(--ease) infinite; }
.shelf__hint { animation: hint 2.4s var(--ease) 1.25; }   /* 1.25 повтора: кивнуть и остановиться на полпути */
.dots button::before { content: ""; display: block; width: .5rem; height: 3px; background: var(--ink-25);
  transition: width var(--beat) var(--ease), background var(--beat) var(--ease); }
.dots button[aria-current="true"]::before { width: 1.25rem; background: var(--ink); }
```
```js
function shelf(track, dots, counter) {
  const items = [...track.children]; let index = 0, raf = 0, coast = 0;
  const sync = () => {                       // активная = ближайшая к левому краю
    const left = track.getBoundingClientRect().left; let best = Infinity;
    items.forEach((el, i) => { const d = Math.abs(el.getBoundingClientRect().left - left); if (d < best) { best = d; index = i; } });
    items.forEach((el, i) => el.dataset.rack = Math.min(2, Math.abs(i - index)));
    dots.forEach((d, i) => d.setAttribute("aria-current", i === index)); counter.textContent = `${index + 1} / ${items.length}`;
  };
  track.addEventListener("scroll", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(sync); }, { passive: true });
  const goTo = i => { i = Math.max(0, Math.min(items.length - 1, i));
    track.scrollTo({ left: track.scrollLeft + items[i].getBoundingClientRect().left - track.getBoundingClientRect().left, behavior: "smooth" }); };
  dots.forEach((d, i) => d.onclick = () => goTo(i));
  track.addEventListener("keydown", e => ({ ArrowRight: () => goTo(index + 1), ArrowLeft: () => goTo(index - 1),
    Home: () => goTo(0), End: () => goTo(items.length - 1) })[e.key]?.(e.preventDefault()));
  track.addEventListener("pointerdown", e => {
    if (e.pointerType === "touch") return;   // на тач работает нативный скролл
    cancelAnimationFrame(coast);
    const s = { x: e.clientX, scroll: track.scrollLeft, last: e.clientX, v: 0, id: e.pointerId };
    track.dataset.dragging = "true";
    const move = ev => { if (ev.pointerId !== s.id) return; s.v = ev.clientX - s.last; s.last = ev.clientX; track.scrollLeft = s.scroll - (ev.clientX - s.x); };
    const glide = () => { s.v *= .94; track.scrollLeft -= s.v; if (Math.abs(s.v) > .4) coast = requestAnimationFrame(glide); };
    const up = () => { removeEventListener("pointermove", move); removeEventListener("pointerup", up); removeEventListener("pointercancel", up);
      track.dataset.dragging = "false"; coast = requestAnimationFrame(glide); };
    addEventListener("pointermove", move); addEventListener("pointerup", up); addEventListener("pointercancel", up);
  });
  sync(); return { goTo };
}
```
Разметка: `role="group" aria-roledescription="carousel" tabindex="0" aria-label="… drag, or use the arrow keys"`, у карточек `draggable="false"`.

### 3. «scroll = camera»: прогресс прокрутки как приборная шкала
Под героем: моно-метка `SCROLL = CAMERA`, тонкая рельса и число `P 0.00` с двумя знаками. Заполнение `scaleX(p)` от левого края.
```html
<div class="camera" aria-hidden="true"><span class="label">scroll = camera</span>
  <div class="camera__rail"><span class="camera__fill"></span></div><span class="label numeric">p <b>0.00</b></span></div>
```
```css
.camera { display: flex; align-items: center; gap: var(--space-3); border-top: var(--rule); padding-top: var(--space-2); }
.camera__rail { flex: 1; min-width: 0; height: 3px; background: var(--ink-12); }
.camera__fill { display: block; height: 3px; background: var(--accent); transform-origin: 0; transform: scaleX(0); }
```
```js
let raf = 0; const fill = document.querySelector(".camera__fill"), out = document.querySelector(".camera b");
const tick = () => { const max = document.documentElement.scrollHeight - innerHeight;
  const p = max > 0 ? Math.min(1, Math.max(0, scrollY / max)) : 0; fill.style.transform = `scaleX(${p})`; out.textContent = p.toFixed(2); };
addEventListener("scroll", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(tick); }, { passive: true });
addEventListener("resize", tick); tick();
```

### 4. Живое превью, которое играет только в кадре
```js
function reel(video) {
  let near = false, inView = false;
  new IntersectionObserver(([e]) => { if (e.isIntersecting && !near) { near = true; video.preload = "auto"; } }, { rootMargin: "1200px" }).observe(video);
  new IntersectionObserver(([e]) => { inView = e.isIntersecting; update(); }, { rootMargin: "120px" }).observe(video);
  const update = () => (inView && !reduceMotion() && !saveData()) ? video.play().catch(() => {}) : video.pause();
  matchMedia(RM).addEventListener("change", update);
}
```
При reduced motion поверх кадра кнопка «▶ play» на полупрозрачной бумаге `color-mix(in srgb, var(--paper) 72%, transparent)`, квадрат 3rem с рамкой, при hover заливается акцентом.

### 5. Переход «карточка → страница» (View Transitions)
Превью в карточке и сцена на странице продукта получают одно имя `view-transition-name: product-stage`, переход только при `no-preference`.
```css
@media (prefers-reduced-motion: no-preference) {
  ::view-transition-old(product-stage), ::view-transition-new(product-stage) {
    animation-duration: .42s; animation-timing-function: var(--ease); object-fit: cover; height: 100%; }
  ::view-transition-group(product-stage) { animation-duration: .42s; }
}
```
```js
const go = update => (!document.startViewTransition || reduceMotion()) ? update() : document.startViewTransition(update);
```

### 6. Тост с таймером, который можно придержать
Тост въезжает снизу (`toast-in .26s`), по низу бежит 3px акцентная полоса `toast-timer` линейно на всё время показа; при наведении `data-paused="true"` ставит её на паузу (`animation-play-state: paused`), закрытие по `animationend` полосы. При reduced motion полоса скрыта.

### 7. Буквы как движущаяся часть (glyph wave по направлению курсора)
Ярлык кнопки режется на глифы при монтировании, эффект выбирается атрибутом, волна идёт с той стороны, откуда пришёл курсор.
```js
function glyphs(btn) {
  const label = btn.querySelector(".glyph"); const text = label.textContent; btn.setAttribute("aria-label", text);
  label.textContent = ""; [...text].forEach((ch, i) => { const s = document.createElement("span"); s.textContent = ch === " " ? " " : ch;
    s.setAttribute("aria-hidden", "true"); s.style.setProperty("--i", i); label.append(s); });
  label.style.setProperty("--n", text.length);
  const run = fromRight => { btn.dataset.dir = fromRight ? "rtl" : "ltr"; btn.classList.remove("is-wave"); void btn.offsetWidth; btn.classList.add("is-wave"); };
  btn.addEventListener("pointerenter", e => { const r = btn.getBoundingClientRect(); run(e.clientX > r.left + r.width / 2); });
  btn.addEventListener("focus", () => run(false));
}
```
```css
.glyph span { display: inline-block; }
.is-wave .glyph span { animation: glyph-up .5s var(--ease) both; animation-delay: calc(var(--i) * 22ms); }
[data-dir="rtl"].is-wave .glyph span { animation-delay: calc((var(--n) - var(--i)) * 22ms); }
@keyframes glyph-up { 40% { transform: translateY(-.45em); opacity: .2 } 41% { transform: translateY(.45em) } }
```

### 8. Индикатор на двух пружинах (вкладки, нижняя навигация)
Индикатор не скользит целиком: передний и задний края — две независимые пружины, ведущая жёстче. В пути он вытягивается в «трубку», потом хвост догоняет и он сжимается обратно.
```js
function springBar(bar, getTarget) {
  const L = { x: 0, v: 0 }, R = { x: 0, v: 0 }; let raf = 0;
  const step = (s, to, k, d) => { s.v += (to - s.x) * k; s.v *= d; s.x += s.v; };
  const frame = () => { const t = getTarget(); const forward = t.left > L.x;
    step(L, t.left,  forward ? .06 : .16, .72); step(R, t.right, forward ? .16 : .06, .72);  // ведущий край жёстче
    bar.style.transform = `translateX(${L.x}px) scaleX(${Math.max(1, R.x - L.x)})`;            // ширина базового элемента 1px
    if (Math.abs(L.v) + Math.abs(R.v) + Math.abs(t.left - L.x) > .1) raf = requestAnimationFrame(frame); };
  return () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); };
}
```
Варианты из каталога: капля жидкости под краем панели, которая отрывает каплю в иконку; «бусина», под которой панель прогибается тем глубже, чем быстрее поездка; нить света, растянутая между старой и новой вкладкой.

### 9. «Свёртывание» (furl): пилюля → диск → ответ
Главный жест каталога. Кнопка-пилюля на время работы сворачивается в круг (ширина через `clip-path`/`scale`, не `width`), по кругу едет прогресс, по завершении круг разворачивается обратно и показывает итог (галочка, «Sent», «Ordered ✓»). Пример реализации в `ui-components` («Кнопка загрузки, чей контур и есть прогресс»). Типичные тайминги, измеренные авторами по кадрам: свёртка 640 мс на `cubic-bezier(.72,0,.33,.95)`, вспышка нового цвета темы 240 мс, поворот иконки 180° за 280 мс.

### 10. Жидкость как индикатор
Уровень заливки = прогресс. Жидкость вливается от точки нажатия (`clip-path: circle(r at x y)`), поверхность — синусоида в SVG-пути или `border-radius`-волна, рябь сильнее при быстрой передаче и «стекленеет» при паузе. Буквы ниже ватерлинии вырезаются из жидкости (`mix-blend-mode: difference` или дублирующий слой с `clip-path: inset(...)`).

### 11. Наклон «от касания» (nudge) и магнитный ярлык
Пилюля отклоняется от курсора, как будто её толкнули: `rotate` и `translate` пропорциональны смещению курсора от центра, возвращение пружиной. Только при `(hover: hover) and (pointer: fine)`.
```js
el.addEventListener("pointermove", e => { const r = el.getBoundingClientRect();
  const dx = (e.clientX - r.left) / r.width - .5, dy = (e.clientY - r.top) / r.height - .5;
  el.style.transform = `translate(${-dx * 6}px, ${-dy * 4}px) rotate(${-dx * 6}deg)`; });
el.addEventListener("pointerleave", () => el.style.transform = "");   /* transition: transform .5s cubic-bezier(.34,1.56,.64,1) */
```

### 12. Раскрытие без высоты (аккордеон на grid)
```css
.accordion__panel { display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--beat) var(--ease); }
.accordion__panel[data-open="true"] { grid-template-rows: 1fr; }
.accordion__inner { overflow: hidden; }
```

### 13. Скелетон загрузки до гидрации
Ещё до JS страница рисует бренд и сетку плиток 9:16 на `--tray` с тонкой рамкой, пульсирующих `boot-pulse 1.2s var(--ease) infinite alternate` (контейнер `role="status" aria-label="Loading"`).

### Формат вывода
- Код эффекта (HTML + CSS + JS), подключение, параметры (длительность, кривая, жёсткость пружин) вынесены в CSS-переменные или константы.
- Отдельно: что видит пользователь при reduced motion и на тач-устройстве.
