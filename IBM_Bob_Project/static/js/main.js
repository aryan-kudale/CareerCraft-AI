/* ============================================================
   CareerCraft AI — Main JavaScript
   ============================================================ */

// ── Dark Mode ──────────────────────────────────────────────────
(function initTheme() {
  const saved = localStorage.getItem('cc-theme') || 'light';
  document.documentElement.setAttribute('data-bs-theme', saved);
  updateThemeIcon(saved);
})();

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (!icon) return;
  icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
}

document.addEventListener('DOMContentLoaded', function () {

  // ── Bootstrap tooltips ──────────────────────────────────────
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltips.forEach(el => new bootstrap.Tooltip(el, {placement: 'bottom'}));

  // ── Dark mode toggle ────────────────────────────────────────
  const toggleBtn = document.getElementById('themeToggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      const html = document.documentElement;
      const next = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-bs-theme', next);
      localStorage.setItem('cc-theme', next);
      updateThemeIcon(next);
    });
  }

  // ── Animate elements on scroll ──────────────────────────────
  const animateOnScroll = new IntersectionObserver(
    (entries) => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate__animated', 'animate__fadeInUp');
        animateOnScroll.unobserve(entry.target);
      }
    }),
    {threshold: 0.1}
  );
  document.querySelectorAll('.feature-card').forEach(el => animateOnScroll.observe(el));

  // ── Auto-dismiss alerts ──────────────────────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 4000);
  });

  // ── Navbar scroll shadow ─────────────────────────────────────
  const nav = document.getElementById('mainNav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.style.boxShadow = window.scrollY > 10
        ? '0 2px 16px rgba(0,0,0,.12)'
        : '0 1px 0 var(--cc-nav-border)';
    }, {passive: true});
  }

  // ── Status badge polling (every 60s) ─────────────────────────
  if (document.getElementById('statusBadge')) {
    setTimeout(pollStatus, 5000);
    setInterval(pollStatus, 60000);
  }

});

async function pollStatus() {
  try {
    const r = await fetch('/api/status', {cache: 'no-store'});
    if (!r.ok) return;
    const d = await r.json();
    updateAllStatusBadges(d.status, d.message);
  } catch (e) { /* network error – silent */ }
}

function updateAllStatusBadges(status, message) {
  const classMap = {
    ok: 'watson-ok',
    no_credentials: 'watson-demo',
    error: 'watson-error',
    unchecked: 'watson-demo',
  };
  const labelMap = {
    ok: 'IBM Granite Live',
    no_credentials: 'Demo Mode',
    error: 'Connection Error',
    unchecked: 'Checking…',
  };
  const cls   = classMap[status] || 'watson-demo';
  const label = labelMap[status] || 'Unknown';

  document.querySelectorAll('.watson-badge').forEach(el => {
    el.className = `watson-badge ${cls}`;
    const lbl = el.querySelector('.status-label');
    if (lbl) lbl.textContent = label;
    if (el.dataset.bsOriginalTitle !== undefined) {
      el.setAttribute('data-bs-original-title', message);
    }
  });

  const navBadge = document.getElementById('statusBadge');
  if (navBadge) navBadge.title = message;
}

// ── Expose for inline scripts ──────────────────────────────────
window.CareerCraft = { pollStatus, updateAllStatusBadges };
