/* Мобильное меню: кнопка-«бургер» открывает/закрывает меню (стили — в home.css / inner.css) */
(function () {
  var btn = document.querySelector('.burger');
  if (!btn) return;
  var body = document.body;
  function set(open) {
    body.classList.toggle('menu-open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  btn.addEventListener('click', function () { set(!body.classList.contains('menu-open')); });
  document.querySelectorAll('#siteNav a').forEach(function (a) {
    a.addEventListener('click', function () { set(false); });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  var mq = window.matchMedia('(max-width:860px)');
  var close = function () { set(false); };
  if (mq.addEventListener) mq.addEventListener('change', close); else if (mq.addListener) mq.addListener(close);
})();
