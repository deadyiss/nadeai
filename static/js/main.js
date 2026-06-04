<<<<<<< HEAD
/* =====================================
   Local RAG — Main UI (query + upload)
   ===================================== */

const Main = {
  _loadingMessages: [
    'Mencari dokumen relevan...',
    'Memeriksa konflik antar dokumen...',
    'Memproses jawaban dengan LLM...',
    'Memverifikasi klaim (hallucination check)...',
    'Menyusun hasil akhir...'
  ],
  _loadingTimer: null,
  _loadingIdx: 0,
  _selectedFile: null,
  _allDocs: [],
  _currentPage: 1,
  _pageSize: 5,

  init() {
    if (!Auth.isLoggedIn()) return;

    // Query
    document.getElementById('btnQuery')?.addEventListener('click', () => this.runQuery());
    document.getElementById('queryInput')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) this.runQuery();
    });

    // Upload zone — click + drag/drop
    const zone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    if (zone && fileInput) {
      zone.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', () => {
        const f = fileInput.files[0];
        if (f) this._selectFile(f);
      });
      ['dragenter', 'dragover'].forEach(evt => {
        zone.addEventListener(evt, e => {
          e.preventDefault(); e.stopPropagation();
          zone.classList.add('dragover');
        });
      });
      ['dragleave', 'drop'].forEach(evt => {
        zone.addEventListener(evt, e => {
          e.preventDefault(); e.stopPropagation();
          zone.classList.remove('dragover');
        });
      });
      zone.addEventListener('drop', e => {
        const f = e.dataTransfer.files[0];
        if (f) {
          fileInput.files = e.dataTransfer.files;
          this._selectFile(f);
        }
      });
    }

    document.getElementById('btnClearFile')?.addEventListener('click', (e) => {
      e.stopPropagation();
      this._clearFile();
    });
    document.getElementById('btnUpload')?.addEventListener('click', () => this.uploadDocument());
    document.getElementById('btnRefreshDocs')?.addEventListener('click', () => this.loadDocuments());

    // Result tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => this._switchTab(btn.dataset.tab));
    });

    this.loadDocuments();
  },

  _selectFile(f) {
    this._selectedFile = f;
    document.getElementById('uploadPrompt').classList.add('hidden');
    const sel = document.getElementById('uploadSelected');
    sel.classList.remove('hidden');
    document.getElementById('selectedFileName').textContent =
      `${f.name} (${this._formatSize(f.size)})`;
    document.getElementById('btnUpload').disabled = false;
  },

  _clearFile() {
    this._selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('uploadPrompt').classList.remove('hidden');
    document.getElementById('uploadSelected').classList.add('hidden');
    document.getElementById('btnUpload').disabled = true;
  },

  _formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  },

  _switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
      c.classList.toggle('active', c.dataset.tab === tabName);
    });
  },

  _startLoading() {
    this._loadingIdx = 0;
    const loadingText = document.getElementById('loadingText');
    if (loadingText) loadingText.textContent = this._loadingMessages[0];
    this._loadingTimer = setInterval(() => {
      if (this._loadingIdx < this._loadingMessages.length - 1) {
        this._loadingIdx++;
        if (loadingText) loadingText.textContent = this._loadingMessages[this._loadingIdx];
      }
      // stop advancing at last message — no loop back to start
    }, 2500);
  },
  _stopLoading() {
    if (this._loadingTimer) {
      clearInterval(this._loadingTimer);
      this._loadingTimer = null;
    }
  },

  async runQuery() {
    const input = document.getElementById('queryInput');
    const query = input.value.trim();
    if (!query) {
      Toast.warn('Tulis pertanyaan terlebih dahulu.');
      input.focus();
      return;
    }
    const docCount = document.querySelectorAll('#docList li:not(.doc-empty)').length;
    const topK = docCount <= 3 ? 3 : docCount <= 10 ? 5 : 7;
    const btn = document.getElementById('btnQuery');
    const result = document.getElementById('queryResult');
    const loading = document.getElementById('queryLoading');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span><span>Memproses...</span>';
    result.classList.add('hidden');
    loading.classList.remove('hidden');
    this._startLoading();

    try {
      const resp = await API.post('/api/query', { query, top_k: topK });
      this.renderResult(resp.data);
      loading.classList.add('hidden');
      result.classList.remove('hidden');
      result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
      loading.classList.add('hidden');
      Toast.error('Query gagal: ' + e.message);
    } finally {
      this._stopLoading();
      btn.disabled = false;
      btn.innerHTML =
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg><span>Tanya</span>';
    }
  },

  renderResult(data) {
    // Answer
    document.getElementById('answerText').textContent = data.answer || '(tidak ada jawaban)';

    // Confidence ring
    const confPct = Math.round((data.confidence || 0) * 100);
    const ring = document.getElementById('confRing');
    const circumference = 2 * Math.PI * 32;
    ring.style.strokeDashoffset = circumference - (confPct / 100) * circumference;
    document.getElementById('confText').textContent = confPct + '%';
    if (confPct >= 70)      ring.style.stroke = 'var(--success-500)';
    else if (confPct >= 40) ring.style.stroke = 'var(--warning-500)';
    else                    ring.style.stroke = 'var(--error-500)';

    // Hallucination badge
    const halluc = data.hallucination || { status: 'UNKNOWN' };
    const hBadge = document.getElementById('hallucBadge');
    hBadge.textContent = halluc.status;
    hBadge.className = 'badge badge-lg ' + (
      halluc.status === 'VERIFIED' ? 'badge-ok' :
      halluc.status === 'FLAGGED' ? 'badge-err' :
      halluc.status === 'NO_CLAIMS' ? 'badge-neutral' : 'badge-info'
    );
    document.getElementById('hallucScore').textContent =
      halluc.overall_score != null ? `score: ${halluc.overall_score}` : '';

    // Conflict badge
    const conflictCount = (data.conflict_details || []).length;
    const cBadge = document.getElementById('conflictBadge');
    if (data.has_conflict) {
      cBadge.textContent = 'DETECTED';
      cBadge.className = 'badge badge-lg badge-warn';
    } else {
      cBadge.textContent = 'NONE';
      cBadge.className = 'badge badge-lg badge-ok';
    }
    document.getElementById('conflictCount').textContent =
      conflictCount ? `${conflictCount} ditemukan` : 'tidak ada';

    // Sources tab
    const sourceList = document.getElementById('sourceList');
    const sources = data.sources || [];
    document.getElementById('sourceCount').textContent = sources.length;
    sourceList.innerHTML = '';
    if (sources.length === 0) {
      sourceList.innerHTML = '<li class="empty-list">Tidak ada dokumen sumber.</li>';
    } else {
      sources.forEach(src => {
        const li = document.createElement('li');
        li.innerHTML = `
          <span class="source-id">#${src.doc_id}</span>
          <span class="source-filename">${this._escape(src.filename)}</span>
          <span class="source-sim">sim ${src.similarity.toFixed(3)}</span>`;
        sourceList.appendChild(li);
      });
    }

    // Claims tab
    const claimList = document.getElementById('claimList');
    const claims = halluc.claims || [];
    document.getElementById('claimCount').textContent = claims.length;
    claimList.innerHTML = '';
    if (claims.length === 0) {
      claimList.innerHTML =
        '<div class="empty-list">Tidak ada klaim untuk diverifikasi (jawaban kosong atau berupa refusal).</div>';
    } else {
      claims.forEach(cl => {
        const verified = cl.status === 'VERIFIED';
        const div = document.createElement('div');
        div.className = 'claim-item ' + (verified ? 'verified' : 'flagged');
        div.innerHTML = `
          <div class="claim-text">
            <span class="claim-mark ${verified ? 'ok' : 'err'}">${verified ? '✓' : '✗'}</span>
            <span>${this._escape(cl.claim)}</span>
          </div>
          <div class="claim-meta">
            entail: ${cl.entailment ?? '-'} ·
            contradict: ${cl.contradiction ?? '-'} ·
            verdict: <strong>${cl.verdict || '-'}</strong> ·
            source: ${this._escape(cl.best_source || '-')}
          </div>`;
        claimList.appendChild(div);
      });
    }

    // Conflicts tab
    const conflictList = document.getElementById('conflictList');
    const conflicts = data.conflict_details || [];
    document.getElementById('conflictListCount').textContent = conflicts.length;
    conflictList.innerHTML = '';
    if (conflicts.length === 0) {
      conflictList.innerHTML = '<div class="empty-list">Tidak ditemukan konflik antar dokumen.</div>';
    } else {
      conflicts.forEach(c => {
        const div = document.createElement('div');
        div.className = 'conflict-item' + (c.severity === 'HIGH' ? ' severity-high' : '');
        div.innerHTML = `
          <div class="conflict-title">
            <span class="badge ${c.severity === 'HIGH' ? 'badge-err' : 'badge-warn'}">${c.severity}</span>
            ${this._escape(c.conflict_type)}
          </div>
          <div class="conflict-desc">${this._escape(c.description)}</div>
          <div class="conflict-docs">Affected: ${(c.affected_docs || []).join(', ')}</div>`;
        conflictList.appendChild(div);
      });
    }

    // Timing tab
    const tg = document.getElementById('timingGrid');
    const stages = data.stages || {};
    tg.innerHTML = `
      <div class="timing-cell"><span class="timing-label">Search</span><div class="timing-value">${stages.search_ms ?? '-'}ms</div></div>
      <div class="timing-cell"><span class="timing-label">Conflict</span><div class="timing-value">${stages.conflict_ms ?? '-'}ms</div></div>
      <div class="timing-cell"><span class="timing-label">LLM</span><div class="timing-value">${stages.llm_ms ?? '-'}ms</div></div>
      <div class="timing-cell"><span class="timing-label">Hallucination</span><div class="timing-value">${stages.hallucination_ms ?? '-'}ms</div></div>
      <div class="timing-cell"><span class="timing-label">Total</span><div class="timing-value">${data.execution_time_ms ?? '-'}ms</div></div>`;
  },

  async uploadDocument() {
    if (!this._selectedFile) {
      Toast.warn('Pilih file terlebih dahulu.');
      return;
    }
    const isShared = document.getElementById('isShared')?.checked || false;
    const btn = document.getElementById('btnUpload');
    const progress = document.getElementById('uploadProgress');

    const fd = new FormData();
    fd.append('file', this._selectedFile);
    fd.append('is_shared', isShared ? 'true' : 'false');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span><span>Uploading...</span>';
    progress.classList.remove('hidden');

    try {
      const resp = await API.post('/api/upload', fd);
      Toast.success(`Berhasil: ${resp.data.document.filename} (${resp.data.word_count} kata)`);
      this._clearFile();
      await this.loadDocuments();
    } catch (e) {
      Toast.error('Upload gagal: ' + e.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML =
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg><span>Upload & Index</span>';
      progress.classList.add('hidden');
    }
  },

  async loadDocuments() {
    const ul = document.getElementById('docList');
    if (!ul) return;
    try {
      const resp = await API.get('/api/documents');
      this._allDocs = resp.data.documents || [];
      this._currentPage = 1;
      this._renderDocPage();
    } catch (e) {
      ul.innerHTML = `<li class="empty-list">Gagal load: ${this._escape(e.message)}</li>`;
    }
  },

  _renderDocPage() {
    const ul = document.getElementById('docList');
    if (!ul) return;
    const docs = this._allDocs;
    ul.innerHTML = '';

    if (docs.length === 0) {
      ul.innerHTML = `<li class="doc-empty"><div class="empty-icon"><svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><p>Belum ada dokumen</p></li>`;
      document.getElementById('docPagination')?.remove();
      document.getElementById('docPageInfo')?.remove();
      return;
    }

    const total = docs.length;
    const totalPages = Math.ceil(total / this._pageSize);
    this._currentPage = Math.min(this._currentPage, totalPages);
    const start = (this._currentPage - 1) * this._pageSize;
    const pageDocs = docs.slice(start, start + this._pageSize);
    const me = Auth.getUser();

    pageDocs.forEach(d => {
      const li = document.createElement('li');
      const sharedBadge = d.is_shared ? '<span class="badge badge-info">SHARED</span>' : '';
      const isMine = d.user_id === me?.id;
      const ownerInfo = isMine ? 'milik Anda' : `user #${d.user_id}`;
      const canDelete = isMine || Auth.isAdmin();
      const chunkInfo = d.chunk_total > 1 ? ` · ${d.chunk_total} chunks` : '';
      li.innerHTML = `
        <div class="doc-icon"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
        <div class="doc-meta-block">
          <div class="doc-name">${this._escape(d.filename)} ${sharedBadge}</div>
          <div class="doc-info">#${d.id} · ${d.word_count} kata${chunkInfo} · ${ownerInfo}</div>
        </div>
        ${canDelete ? `<div class="doc-actions"><button class="btn btn-ghost btn-icon" data-doc-id="${d.id}" data-doc-name="${this._escape(d.filename)}" title="Hapus"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button></div>` : ''}`;
      ul.appendChild(li);
    });

    ul.querySelectorAll('button[data-doc-id]').forEach(btn => {
      btn.addEventListener('click', () => this.deleteDocument(btn.dataset.docId, btn.dataset.docName));
    });

    // Pagination
    let pag = document.getElementById('docPagination');
    let info = document.getElementById('docPageInfo');
    if (!pag) {
      pag = document.createElement('div');
      pag.id = 'docPagination';
      pag.className = 'pagination';
      ul.parentNode.appendChild(pag);
      info = document.createElement('div');
      info.id = 'docPageInfo';
      info.className = 'page-info';
      ul.parentNode.appendChild(info);
    }
    pag.innerHTML = '';
    info.textContent = '';

    if (totalPages <= 1) { pag.remove(); info.remove(); return; }

    info.textContent = `Menampilkan ${start + 1}–${Math.min(start + this._pageSize, total)} dari ${total} dokumen`;

    const addBtn = (label, page, disabled, active) => {
      const b = document.createElement('button');
      b.className = 'page-btn' + (active ? ' active' : '');
      b.textContent = label;
      b.disabled = disabled;
      if (!disabled && !active) b.onclick = () => { this._currentPage = page; this._renderDocPage(); };
      pag.appendChild(b);
    };

    addBtn('‹', this._currentPage - 1, this._currentPage === 1, false);
    for (let p = 1; p <= totalPages; p++) {
      if (totalPages > 7 && Math.abs(p - this._currentPage) > 2 && p !== 1 && p !== totalPages) {
        if (p === 2 || p === totalPages - 1) { const s = document.createElement('span'); s.textContent = '…'; s.style.padding = '0 4px'; pag.appendChild(s); }
        continue;
      }
      addBtn(p, p, false, p === this._currentPage);
    }
    addBtn('›', this._currentPage + 1, this._currentPage === totalPages, false);
  },

  async deleteDocument(docId, docName) {
    const ok = await Modal.confirm({
      icon: '🗑️',
      title: 'Hapus Dokumen',
      body: `Yakin ingin menghapus <strong>${docName || '#' + docId}</strong>?<br>Semua chunk dokumen ini akan dihapus permanen.`,
      confirmText: 'Ya, Hapus',
      cancelText: 'Batal',
      danger: true,
    });
    if (!ok) return;
    try {
      await API.delete(`/api/document/${docId}`);
      Toast.success('Dokumen berhasil dihapus.');
      await this.loadDocuments();
    } catch (e) {
      Toast.error('Gagal hapus: ' + e.message);
    }
  },

  _escape(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
};

document.addEventListener('DOMContentLoaded', () => Main.init());
=======
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
>>>>>>> 0c7befc (Final Revision)
