document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('[data-menu-toggle]');
  const sidebar = document.querySelector('[data-sidebar]');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (event) => {
      if (!sidebar.classList.contains('open')) return;
      if (sidebar.contains(event.target) || toggle.contains(event.target)) return;
      sidebar.classList.remove('open');
    });
  }

  document.querySelectorAll('a.btn-danger, form[data-confirm]').forEach((element) => {
    element.addEventListener('click', (event) => {
      const message = element.dataset.confirm || 'Voulez-vous vraiment continuer ? Cette action est irréversible.';
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });
});
