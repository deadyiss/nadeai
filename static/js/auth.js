/* =====================================
   Local RAG — Auth & API client (v2)
   ===================================== */

const Auth = {
  KEY_TOKEN: 'rag_token',
  KEY_USER: 'rag_user',

  getToken() { return localStorage.getItem(this.KEY_TOKEN); },
  setToken(t) { localStorage.setItem(this.KEY_TOKEN, t); },
  clearToken() {
    localStorage.removeItem(this.KEY_TOKEN);
    localStorage.removeItem(this.KEY_USER);
  },
  getUser() {
    const raw = localStorage.getItem(this.KEY_USER);
    return raw ? JSON.parse(raw) : null;
  },
  setUser(u) { localStorage.setItem(this.KEY_USER, JSON.stringify(u)); },
  isLoggedIn() { return !!this.getToken(); },
  isAdmin() {
    const u = this.getUser();
    return u && u.role === 'admin';
  },
  async logout() {
    const token = this.getToken();
    if (token) {
      try { await API.post('/auth/logout', {}); } catch (e) {}
    }
    this.clearToken();
    window.location.href = '/login';
  }
};

const API = {
  async _fetch(path, opts = {}, withAuth = true) {
    const headers = opts.headers || {};
    if (withAuth) {
      const token = Auth.getToken();
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    if (opts.body && !(opts.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const resp = await fetch(path, { ...opts, headers });
    let data;
    try {
      data = await resp.json();
    } catch (e) {
      throw new Error(`Server returned non-JSON (status ${resp.status})`);
    }

    if (!resp.ok) {
      if (resp.status === 401 && withAuth) {
        Auth.clearToken();
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
      }
      throw new Error(data?.error?.message || `HTTP ${resp.status}`);
    }
    return data;
  },
  get(path, withAuth = true) {
    return this._fetch(path, { method: 'GET' }, withAuth);
  },
  post(path, body, withAuth = true) {
    const opts = { method: 'POST' };
    if (body instanceof FormData) opts.body = body;
    else opts.body = JSON.stringify(body);
    return this._fetch(path, opts, withAuth);
  },
  delete(path, withAuth = true) {
    return this._fetch(path, { method: 'DELETE' }, withAuth);
  }
};

const Toast = {
  _icons: {
    success: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    error:   '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    warn:    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    info:    '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  },
  show(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    if (!container) { console.log(`[${type}] ${message}`); return; }
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span class="toast-icon">${this._icons[type] || this._icons.info}</span><span>${this._escape(message)}</span>`;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.25s';
      setTimeout(() => el.remove(), 250);
    }, duration);
  },
  _escape(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
  success(m) { this.show(m, 'success'); },
  error(m)   { this.show(m, 'error', 5000); },
  warn(m)    { this.show(m, 'warn'); },
  info(m)    { this.show(m, 'info'); },
};

/* ---- Modal confirm ---- */
const Modal = {
  confirm({ icon = '🗑️', title = 'Konfirmasi', body = '', confirmText = 'Ya, lanjutkan', cancelText = 'Batal', danger = false } = {}) {
    return new Promise(resolve => {
      const backdrop = document.createElement('div');
      backdrop.className = 'modal-backdrop';
      backdrop.innerHTML = `
        <div class="modal" role="dialog" aria-modal="true">
          <div class="modal-icon">${icon}</div>
          <div class="modal-title">${title}</div>
          <div class="modal-body">${body}</div>
          <div class="modal-actions">
            <button class="btn btn-ghost" id="_modalCancel">${cancelText}</button>
            <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="_modalConfirm">${confirmText}</button>
          </div>
        </div>`;
      document.body.appendChild(backdrop);
      requestAnimationFrame(() => backdrop.classList.add('open'));
      const close = (val) => {
        backdrop.classList.remove('open');
        setTimeout(() => backdrop.remove(), 200);
        resolve(val);
      };
      backdrop.querySelector('#_modalConfirm').onclick = () => close(true);
      backdrop.querySelector('#_modalCancel').onclick  = () => close(false);
      backdrop.addEventListener('click', e => { if (e.target === backdrop) close(false); });
    });
  }
};

/* Global init: sidebar visibility + active nav state */
document.addEventListener('DOMContentLoaded', () => {
  const isLogged = Auth.isLoggedIn();
  const isAdmin = Auth.isAdmin();
  const user = Auth.getUser();

  // Show admin-only nav items
  document.querySelectorAll('.admin-only').forEach(el => {
    if (isAdmin) el.classList.remove('hidden');
    else el.classList.add('hidden');
  });

  // App shell vs Auth guard
  const appShell = document.getElementById('appShell');
  const authGuard = document.getElementById('authGuard');
  if (appShell && authGuard) {
    if (isLogged) {
      appShell.classList.remove('hidden');
      authGuard.classList.add('hidden');
    } else {
      appShell.classList.add('hidden');
      authGuard.classList.remove('hidden');
    }
  }

  // User card in sidebar
  if (user) {
    const navName = document.getElementById('navUserName');
    const navRole = document.getElementById('navUserRole');
    const avatar = document.getElementById('userAvatar');
    if (navName) navName.textContent = user.username;
    if (navRole) navRole.textContent = user.role;
    if (avatar)  avatar.textContent = (user.username || '?').charAt(0).toUpperCase();
  }

  // Mark active nav
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    const route = item.dataset.route;
    if (!route) return;
    if (path === route ||
        (route !== '/' && path.startsWith(route))) {
      item.classList.add('active');
    }
  });

  // Logout button
  const logoutBtn = document.getElementById('btnLogout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => Auth.logout());
  }
});
