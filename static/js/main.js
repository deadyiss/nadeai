// ─── TOAST ───
function toast(msg, type = 'info') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = type === 'error' ? 'show toast-error' : 'show';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 2800);
}

// ─── CTRL+ENTER for QA page ───
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 'Enter') {
    const form = document.getElementById('qa-form');
    if (form) form.submit();
  }
});

// ─── Sidebar drawer (mobile) + collapse (desktop) ───
(function () {
  const body = document.body;
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-nav]');
    if (!el) return;
    const action = el.dataset.nav;
    if (action === 'open')      body.classList.add('nav-open');
    else if (action === 'close') body.classList.remove('nav-open');
    else if (action === 'collapse') body.classList.add('nav-collapsed');
    else if (action === 'show')  body.classList.remove('nav-collapsed');
  });
  // Tapping a menu link closes the mobile drawer
  document.addEventListener('click', (e) => {
    if (e.target.closest('.sidebar-item') && body.classList.contains('nav-open')) {
      body.classList.remove('nav-open');
    }
  });
  // Esc closes the drawer
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') body.classList.remove('nav-open');
  });
})();

// ─── Upload drag-over highlight ───
(function () {
  const zone = document.querySelector('.upload-zone');
  if (!zone) return;
  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const inp = document.getElementById('file-input');
    if (inp && e.dataTransfer.files.length) {
      inp.files = e.dataTransfer.files;
      const titleEl = document.getElementById('upload-title');
      if (titleEl) titleEl.textContent = e.dataTransfer.files[0].name;
    }
  });
})();
