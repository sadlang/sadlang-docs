// ============================================================================
// لافتة القناة (مستقرّ / القادم) — تُحقَن أعلى كلّ صفحة.
// هذه النسخة المحايدة للتطوير المحلّيّ (mdbook serve)؛ يستبدلها سير النشر
// (.github/workflows/deploy.yml) بنسخة خاصّة بكلّ قناة قبل البناء.
// ============================================================================
(function () {
  var bar = document.createElement("div");
  bar.dir = "rtl";
  bar.style.cssText =
    "background:#0b7285;color:#fff;text-align:center;padding:6px 10px;font-size:.9em;";
  bar.innerHTML =
    "نسخة تطوير محلّيّة — قناتا «المستقرّ» و«القادم» تظهران عند النشر على الموقع.";
  document.body.insertBefore(bar, document.body.firstChild);
})();
