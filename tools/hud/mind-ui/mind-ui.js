/* Mind UI — собрано mindkit design js, не править вручную */
(function () {
  if (window.__mindUI) return; window.__mindUI = true;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  // 3D: карточка поворачивается за курсором
  document.addEventListener('pointermove', function (e) {
    if (reduce) return;
    var el = e.target.closest && e.target.closest('[data-mt-tilt]');
    if (!el) return;
    var r = el.getBoundingClientRect();
    var x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
    el.style.setProperty('--mt-rx', (-y * 6).toFixed(2) + 'deg');
    el.style.setProperty('--mt-ry', (x * 6).toFixed(2) + 'deg');
  });
  document.addEventListener('pointerout', function (e) {
    var el = e.target.closest && e.target.closest('[data-mt-tilt]');
    if (el && !el.contains(e.relatedTarget)) { el.style.removeProperty('--mt-rx'); el.style.removeProperty('--mt-ry'); }
  });
  // Bounce по клику
  document.addEventListener('click', function (e) {
    if (reduce) return;
    var el = e.target.closest && e.target.closest('.mt-btn, .mt-icon-btn, [data-mt-bounce]');
    if (!el) return;
    el.classList.remove('mt-popping'); void el.offsetWidth; el.classList.add('mt-popping');
  }, true);
  // Иконка по имени: MindUI.icon('inbox') → <i class="mi mi-inbox">
  window.MindUI = { icon: function (name, cls) {
    var i = document.createElement('i'); i.className = 'mi mi-' + name + (cls ? ' ' + cls : '');
    i.setAttribute('aria-hidden', 'true'); return i; } };
})();
