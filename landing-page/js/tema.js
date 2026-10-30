(function () {
  var tema = 'dark';
  try { tema = localStorage.getItem('horus_theme') || 'dark'; } catch (e) {  }
  document.documentElement.setAttribute('data-theme', tema);
})();
