/* ══════════════════════════════════════════════════════════
   SocialHub — upload.js
   Handles drag-&-drop, file preview, caption counter,
   hashtag pills and schedule toggle.
══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Elements ──────────────────────────────────────────
  const dropzone    = document.getElementById('dropzone');
  const mediaInput  = document.getElementById('mediaInput');
  const previewGrid = document.getElementById('previewGrid');
  const captionArea = document.getElementById('captionArea');
  const captionCnt  = document.getElementById('captionCount');
  const hashInput   = document.getElementById('hashtagInput');
  const hashPills   = document.getElementById('hashtagPills');
  const schedulePicker = document.getElementById('schedulePicker');
  const scheduledAt = document.getElementById('scheduledAt');
  const submitLabel = document.getElementById('submitLabel');
  const submitBtn   = document.getElementById('submitBtn');

  // ── Drag & drop ───────────────────────────────────────
  dropzone?.addEventListener('click', () => mediaInput?.click());

  dropzone?.addEventListener('dragover', e => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone?.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

  dropzone?.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
  });

  mediaInput?.addEventListener('change', () => handleFiles(mediaInput.files));

  // ── File preview ──────────────────────────────────────
  let allFiles = [];   // DataTransfer to track files

  function handleFiles(fileList) {
    [...fileList].forEach(file => {
      if (!file.type.startsWith('video/') && !file.type.startsWith('image/')) return;
      if (allFiles.find(f => f.name === file.name && f.size === file.size)) return;
      allFiles.push(file);
      addPreview(file);
    });
    syncInput();
  }

  function addPreview(file) {
    const item = document.createElement('div');
    item.className = 'preview-item';
    item.dataset.name = file.name;
    item.dataset.size = file.size;

    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-btn';
    removeBtn.innerHTML = '✕';
    removeBtn.type = 'button';
    removeBtn.onclick = () => {
      allFiles = allFiles.filter(f => !(f.name === file.name && f.size === file.size));
      item.remove();
      syncInput();
    };

    if (file.type.startsWith('image/')) {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.onload = () => URL.revokeObjectURL(img.src);
      item.appendChild(img);
    } else {
      const video = document.createElement('video');
      video.src = URL.createObjectURL(file);
      video.muted = true;
      video.style.cssText = 'width:100%;height:100%;object-fit:cover;';
      item.appendChild(video);
    }

    item.appendChild(removeBtn);
    previewGrid?.appendChild(item);
  }

  function syncInput() {
    // Build a new FileList-like structure using DataTransfer
    if (!mediaInput) return;
    const dt = new DataTransfer();
    allFiles.forEach(f => dt.items.add(f));
    mediaInput.files = dt.files;

    // Update dropzone UI
    const inner = document.getElementById('dropzoneInner');
    if (inner) {
      inner.style.display = allFiles.length ? 'none' : 'block';
    }
  }

  // ── Caption counter ───────────────────────────────────
  captionArea?.addEventListener('input', () => {
    if (captionCnt) captionCnt.textContent = captionArea.value.length;
  });

  // ── Hashtag pills ──────────────────────────────────────
  hashInput?.addEventListener('keydown', e => {
    if ([' ', 'Enter', ','].includes(e.key)) {
      e.preventDefault();
      addHashtag(hashInput.value.trim());
    }
  });

  hashInput?.addEventListener('blur', () => {
    if (hashInput.value.trim()) addHashtag(hashInput.value.trim());
  });

  let hashtags = [];

  function addHashtag(tag) {
    if (!tag) return;
    tag = tag.replace(/^#+/, '').replace(/\s+/g, '');
    if (!tag || hashtags.includes(tag)) { hashInput.value = ''; return; }
    hashtags.push(tag);
    hashInput.value = '';
    renderHashtags();
  }

  function removeHashtag(tag) {
    hashtags = hashtags.filter(h => h !== tag);
    renderHashtags();
  }

  function renderHashtags() {
    if (!hashPills) return;
    hashPills.innerHTML = '';
    hashtags.forEach(tag => {
      const span = document.createElement('span');
      span.className = 'hashtag-pill';
      span.innerHTML = `#${tag} <span style="cursor:pointer;margin-left:2px" onclick="removeHashtag('${tag}')">×</span>`;
      hashPills.appendChild(span);
    });
    // Update hidden field
    const hiddenInput = document.querySelector('input[name="hashtags"]') || hashInput;
    hiddenInput.value = hashtags.map(h => '#' + h).join(' ');
  }

  // Make removeHashtag global
  window.removeHashtag = removeHashtag;

  // ── Schedule toggle ────────────────────────────────────
  window.toggleSchedule = function (radio) {
    if (!schedulePicker || !scheduledAt || !submitLabel) return;
    if (radio.value === 'schedule') {
      schedulePicker.style.display = 'block';
      submitLabel.textContent = 'Jadwalkan Post';
      // Default: 1 hour from now
      if (!scheduledAt.value) {
        const d = new Date(Date.now() + 3600_000);
        scheduledAt.value = d.toISOString().slice(0, 16);
      }
    } else {
      schedulePicker.style.display = 'none';
      submitLabel.textContent = 'Publish Sekarang';
    }
  };

  // ── Form validation ────────────────────────────────────
  document.getElementById('uploadForm')?.addEventListener('submit', e => {
    const checked = document.querySelectorAll('input[name="platform_accounts"]:checked');
    if (checked.length === 0) {
      e.preventDefault();
      alert('Pilih minimal satu platform untuk publish!');
      return;
    }
    if (allFiles.length === 0) {
      e.preventDefault();
      alert('Upload minimal satu file media!');
      return;
    }
    // Disable button to prevent double submit
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Memproses…';
    }
  });

});
