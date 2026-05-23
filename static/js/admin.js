/* =====================================
   Local RAG — Admin UI (v2)
   ===================================== */

const AdminAuth = {
  requireAdmin() {
    if (!Auth.isLoggedIn()) {
      window.location.href = '/login';
      return false;
    }
    if (!Auth.isAdmin()) {
      Toast.error('Akses ditolak — admin only');
      setTimeout(() => window.location.href = '/', 1500);
      return false;
    }
    return true;
  }
};

const Admin = {
  async loadDashboard() {
    try {
      const resp = await API.get('/admin/dashboard');
      const s = resp.data.stats;
      const v = resp.data.vector_store;

      document.getElementById('statUsers').textContent = s.total_users;
      document.getElementById('statUsersSub').textContent =
        `${s.active_users} aktif · ${s.admin_users} admin`;
      document.getElementById('statDocs').textContent = s.total_documents;
      document.getElementById('statDocsSub').textContent = `${s.shared_documents} shared`;
      document.getElementById('statQueries').textContent = s.total_queries;
      document.getElementById('statQueriesSub').textContent =
        `${s.queries_with_conflict} dengan konflik`;
      document.getElementById('statConflicts').textContent = s.total_conflicts_logged;

      document.getElementById('vsTotal').textContent = v.total_vectors;
      document.getElementById('vsDim').textContent = v.dimension;
      document.getElementById('vsModel').textContent = v.model;

      await this.loadQueries();
    } catch (e) {
      Toast.error('Gagal load dashboard: ' + e.message);
    }
  },

  async loadQueries() {
    const tbody = document.getElementById('queryTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" class="muted center">Loading...</td></tr>';
    try {
      const resp = await API.get('/admin/queries?limit=50');
      const queries = resp.data.queries || [];
      if (queries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="muted center">Belum ada query.</td></tr>';
        return;
      }
      tbody.innerHTML = '';
      queries.forEach(q => {
        const tr = document.createElement('tr');
        const confPct = q.confidence != null ? Math.round(q.confidence * 100) : null;
        const confBadge = confPct != null ? this._confidenceBadge(confPct) : '-';
        const conflictBadge = q.has_conflict
          ? '<span class="badge badge-warn">YA</span>'
          : '<span class="badge badge-ok">TIDAK</span>';
        tr.innerHTML = `
          <td>${this._fmtTime(q.created_at)}</td>
          <td><span class="badge badge-neutral">user #${q.user_id}</span></td>
          <td>${this._escape(q.query_text).substring(0, 100)}</td>
          <td>${confBadge}</td>
          <td>${conflictBadge}</td>
          <td><code>${q.execution_time?.toFixed(0) || '-'}ms</code></td>`;
        tbody.appendChild(tr);
      });
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" class="muted">Gagal: ${e.message}</td></tr>`;
    }
  },

  _confidenceBadge(pct) {
    let cls = 'badge-err';
    if (pct >= 70) cls = 'badge-ok';
    else if (pct >= 40) cls = 'badge-warn';
    return `<span class="badge ${cls}">${pct}%</span>`;
  },

  async loadUsers() {
    const tbody = document.getElementById('userTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="muted center">Loading...</td></tr>';
    try {
      const resp = await API.get('/admin/users');
      const users = resp.data.users || [];
      tbody.innerHTML = '';
      if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="muted center">Tidak ada user.</td></tr>';
        return;
      }
      const me = Auth.getUser();
      users.forEach(u => {
        const tr = document.createElement('tr');
        const roleBadge = u.role === 'admin'
          ? '<span class="badge badge-info">admin</span>'
          : '<span class="badge badge-neutral">user</span>';
        const statusBadge = u.is_active
          ? '<span class="badge badge-ok">active</span>'
          : '<span class="badge badge-err">disabled</span>';
        const canDelete = u.id !== me?.id;
        tr.innerHTML = `
          <td><code>#${u.id}</code></td>
          <td><strong>${this._escape(u.username)}</strong></td>
          <td>${this._escape(u.email || '-')}</td>
          <td>${roleBadge}</td>
          <td>${statusBadge}</td>
          <td class="muted small">${this._fmtTime(u.created_at)}</td>
          <td>${canDelete
            ? `<button class="btn btn-danger btn-small" data-user-id="${u.id}">Hapus</button>`
            : '<span class="muted small">— anda —</span>'}</td>`;
        tbody.appendChild(tr);
      });
      tbody.querySelectorAll('button[data-user-id]').forEach(btn => {
        btn.addEventListener('click', () => Admin.deleteUser(btn.dataset.userId));
      });
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7" class="muted">Gagal: ${e.message}</td></tr>`;
    }
  },

  async createUser(event) {
    event.preventDefault();
    const username = document.getElementById('newUsername').value.trim();
    const email = document.getElementById('newEmail').value.trim() || null;
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newRole').value;
    try {
      await API.post('/admin/users', { username, email, password, role });
      Toast.success(`User "${username}" dibuat (role: ${role}).`);
      document.getElementById('createUserForm').reset();
      await Admin.loadUsers();
    } catch (e) {
      Toast.error('Gagal create user: ' + e.message);
    }
  },

  async deleteUser(userId) {
    if (!confirm(`Hapus user #${userId}? Semua dokumen + query history user ini ikut terhapus.`)) return;
    try {
      await API.delete(`/admin/users/${userId}`);
      Toast.success(`User #${userId} dihapus.`);
      await Admin.loadUsers();
    } catch (e) {
      Toast.error('Gagal: ' + e.message);
    }
  },

  async loadAllDocuments() {
    const tbody = document.getElementById('docTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="muted center">Loading...</td></tr>';
    try {
      const resp = await API.get('/admin/documents');
      const docs = resp.data.documents || [];
      tbody.innerHTML = '';
      if (docs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="muted center">Belum ada dokumen.</td></tr>';
        return;
      }
      docs.forEach(d => {
        const tr = document.createElement('tr');
        const sharedBadge = d.is_shared
          ? '<span class="badge badge-info">SHARED</span>'
          : '<span class="badge badge-neutral">private</span>';
        tr.innerHTML = `
          <td><code>#${d.id}</code></td>
          <td><strong>${this._escape(d.filename)}</strong></td>
          <td>user #${d.user_id}</td>
          <td><code>${d.word_count}</code></td>
          <td>${sharedBadge}</td>
          <td class="muted small">${this._fmtTime(d.created_at)}</td>
          <td><button class="btn btn-danger btn-small" data-doc-id="${d.id}">Hapus</button></td>`;
        tbody.appendChild(tr);
      });
      tbody.querySelectorAll('button[data-doc-id]').forEach(btn => {
        btn.addEventListener('click', () => Admin.deleteDoc(btn.dataset.docId));
      });
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7" class="muted">Gagal: ${e.message}</td></tr>`;
    }
  },

  async deleteDoc(docId) {
    if (!confirm(`Hapus dokumen #${docId}?`)) return;
    try {
      await API.delete(`/api/document/${docId}`);
      Toast.success(`Dokumen #${docId} dihapus.`);
      await Admin.loadAllDocuments();
    } catch (e) {
      Toast.error('Gagal: ' + e.message);
    }
  },

  _fmtTime(iso) {
    if (!iso) return '-';
    try {
      const d = new Date(iso);
      return d.toLocaleString('id-ID', {
        day: '2-digit', month: 'short',
        hour: '2-digit', minute: '2-digit'
      });
    } catch (e) { return iso; }
  },
  _escape(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
};
