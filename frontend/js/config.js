// Where the Minbar backend lives. Normally the pages are served by FastAPI itself
// (same origin). When they are opened from a separate static dev server such as
// VS Code Live Server, add ?api=http://127.0.0.1:8765 once; it is kept for the tab.
(function () {
  const KEY = 'minbar.api';
  let base = '';
  try {
    const param = new URLSearchParams(location.search).get('api');
    if (param !== null) {
      if (/^https?:\/\/[^/]+$/i.test(param.replace(/\/+$/, ''))) sessionStorage.setItem(KEY, param.replace(/\/+$/, ''));
      else sessionStorage.removeItem(KEY);
    }
    base = sessionStorage.getItem(KEY) || '';
  } catch {}
  const meta = document.querySelector('meta[name="minbar-api"]');
  base = base || (meta && meta.content) || location.origin;
  window.MINBAR = {
    api: base,
    ws: base.replace(/^http/i, 'ws'),
    url: path => base + path,
    wsUrl: path => base.replace(/^http/i, 'ws') + path,
    offlineHint: 'تعذّر الوصول إلى خادم منبر. افتح الصفحة من الخادم نفسه (مثل http://127.0.0.1:8000/broadcast)، أو أضف ?api=http://127.0.0.1:8765 إلى الرابط.',
  };
})();
