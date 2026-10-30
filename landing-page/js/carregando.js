(function () {
  var tela = document.getElementById('carregando');
  if (!tela) return;

  var TEXTOS = {
    pt: { carregando: 'Carregando o Astra', abrindo: 'Abrindo o Astra', voltando: 'Voltando para a home' },
    en: { carregando: 'Loading Astra', abrindo: 'Opening Astra', voltando: 'Going back home' },
    es: { carregando: 'Cargando Astra', abrindo: 'Abriendo Astra', voltando: 'Volviendo al inicio' },
  };
  var idioma = 'pt';
  try { idioma = (localStorage.getItem('astra_idioma') || 'pt').slice(0, 2); } catch (e) {  }
  var t = TEXTOS[idioma] || TEXTOS.pt;
  var estado = tela.querySelector('.cg-estado');
  var reduzir = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DURACAO = reduzir ? 300 : 2600;
  var quadro = null;

  function animar(depois) {
    cancelAnimationFrame(quadro);
    var inicio = performance.now();
    (function passo(agora) {
      var x = Math.min(1, (agora - inicio) / DURACAO);
      var p = x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
      tela.style.setProperty('--p', p.toFixed(4));
      if (x < 1) quadro = requestAnimationFrame(passo);
      else if (depois) depois();
    })(inicio);
  }
  function mostrar(modo, depois) {
    estado.textContent = t[modo] || t.carregando;
    tela.classList.add('ativo');
    animar(depois);
  }
  function esconder() {
    document.documentElement.classList.remove('cg-saindo');
    tela.classList.remove('ativo', 'sem-fade');
  }
  function revelar() {
    document.documentElement.classList.remove('cg-escondido');
    esconder();
  }
  function ir(url, modo) {
    document.documentElement.classList.add('cg-saindo');
    mostrar(modo, function () {
      try { sessionStorage.setItem('astra_transicao', modo || 'carregando'); } catch (e) {  }
      location.href = url;
    });
  }
  window.AstraCarregando = { mostrar: mostrar, esconder: esconder, ir: ir };

  function modoDeEntrada(tipo) {
    var naPaginaInicial = location.pathname === '/';
    return naPaginaInicial && tipo === 'back_forward' ? 'voltando' : 'carregando';
  }
  var naHome = tela.hasAttribute('data-entrada');
  var modoDaTransicao = null;
  try { modoDaTransicao = sessionStorage.getItem('astra_transicao'); sessionStorage.removeItem('astra_transicao'); } catch (e) {  }
  var chegouPorTransicao = !!modoDaTransicao;

  if (chegouPorTransicao) {
    estado.textContent = t[modoDaTransicao] || t.carregando;
    tela.style.setProperty('--p', '1');
    tela.classList.add('ativo', 'sem-fade');
    document.documentElement.classList.add('cg-escondido');
    var revelou = false;
    var revelarUmaVez = function () { if (!revelou) { revelou = true; revelar(); } };
    document.addEventListener('DOMContentLoaded', function () { setTimeout(revelarUmaVez, 0); });
    setTimeout(revelarUmaVez, 900);
  } else if (naHome) {
    var nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || {};
    if (nav.type === 'reload' || nav.type === 'back_forward') {
      tela.classList.add('sem-fade');
      document.documentElement.classList.add('cg-escondido');
      mostrar(modoDeEntrada(nav.type), function () { setTimeout(revelar, 150); });
    }
  }
  addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    if (naHome) {
      document.documentElement.classList.add('cg-escondido');
      mostrar(modoDeEntrada('back_forward'), function () { setTimeout(revelar, 150); });
    }
    else esconder();
  });
})();
