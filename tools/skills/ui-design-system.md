# Навык: Тёмная дизайн-система в стиле Code and Chill (UI Design System Skill)

## Инструкции для агента
Ты выступаешь в роли продуктового UI-дизайнера и фронтенд-инженера. Ты строишь интерфейсы в стиле витрин анимированных компонентов (референс: codeandchill.store — «interface parts that behave under pressure»): тёплый почти-чёрный фон `#171615`, плотная типографика, много воздуха, один яркий акцент, живые превью вместо статичных картинок. Всё на чистом HTML, CSS и JavaScript, без фреймворков и тяжёлых библиотек.

### Принципы стиля
1. **Тёплый тёмный, не синий**: фон `#171615`, поверхности чуть светлее и теплее. Никакого `#000` и холодного `#0f172a`.
2. **Один акцент**: всё монохромно (кремовый текст на тёплом чёрном), акцентный цвет только для главного действия, фокуса и «живых» индикаторов.
3. **Тонкие границы вместо теней**: карточки отделяются линией `1px` с прозрачностью 8–12%, а не большими тенями.
4. **Крупный заголовок, мелкий служебный текст**: заголовки `clamp()` с плотным трекингом `-0.03em`, служебные подписи моноширинным шрифтом КАПСОМ с разрядкой `0.08em`.
5. **Зерно и свечение**: лёгкий шум поверх фона и мягкое радиальное свечение за героем дают глубину без картинок.
6. **Движение осмысленно**: анимация показывает состояние или ведёт взгляд, длительности 150–700 мс, всегда уважается `prefers-reduced-motion` (см. навык `ui-motion`).

### Токены (вставляй в начало любого CSS)
```css
:root {
  /* Цвет */
  --bg: #171615;            /* фон страницы */
  --bg-elev: #1e1d1b;       /* карточки */
  --bg-elev-2: #262422;     /* hover, поля ввода */
  --line: rgba(240, 235, 225, 0.10);
  --line-strong: rgba(240, 235, 225, 0.18);
  --text: #f0ebe1;          /* основной кремовый */
  --text-dim: #a8a196;      /* вторичный */
  --text-faint: #6f6a62;    /* подписи */
  --accent: #ff6a3d;        /* тёплый оранжевый: CTA, фокус */
  --accent-ink: #1a0d07;    /* текст на акценте */
  --ok: #7ad48a;  --warn: #f2c14e;  --err: #ff5c5c;

  /* Типографика */
  --font-sans: "Inter", "Manrope", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-display: "Space Grotesk", "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  --fs-hero: clamp(2.75rem, 7vw, 6.5rem);
  --fs-h2: clamp(1.9rem, 4vw, 3.25rem);
  --fs-h3: 1.25rem;
  --fs-body: 1rem;
  --fs-small: 0.8125rem;

  /* Пространство и форма */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px; --space-12: 48px; --space-16: 64px; --space-24: 96px;
  --radius-sm: 8px; --radius: 14px; --radius-lg: 22px; --radius-pill: 999px;
  --container: 1200px;

  /* Движение */
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);       /* «expo out» для появлений */
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1); /* лёгкий перелёт для кнопок */
  --dur-fast: 160ms; --dur: 320ms; --dur-slow: 700ms;
}

*, *::before, *::after { box-sizing: border-box; }
html { color-scheme: dark; -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 400 var(--fs-body)/1.6 var(--font-sans);
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
}
::selection { background: var(--accent); color: var(--accent-ink); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 6px; }
.container { width: min(100% - 32px, var(--container)); margin-inline: auto; }
```

### Типографика
```css
.display {
  font: 600 var(--fs-hero)/0.95 var(--font-display);
  letter-spacing: -0.035em; text-wrap: balance; margin: 0;
}
.h2 { font: 600 var(--fs-h2)/1.05 var(--font-display); letter-spacing: -0.03em; text-wrap: balance; }
.lead { font-size: clamp(1.05rem, 1.6vw, 1.25rem); color: var(--text-dim); max-width: 56ch; text-wrap: pretty; }
.eyebrow {
  font: 500 var(--fs-small)/1 var(--font-mono); text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--text-faint);
  display: inline-flex; align-items: center; gap: 8px;
}
.eyebrow::before { /* «живая» точка */
  content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--accent);
  box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent) 60%, transparent);
  animation: pulse-dot 2s var(--ease-out) infinite;
}
@keyframes pulse-dot { 70% { box-shadow: 0 0 0 8px transparent; } 100% { box-shadow: 0 0 0 0 transparent; } }
/* Градиентный акцент на одном слове заголовка */
.text-glow {
  background: linear-gradient(100deg, var(--text) 20%, var(--accent) 50%, var(--text) 80%);
  background-size: 200% 100%; -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: sheen 6s linear infinite;
}
@keyframes sheen { to { background-position: -200% 0; } }
```
Шрифты подключай через Google Fonts с `display=swap` и `preconnect`; всегда оставляй системный фолбэк.

### Поверхности, зерно и свечение
```css
.card {
  background: var(--bg-elev); border: 1px solid var(--line); border-radius: var(--radius-lg);
  padding: var(--space-8); position: relative; overflow: hidden;
  transition: border-color var(--dur) var(--ease-out), transform var(--dur) var(--ease-out);
}
.card:hover { border-color: var(--line-strong); }

/* Плёночное зерно поверх всей страницы: SVG-шум без картинок */
body::after {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 100; opacity: 0.06;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

/* Мягкое свечение за героем */
.hero { position: relative; isolation: isolate; }
.hero::before {
  content: ""; position: absolute; inset: -20% -10% auto; height: 80%; z-index: -1;
  background: radial-gradient(50% 50% at 50% 40%, color-mix(in srgb, var(--accent) 22%, transparent), transparent 70%);
  filter: blur(40px);
}

/* Сетка-фон, гаснущая к краям */
.grid-bg {
  background-image:
    linear-gradient(var(--line) 1px, transparent 1px),
    linear-gradient(90deg, var(--line) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse at center, #000 30%, transparent 75%);
}

/* Стекло для липкой шапки */
.glass {
  background: color-mix(in srgb, var(--bg) 70%, transparent);
  backdrop-filter: blur(14px) saturate(140%); -webkit-backdrop-filter: blur(14px) saturate(140%);
  border-bottom: 1px solid var(--line);
}
```

### Сетки
- Витрина компонентов: `display:grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr)); gap: 20px;`.
- Бенто-раскладка: 6 колонок, крупные карточки `grid-column: span 4`, мелкие `span 2`, на мобильном всё `span 6`.
- Вертикальный ритм секций: `padding-block: clamp(64px, 12vw, 160px)`.
- Боковой отступ на телефоне 16px, без горизонтального скролла (проверяй ширину 360px).

### Контрольный список перед сдачей
1. Контраст текста не ниже WCAG AA (кремовый на `#171615` проходит, `--text-faint` только для подписей ≥ 13px).
2. Акцент встречается на экране не больше 2–3 раз.
3. У каждого интерактивного элемента есть `:hover`, `:active`, `:focus-visible` и `disabled`.
4. Никаких чужих логотипов, фото и текстов: стиль воспроизводится собственным кодом.
5. Страница работает без JS (контент виден), JS только улучшает.

### Формат вывода
- Один файл `index.html` (или `index.html` + `styles.css` + `app.js`), токены в `:root` в начале CSS.
- Короткий список применённых приёмов и где в коде их менять.
