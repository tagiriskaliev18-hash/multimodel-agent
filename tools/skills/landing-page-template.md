# Навык: Одностраничный лендинг-витрина (One-Page Landing Template Skill)

## Инструкции для агента
Ты выступаешь в роли дизайнера и верстальщика лендингов. Ты собираешь одностраничный сайт в стиле витрины анимированных компонентов (референс: codeandchill.store): тёмный тёплый фон, крупный типографический герой, живые превью вместо скриншотов, прозрачные разовые цены, FAQ. Один `index.html` на чистом HTML/CSS/JS, весит меньше 100 KB без шрифтов, работает без JS. Стили и токены берёшь из `ui-design-system`, эффекты из `ui-motion`, компоненты из `ui-components`.

### Структура страницы (сверху вниз)
1. **Шапка** `.glass`, липкая: логотип-слово, 3–4 якорные ссылки, кнопка CTA. На скролле вниз прячется (`translateY(-100%)`), при скролле вверх возвращается. На мобильном бургер, меню на `<dialog>`.
2. **Прогресс-бар скролла** 2px акцентом (`animation-timeline: scroll(root)`).
3. **Герой** `.hero` + `.grid-bg`: `.eyebrow` с живой точкой («New: 12 components»), заголовок `.display` с раскладкой по словам и одним словом в `.text-glow`, `.lead` до 2 строк, две кнопки (главная магнитная `.btn--primary.magnetic`, вторичная со стрелкой), под ними строка доверия моно-шрифтом («Plain HTML · CSS · JS — No dependencies»).
4. **Бегущая строка** `.marquee` с названиями категорий/технологий, разделитель «✦».
5. **Витрина** (`#components`): фильтры-вкладки `.tabs` (All / Buttons / Text / Cards / Loaders), сетка `.preview`-карточек со `.spot`-подсветкой; каждый эффект работает прямо в карточке. Смена фильтра через `document.startViewTransition`.
6. **Бенто-секция «почему»**: 4–5 карточек разного размера с цифрами `countUp` («2 KB avg», «60 fps», «0 deps», «A11y ready»).
7. **Код-превью**: окно редактора (три точки, вкладки HTML/CSS/JS, `<pre>` с подсветкой, кнопка копирования).
8. **Цены**: 2–3 карточки, средняя выделена акцентной рамкой и бейджем; «разовая оплата, бесплатные обновления». Цены и тексты пиши свои, не копируй чужие.
9. **FAQ** `.faq` на `<details>`.
10. **Финальный CTA**: огромный заголовок во всю ширину, кнопка, свечение снизу.
11. **Подвал**: колонки ссылок, год, мелкий моно-текст, ссылка «наверх».

### Каркас
```html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#171615">
  <title>Название — короткий слоган</title>
  <meta name="description" content="…">
  <meta property="og:title" content="…"><meta property="og:image" content="/og.jpg">
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>/* токены ui-design-system → базовые стили → компоненты → эффекты → @media reduced-motion */</style>
</head>
<body>
  <a class="sr-only" href="#main">К содержимому</a>
  <div class="progress" aria-hidden="true"></div>
  <header class="site-header glass">…</header>
  <main id="main">
    <section class="hero grid-bg">…</section>
    <div class="marquee">…</div>
    <section id="components">…</section>
    <section id="why">…</section>
    <section id="pricing">…</section>
    <section id="faq" class="faq">…</section>
    <section class="cta">…</section>
  </main>
  <footer>…</footer>
  <script type="module">/* reveal, split, magnetic, spotlight, tabs, countUp, header-hide */</script>
</body>
</html>
```

### Прячущаяся шапка
```js
let lastY = scrollY, ticking = false;
addEventListener("scroll", () => { if (ticking) return; ticking = true; requestAnimationFrame(() => {
  const y = scrollY, h = document.querySelector(".site-header");
  h.classList.toggle("is-hidden", y > lastY && y > 120); h.classList.toggle("is-scrolled", y > 8);
  lastY = y; ticking = false; }); }, { passive: true });
```
```css
.site-header { position: sticky; top: 0; z-index: 40; transition: transform .4s var(--ease-out); }
.site-header.is-hidden { transform: translateY(-100%); }
.site-header:focus-within { transform: none; } /* не прячем, пока фокус внутри */
```

### Бенто-сетка
```css
.bento { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; }
.bento > :nth-child(1) { grid-column: span 4; grid-row: span 2; }
.bento > :nth-child(n+2) { grid-column: span 2; }
@media (max-width: 760px) { .bento > * { grid-column: 1 / -1 !important; grid-row: auto !important; } }
```

### Ценовая карточка с вращающейся рамкой
```css
@property --angle { syntax: "<angle>"; initial-value: 0deg; inherits: false; }
.price--featured { border: 1px solid transparent;
  background: linear-gradient(var(--bg-elev), var(--bg-elev)) padding-box,
              conic-gradient(from var(--angle), transparent 60%, var(--accent), transparent 90%) border-box;
  animation: spin-border 4s linear infinite; }
@keyframes spin-border { to { --angle: 360deg; } }
```

### Окно редактора кода
```css
.editor { border: 1px solid var(--line); border-radius: var(--radius); background: #12110f; overflow: hidden; }
.editor__bar { display: flex; align-items: center; gap: 6px; padding: 10px 14px; border-bottom: 1px solid var(--line); }
.editor__bar i { width: 10px; height: 10px; border-radius: 50%; background: var(--line-strong); }
.editor pre { margin: 0; padding: 20px; overflow-x: auto; font: 13px/1.7 var(--font-mono); color: var(--text-dim); }
.editor .k { color: var(--accent); } .editor .s { color: var(--ok); } .editor .c { color: var(--text-faint); }
```

### Критерии готовности
1. Lighthouse: Performance ≥ 95, Accessibility ≥ 95 на мобильном профиле.
2. Нет горизонтального скролла на 360px; все тач-цели ≥ 44px.
3. Все эффекты отключаются при reduced motion, контент виден без JS.
4. Только собственные тексты, иконки (inline SVG) и изображения, никаких чужих логотипов и брендинга.
5. Мета-теги: `theme-color`, `description`, Open Graph 1200×630.

### Формат вывода
- Готовый `index.html` целиком; если больше 600 строк, выноси `styles.css` и `app.js`.
- Список секций и использованных эффектов с якорями в коде.
- Живой пример всех приёмов: `tools/design-kit/index.html`.
