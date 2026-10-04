# Навык: Анимации и микро-взаимодействия (UI Motion & Effects Skill)

## Инструкции для агента
Ты выступаешь в роли motion-дизайнера и фронтенд-инженера. Ты добавляешь в интерфейс «красивые фишки» уровня витрин анимированных компонентов (референс: codeandchill.store): появление при скролле, раскладка текста по буквам, магнитные кнопки, свет под курсором, бегущая строка, наклон карточек, счётчики, «скрэмбл» текста. Только чистый CSS и ванильный JS, без GSAP/Framer, 60 fps, работа на тач-устройствах и при `prefers-reduced-motion`.

### Правила движения
1. Анимируй только `transform` и `opacity` (и `filter`/`clip-path` точечно). Никогда `top/left/width/height` в цикле.
2. Появления: `--ease-out` (`cubic-bezier(0.22,1,0.36,1)`), 500–800 мс, сдвиг 16–32 px. Hover: 150–250 мс.
3. Каскад (stagger) 40–80 мс между элементами, не больше 8–10 шагов, дальше показывай сразу.
4. Эффекты от курсора включай только при `(hover: hover) and (pointer: fine)`.
5. Обновления от мыши/скролла через `requestAnimationFrame`, слушатели `{ passive: true }`.
6. Под нагрузкой ничего не ломается: быстрые повторные клики, ресайз, смена вкладки, длинный текст.
7. Всегда блок reduced motion:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
}
```
```js
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;
```

### 1. Появление при скролле с каскадом
```html
<div data-reveal-group><article data-reveal>…</article><article data-reveal>…</article></div>
```
```css
.js [data-reveal] { opacity: 0; transform: translateY(24px); filter: blur(6px);
  transition: opacity .8s var(--ease-out), transform .8s var(--ease-out), filter .8s var(--ease-out);
  transition-delay: calc(var(--i, 0) * 70ms); }
.js [data-reveal].is-in { opacity: 1; transform: none; filter: none; }
```
```js
document.documentElement.classList.add("js"); // без JS контент виден
document.querySelectorAll("[data-reveal-group]").forEach(g =>
  g.querySelectorAll("[data-reveal]").forEach((el, i) => el.style.setProperty("--i", Math.min(i, 8))));
const io = new IntersectionObserver(entries => entries.forEach(e => {
  if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
}), { rootMargin: "0px 0px -10% 0px", threshold: 0.15 });
document.querySelectorAll("[data-reveal]").forEach(el => io.observe(el));
```

### 2. Заголовок по словам/буквам (split text)
```js
function splitText(el, by = "word") {
  const text = el.textContent; el.setAttribute("aria-label", text); el.textContent = "";
  const parts = by === "char" ? [...text] : text.split(/(\s+)/);
  parts.forEach((p, i) => {
    if (/^\s+$/.test(p)) { el.append(p); return; }
    const mask = document.createElement("span"); mask.className = "split-mask"; mask.setAttribute("aria-hidden", "true");
    const inner = document.createElement("span"); inner.className = "split-inner"; inner.textContent = p;
    inner.style.setProperty("--i", i); mask.append(inner); el.append(mask);
  });
}
```
```css
.split-mask { display: inline-block; overflow: hidden; vertical-align: top; padding-bottom: .08em; }
.split-inner { display: inline-block; transform: translateY(110%);
  animation: rise .9s var(--ease-out) forwards; animation-delay: calc(var(--i) * 45ms + 100ms); }
@keyframes rise { to { transform: none; } }
```

### 3. Бесконечная бегущая строка (marquee) без рывков
```html
<div class="marquee" style="--speed: 30s"><div class="marquee__track">
  <span>Buttons</span><span>Tabs</span><span>Toasts</span><span>Loaders</span></div></div>
```
```css
.marquee { overflow: hidden; mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent); }
.marquee__track { display: flex; gap: 48px; width: max-content; animation: marquee var(--speed) linear infinite; }
.marquee:hover .marquee__track { animation-play-state: paused; }
@keyframes marquee { to { transform: translateX(calc(-50% - 24px)); } } /* -50% и половина gap */
```
```js
document.querySelectorAll(".marquee__track").forEach(t => {   // дублируем содержимое для бесшовности
  t.append(...[...t.children].map(n => { const c = n.cloneNode(true); c.setAttribute("aria-hidden", "true"); return c; }));
});
```

### 4. Свет под курсором на карточках (spotlight + светящаяся рамка)
```css
.spot { --x: 50%; --y: 50%; position: relative; }
.spot::before { content: ""; position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
  background: radial-gradient(400px circle at var(--x) var(--y), rgba(255,106,61,.12), transparent 40%);
  opacity: 0; transition: opacity .3s; }
.spot::after { content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1px; pointer-events: none;
  background: radial-gradient(300px circle at var(--x) var(--y), rgba(255,106,61,.7), transparent 40%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude; opacity: 0; transition: opacity .3s; }
.spot:hover::before, .spot:hover::after { opacity: 1; }
```
```js
if (finePointer) document.querySelectorAll(".spot").forEach(card => {
  card.addEventListener("pointermove", e => {
    const r = card.getBoundingClientRect();
    card.style.setProperty("--x", `${e.clientX - r.left}px`);
    card.style.setProperty("--y", `${e.clientY - r.top}px`);
  }, { passive: true });
});
```

### 5. Магнитная кнопка
```js
function magnetic(el, strength = 0.35) {
  if (!finePointer || reduceMotion) return;
  let raf = 0;
  el.addEventListener("pointermove", e => {
    const r = el.getBoundingClientRect();
    const dx = (e.clientX - (r.left + r.width / 2)) * strength;
    const dy = (e.clientY - (r.top + r.height / 2)) * strength;
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => el.style.transform = `translate(${dx}px, ${dy}px)`);
  });
  el.addEventListener("pointerleave", () => { cancelAnimationFrame(raf); el.style.transform = ""; });
}
```
```css
.magnetic { transition: transform .4s var(--ease-spring); will-change: transform; }
```

### 6. 3D-наклон карточки (tilt) с бликом
```js
function tilt(el, max = 8) {
  if (!finePointer || reduceMotion) return;
  el.addEventListener("pointermove", e => {
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
    el.style.transform = `perspective(900px) rotateX(${-py * max}deg) rotateY(${px * max}deg)`;
    el.style.setProperty("--gx", `${(px + 0.5) * 100}%`);
  });
  el.addEventListener("pointerleave", () => el.style.transform = "");
}
```
```css
.tilt { transition: transform .5s var(--ease-out); transform-style: preserve-3d; }
.tilt::after { content: ""; position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
  background: linear-gradient(115deg, transparent 30%, rgba(255,255,255,.08) var(--gx, 50%), transparent 70%); }
```

### 7. Кастомный курсор с инерцией
```js
function cursor() {
  if (!finePointer || reduceMotion) return;
  const dot = Object.assign(document.createElement("div"), { className: "cursor" });
  document.body.append(dot);
  let x = innerWidth / 2, y = innerHeight / 2, cx = x, cy = y;
  addEventListener("pointermove", e => { x = e.clientX; y = e.clientY; }, { passive: true });
  document.addEventListener("pointerover", e => dot.classList.toggle("is-hover", !!e.target.closest("a,button,[data-cursor]")));
  (function loop() { cx += (x - cx) * 0.18; cy += (y - cy) * 0.18;
    dot.style.transform = `translate(${cx}px, ${cy}px) translate(-50%, -50%)`; requestAnimationFrame(loop); })();
}
```
```css
.cursor { position: fixed; left: 0; top: 0; width: 10px; height: 10px; border-radius: 50%; z-index: 999;
  background: var(--text); mix-blend-mode: difference; pointer-events: none;
  transition: width .25s var(--ease-out), height .25s var(--ease-out); }
.cursor.is-hover { width: 44px; height: 44px; }
```

### 8. Скрэмбл-текст (перебор символов при наведении)
```js
function scramble(el, chars = "!<>-_\\/[]{}—=+*^?#01") {
  const final = el.textContent; let frame = 0, raf = 0;
  const run = () => {
    cancelAnimationFrame(raf); frame = 0;                    // повторный hover перезапускает, а не копит циклы
    const tick = () => {
      el.textContent = [...final].map((c, i) => i < frame / 2 || c === " " ? c
        : chars[Math.floor(Math.random() * chars.length)]).join("");
      if (frame++ < final.length * 2) raf = requestAnimationFrame(tick); else el.textContent = final;
    };
    tick();
  };
  if (!reduceMotion) el.addEventListener("pointerenter", run);
}
```
Для скрэмбла используй моноширинный шрифт, чтобы ширина не прыгала.

### 9. Счётчик чисел при появлении
```js
function countUp(el, to = +el.dataset.to, dur = 1400) {
  if (reduceMotion) { el.textContent = to.toLocaleString("ru-RU"); return; }
  const t0 = performance.now(), ease = t => 1 - Math.pow(1 - t, 4);
  (function step(now) { const p = Math.min((now - t0) / dur, 1);
    el.textContent = Math.round(to * ease(p)).toLocaleString("ru-RU");
    if (p < 1) requestAnimationFrame(step); })(t0);
}
```
Задавай `font-variant-numeric: tabular-nums`, чтобы цифры не дрожали.

### 10. Прогресс скролла и параллакс без JS (scroll-driven animations)
```css
.progress { position: fixed; inset: 0 0 auto; height: 2px; background: var(--accent);
  transform-origin: 0 50%; animation: grow linear both; animation-timeline: scroll(root); }
@keyframes grow { from { transform: scaleX(0); } }
@supports (animation-timeline: view()) {
  .parallax { animation: drift linear both; animation-timeline: view(); animation-range: entry 0% exit 100%; }
  @keyframes drift { from { transform: translateY(40px); } to { transform: translateY(-40px); } }
}
```

### 11. Кнопка с бегущей подсветкой и «волной» нажатия
```css
.btn-shine { position: relative; overflow: hidden; }
.btn-shine::after { content: ""; position: absolute; inset: 0; transform: translateX(-120%);
  background: linear-gradient(100deg, transparent 30%, rgba(255,255,255,.35), transparent 70%); }
.btn-shine:hover::after { transform: translateX(120%); transition: transform .7s var(--ease-out); }
.ripple { position: absolute; border-radius: 50%; background: currentColor; opacity: .25; pointer-events: none;
  transform: scale(0); animation: ripple .6s var(--ease-out) forwards; }
@keyframes ripple { to { transform: scale(1); opacity: 0; } }
```
```js
document.addEventListener("pointerdown", e => {
  const b = e.target.closest(".btn-ripple"); if (!b) return;
  const r = b.getBoundingClientRect(), s = Math.max(r.width, r.height) * 2;
  const w = Object.assign(document.createElement("span"), { className: "ripple" });
  Object.assign(w.style, { width: s + "px", height: s + "px", left: e.clientX - r.left - s / 2 + "px", top: e.clientY - r.top - s / 2 + "px" });
  b.append(w); w.addEventListener("animationend", () => w.remove());   // не копим DOM при спаме кликами
});
```

### 12. Переходы между состояниями (View Transitions)
```js
function swap(update) { document.startViewTransition ? document.startViewTransition(update) : update(); }
```
Используй для смены вкладок, фильтров витрины, открытия карточки в полноэкранный превью.

### Формат вывода
- Код эффекта (HTML + CSS + JS) готовый к вставке, с токенами из навыка `ui-design-system`.
- Для каждого эффекта: где включается, как отключается на тач и при reduced motion.
- Готовая демонстрация всех эффектов: `tools/design-kit/index.html`.
