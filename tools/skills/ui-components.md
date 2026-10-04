# Навык: Анимированные компоненты, устойчивые под нагрузкой (UI Components Skill)

## Инструкции для агента
Ты выступаешь в роли инженера дизайн-системы. Ты делаешь «детали интерфейса, которые держат нагрузку» (референс: codeandchill.store): кнопки, переключатели, вкладки, тосты, модалки, аккордеоны, копирование кода, скелетоны. Каждый компонент красиво анимирован, но в первую очередь корректен: доступен с клавиатуры, не ломается от спама кликами, длинного текста, медленной сети и отключённого JS. Чистые HTML/CSS/JS, токены из навыка `ui-design-system`, движение по правилам навыка `ui-motion`.

### Стресс-тест каждого компонента (обязателен)
1. 20 быстрых кликов подряд: нет дублей, зависших состояний, утечек DOM и таймеров.
2. Текст в 3 раза длиннее ожидаемого и одно слово без пробелов: ничего не вылезает (`overflow-wrap: anywhere`, `min-width: 0`).
3. Только клавиатура: Tab, Shift+Tab, Enter, Space, Esc, стрелки; видимый `:focus-visible`.
4. Экранный диктор: правильные роли и `aria-*` (`aria-pressed`, `aria-selected`, `aria-expanded`, `aria-live`).
5. Ширина 320px и масштаб 200%.
6. `prefers-reduced-motion`: состояние меняется мгновенно, логика та же.
7. Асинхронные действия: `disabled` + `aria-busy` во время запроса, обработка ошибки, нельзя отправить дважды.

### Кнопки
```css
.btn {
  --h: 44px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  min-height: var(--h); padding: 0 20px; border-radius: var(--radius-pill); border: 1px solid var(--line-strong);
  background: var(--bg-elev-2); color: var(--text); font: 500 15px/1 var(--font-sans); cursor: pointer;
  transition: transform var(--dur-fast) var(--ease-out), background var(--dur-fast), border-color var(--dur-fast);
  -webkit-tap-highlight-color: transparent; user-select: none;
}
.btn:hover { background: #2e2b28; border-color: rgba(240,235,225,.28); }
.btn:active { transform: scale(0.97); }
.btn:disabled, .btn[aria-busy="true"] { opacity: .55; cursor: not-allowed; transform: none; }
.btn--primary { background: var(--accent); color: var(--accent-ink); border-color: transparent; font-weight: 600; }
.btn--primary:hover { background: color-mix(in srgb, var(--accent) 88%, white); }
/* Стрелка, уезжающая при hover */
.btn .arrow { transition: transform var(--dur) var(--ease-spring); }
.btn:hover .arrow { transform: translateX(3px); }
/* Спиннер загрузки */
.btn[aria-busy="true"]::before { content: ""; width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid currentColor; border-right-color: transparent; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
```
```js
// Асинхронная кнопка: не даёт двойной отправки, возвращает исходное состояние
async function withBusy(btn, task) {
  if (btn.getAttribute("aria-busy") === "true") return;
  btn.setAttribute("aria-busy", "true"); btn.disabled = true;
  try { await task(); } finally { btn.removeAttribute("aria-busy"); btn.disabled = false; }
}
```

### Переключатель (switch)
```html
<button class="switch" role="switch" aria-checked="false"><span class="switch__thumb"></span><span class="sr-only">Тёмная тема</span></button>
```
```css
.switch { width: 46px; height: 28px; padding: 3px; border-radius: 999px; border: 1px solid var(--line-strong);
  background: var(--bg-elev-2); cursor: pointer; transition: background var(--dur) var(--ease-out); }
.switch__thumb { display: block; width: 20px; height: 20px; border-radius: 50%; background: var(--text);
  transition: transform var(--dur) var(--ease-spring), width var(--dur-fast); }
.switch:active .switch__thumb { width: 24px; }              /* «тянется» при нажатии */
.switch[aria-checked="true"] { background: var(--accent); }
.switch[aria-checked="true"] .switch__thumb { transform: translateX(18px); background: var(--accent-ink); }
.switch[aria-checked="true"]:active .switch__thumb { transform: translateX(14px); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
```
```js
document.addEventListener("click", e => { const s = e.target.closest(".switch"); if (!s) return;
  s.setAttribute("aria-checked", String(s.getAttribute("aria-checked") !== "true")); });
```

### Вкладки с «плавающим» индикатором
```html
<div class="tabs" role="tablist"><span class="tabs__pill" aria-hidden="true"></span>
  <button role="tab" aria-selected="true">HTML</button><button role="tab" aria-selected="false" tabindex="-1">CSS</button>
  <button role="tab" aria-selected="false" tabindex="-1">JS</button></div>
```
```css
.tabs { position: relative; display: inline-flex; padding: 4px; gap: 2px; border-radius: 999px; background: var(--bg-elev); border: 1px solid var(--line); }
.tabs [role="tab"] { position: relative; z-index: 1; border: 0; background: none; color: var(--text-dim);
  padding: 8px 16px; border-radius: 999px; font: 500 14px var(--font-sans); cursor: pointer; transition: color var(--dur); }
.tabs [aria-selected="true"] { color: var(--text); }
.tabs__pill { position: absolute; top: 4px; bottom: 4px; left: 0; border-radius: 999px; background: var(--bg-elev-2);
  border: 1px solid var(--line-strong); transition: transform var(--dur) var(--ease-out), width var(--dur) var(--ease-out); }
```
```js
function initTabs(list) {
  const tabs = [...list.querySelectorAll('[role="tab"]')], pill = list.querySelector(".tabs__pill");
  const place = t => { pill.style.width = t.offsetWidth + "px"; pill.style.transform = `translateX(${t.offsetLeft}px)`; };
  const select = t => { tabs.forEach(x => { const on = x === t; x.setAttribute("aria-selected", on); x.tabIndex = on ? 0 : -1; });
    place(t); list.dispatchEvent(new CustomEvent("tabchange", { detail: tabs.indexOf(t) })); };
  list.addEventListener("click", e => { const t = e.target.closest('[role="tab"]'); if (t) select(t); });
  list.addEventListener("keydown", e => { const i = tabs.indexOf(document.activeElement); if (i < 0) return;
    const n = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!n) return;
    const t = tabs[(i + n + tabs.length) % tabs.length]; t.focus(); select(t); });
  new ResizeObserver(() => place(tabs.find(t => t.getAttribute("aria-selected") === "true"))).observe(list);
}
```

### Тосты (уведомления) со стеком
```css
.toasts { position: fixed; right: 16px; bottom: 16px; display: grid; gap: 8px; z-index: 50; width: min(360px, calc(100vw - 32px)); }
.toast { background: var(--bg-elev-2); border: 1px solid var(--line-strong); border-radius: var(--radius); padding: 12px 16px;
  box-shadow: 0 12px 40px rgba(0,0,0,.4); animation: toast-in .45s var(--ease-spring); }
.toast.is-out { animation: toast-out .25s var(--ease-in-out) forwards; }
@keyframes toast-in { from { opacity: 0; transform: translateY(16px) scale(.96); } }
@keyframes toast-out { to { opacity: 0; transform: translateX(24px); } }
```
```js
const toastRoot = Object.assign(document.createElement("div"), { className: "toasts" });
toastRoot.setAttribute("aria-live", "polite"); document.body.append(toastRoot);
function toast(msg, ms = 3000) {
  while (toastRoot.children.length >= 3) toastRoot.firstElementChild.remove();   // не больше 3 при спаме
  const t = Object.assign(document.createElement("div"), { className: "toast", textContent: msg });
  toastRoot.append(t);
  let timer = setTimeout(close, ms);
  t.addEventListener("pointerenter", () => clearTimeout(timer));               // пауза при наведении
  t.addEventListener("pointerleave", () => timer = setTimeout(close, 1200));
  function close() { t.classList.add("is-out"); t.addEventListener("animationend", () => t.remove(), { once: true }); }
}
```

### Модалка на `<dialog>`
```css
dialog.modal { border: 1px solid var(--line-strong); border-radius: var(--radius-lg); background: var(--bg-elev); color: var(--text);
  padding: 32px; width: min(520px, calc(100vw - 32px)); opacity: 0; transform: translateY(12px) scale(.98);
  transition: opacity .3s var(--ease-out), transform .3s var(--ease-out), overlay .3s allow-discrete, display .3s allow-discrete; }
dialog.modal[open] { opacity: 1; transform: none; }
@starting-style { dialog.modal[open] { opacity: 0; transform: translateY(12px) scale(.98); } }
dialog.modal::backdrop { background: rgba(10,9,8,.6); backdrop-filter: blur(6px); }
```
```js
// showModal() даёт фокус-ловушку и Esc из коробки; клик по фону закрывает
dialog.addEventListener("click", e => { if (e.target === dialog) dialog.close(); });
```

### Аккордеон (FAQ) на `<details>` с плавной высотой
```css
.faq details { border-bottom: 1px solid var(--line); }
.faq summary { list-style: none; cursor: pointer; padding: 20px 0; display: flex; justify-content: space-between; font-weight: 500; }
.faq summary::after { content: "+"; transition: transform var(--dur) var(--ease-out); }
.faq details[open] summary::after { transform: rotate(45deg); }
.faq .answer { color: var(--text-dim); padding-bottom: 20px; }
/* Плавная высота без JS (Chrome 131+); в остальных браузерах просто открывается мгновенно */
:root { interpolate-size: allow-keywords; }
.faq details::details-content { block-size: 0; overflow: hidden;
  transition: block-size var(--dur) var(--ease-out), content-visibility var(--dur) allow-discrete; }
.faq details[open]::details-content { block-size: auto; }
```

### Блок кода с кнопкой «Скопировать»
```js
document.addEventListener("click", async e => {
  const b = e.target.closest("[data-copy]"); if (!b) return;
  const code = document.querySelector(b.dataset.copy)?.innerText ?? "";
  try { await navigator.clipboard.writeText(code); b.dataset.state = "done"; b.textContent = "Скопировано"; }
  catch { b.dataset.state = "error"; b.textContent = "Не удалось"; }
  clearTimeout(b._t); b._t = setTimeout(() => { b.textContent = "Скопировать"; delete b.dataset.state; }, 1600);
});
```

### Скелетон загрузки
```css
.skeleton { border-radius: var(--radius-sm); background:
  linear-gradient(90deg, var(--bg-elev) 0%, var(--bg-elev-2) 50%, var(--bg-elev) 100%) 0 0 / 200% 100%;
  animation: shimmer 1.4s linear infinite; }
@keyframes shimmer { to { background-position: -200% 0; } }
```

### Карточка-превью компонента (как на витрине)
Структура: живая сцена сверху (компонент работает прямо в карточке), снизу название, моно-теги и цена/статус.
```html
<article class="card spot preview" data-reveal>
  <div class="preview__stage grid-bg"><!-- живой компонент --></div>
  <div class="preview__meta"><h3>Magnetic Button</h3><span class="eyebrow">CSS · JS · 2 KB</span></div>
</article>
```
```css
.preview { padding: 0; display: grid; }
.preview__stage { aspect-ratio: 16/10; display: grid; place-items: center; border-bottom: 1px solid var(--line); }
.preview__meta { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 16px 20px; min-width: 0; }
.preview__meta h3 { margin: 0; font-size: var(--fs-h3); overflow-wrap: anywhere; }
```

### Формат вывода
- Компонент: HTML + CSS + JS, роли ARIA, состояния, комментарий «как стресс-тестировал».
- Если компонентов несколько, собирай их в сетку превью-карточек (см. навык `landing-page-template`).
