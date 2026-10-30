import * as THREE from './vendor/three/three.module.js';
import { RoomEnvironment } from './vendor/three/RoomEnvironment.js';

const $ = (s) => document.querySelector(s);
const reduzir = matchMedia('(prefers-reduced-motion: reduce)').matches;

const CHAVE_TEMA = 'horus_theme';
const aoMudarTema = [];
function temaClaro() {
  const t = document.documentElement.getAttribute('data-theme');
  return t === 'light' || (t === 'system' && matchMedia('(prefers-color-scheme: light)').matches);
}
function aplicarTema(t, gravar) {
  document.documentElement.setAttribute('data-theme', t);
  if (gravar) { try { localStorage.setItem(CHAVE_TEMA, t); } catch (e) {  } }
  aoMudarTema.forEach((f) => f());
}
$('#temaBotao').addEventListener('click', () => aplicarTema(temaClaro() ? 'dark' : 'light', true));
addEventListener('storage', (e) => { if (e.key === CHAVE_TEMA) aplicarTema(e.newValue || 'dark', false); });
matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => aoMudarTema.forEach((f) => f()));

const CHAVE_IDIOMA = 'astra_idioma';
let codigoIdioma = 'pt-BR';
try { codigoIdioma = localStorage.getItem(CHAVE_IDIOMA) || 'pt-BR'; } catch (e) {  }
const lingua = ['en', 'es'].includes(codigoIdioma.slice(0, 2)) ? codigoIdioma.slice(0, 2) : 'pt';
const TXT = {
  pt: null,
  en: {
    titulo: 'Astra — your AI for any question',
    faixa: '<b>New:</b> Astra is live — your AI for any question ↗',
    recursos: 'Features', exemplos: 'Examples', semCadastro: 'No sign-up ↗', abrir: 'OPEN ASTRA', menu: 'MENU',
    l1: 'PROGRAMMING', l2: 'STUDYING', l3: 'LANGUAGES', l4: 'AND MUCH MORE',
    sobre: 'ASK ANYTHING TO', h1a: 'Your AI for', h1b: 'any question',
    sub: 'An AI assistant that answers in your language. No sign-up: just open it and ask.',
    rolar: 'SCROLL', h2a: 'Everything you', h2b: 'need, in one chat',
    pergunta: 'QUESTION', exTipo: 'EXAMPLE QUESTION', experimente: 'Ask your own (Open Astra)',
    rotulos: ['HOME', 'FEATURES', 'EXAMPLES'],
    perguntas: ['What is the difference between inflation and deflation?', 'Explain photosynthesis in bullet points for tomorrow’s test.', 'Why does my Python code fail on line 2?', 'How do I order a coffee in Italian?'],
    recursosLista: ['Chat about any topic', 'Code review', 'Step-by-step error explanations', 'Code file attachments', 'Code blocks with “Copy”', 'Answers in bullet points', 'History saved in your browser', 'Incognito mode', 'Light and dark theme'],
    exemplosLista: [
      ['ECONOMICS', 'What is the difference between inflation and deflation? Explain with an everyday example.'],
      ['PROGRAMMING', 'Review this code and tell me why the comparison on line 2 fails.'],
      ['STUDYING', 'Explain photosynthesis in bullet points, as if it were for a test.'],
      ['LANGUAGES', 'How do I order a coffee in Italian? And how is it pronounced?'],
      ['HISTORY', 'Why did the French Revolution start? Summarize it in five points.'],
      ['MATH', 'How do I calculate compound interest? Show me the formula with an example.'],
      ['CAREER', 'How do I write a professional summary for my LinkedIn?'],
      ['DATABASES', 'What is the difference between INNER JOIN and LEFT JOIN in SQL?'],
      ['SCIENCE', 'How does a solar eclipse work? Explain it simply.'],
      ['SECURITY', 'What is SQL injection and how do I protect my site against it?'],
      ['WRITING', 'Revise this paragraph and make it clearer and more direct.'],
      ['JAVASCRIPT', 'What is the difference between let, const and var? When should I use each?'],
      ['HEALTH', 'How many hours of sleep does an adult need per night, on average?'],
      ['PYTHON', 'How do I read a CSV file in Python and sum one of the columns?'],
    ],
  },
  es: {
    titulo: 'Astra — tu IA para cualquier duda',
    faixa: '<b>Nuevo:</b> Astra ya está disponible — tu IA para cualquier duda ↗',
    recursos: 'Funciones', exemplos: 'Ejemplos', semCadastro: 'Sin registro ↗', abrir: 'ABRIR ASTRA', menu: 'MENÚ',
    l1: 'PROGRAMACIÓN', l2: 'ESTUDIOS', l3: 'IDIOMAS', l4: 'Y MUCHO MÁS',
    sobre: 'PREGÚNTALE CUALQUIER COSA A', h1a: 'Tu IA para', h1b: 'cualquier duda',
    sub: 'Asistente de IA que responde en tu idioma. Sin registro: solo ábrelo y pregunta.',
    rolar: 'DESLIZAR', h2a: 'Todo lo que', h2b: 'necesitas, en un solo chat',
    pergunta: 'PREGUNTA', exTipo: 'EJEMPLO DE PREGUNTA', experimente: 'Pregunta tú también (Abrir Astra)',
    rotulos: ['INICIO', 'FUNCIONES', 'EJEMPLOS'],
    perguntas: ['¿Cuál es la diferencia entre inflación y deflación?', 'Explica la fotosíntesis en puntos, para el examen de mañana.', '¿Por qué mi código Python da error en la línea 2?', '¿Cómo pido un café en italiano?'],
    recursosLista: ['Chat sobre cualquier tema', 'Revisión de código', 'Explicación de errores, paso a paso', 'Adjuntar archivos de código', 'Bloques de código con “Copiar”', 'Respuestas en puntos', 'Historial guardado en el navegador', 'Modo incógnito', 'Tema claro y oscuro'],
    exemplosLista: [
      ['ECONOMÍA', '¿Cuál es la diferencia entre inflación y deflación? Explícalo con un ejemplo cotidiano.'],
      ['PROGRAMACIÓN', 'Revisa este código y dime por qué la comparación en la línea 2 da error.'],
      ['ESTUDIOS', 'Explícame la fotosíntesis en puntos, como si fuera para un examen.'],
      ['IDIOMAS', '¿Cómo pido un café en italiano? ¿Y cómo se pronuncia?'],
      ['HISTORIA', '¿Por qué comenzó la Revolución Francesa? Resúmelo en cinco puntos.'],
      ['MATEMÁTICAS', '¿Cómo se calcula el interés compuesto? Muéstrame la fórmula con un ejemplo.'],
      ['CARRERA', '¿Cómo escribo un resumen profesional para mi LinkedIn?'],
      ['BASES DE DATOS', '¿Cuál es la diferencia entre INNER JOIN y LEFT JOIN en SQL?'],
      ['CIENCIA', '¿Cómo funciona un eclipse solar? Explícalo de forma sencilla.'],
      ['SEGURIDAD', '¿Qué es la inyección SQL y cómo protejo mi sitio contra ella?'],
      ['ESCRITURA', 'Revisa este párrafo y haz el texto más claro y directo.'],
      ['JAVASCRIPT', '¿Cuál es la diferencia entre let, const y var? ¿Cuándo usar cada uno?'],
      ['SALUD', '¿Cuántas horas de sueño necesita un adulto por noche, en promedio?'],
      ['PYTHON', '¿Cómo leo un archivo CSV en Python y sumo una de las columnas?'],
    ],
  },
}[lingua];
if (TXT) {
  document.documentElement.lang = codigoIdioma;
  document.title = TXT.titulo;
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = TXT[el.dataset.i18n]; });
  document.querySelectorAll('[data-i18n-html]').forEach((el) => { el.innerHTML = TXT[el.dataset.i18nHtml]; });
  document.querySelectorAll('.secao').forEach((s, i) => { s.dataset.rotulo = TXT.rotulos[i]; });
  $('#trilhoTexto').textContent = TXT.rotulos[0];
}
const botaoIdioma = $('#idiomaBotao');
const menuIdioma = $('#idiomaMenu');
botaoIdioma.textContent = lingua.toUpperCase();
menuIdioma.querySelectorAll('button').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.lang.slice(0, 2) === lingua)));
function abrirMenuIdioma(abrir) { menuIdioma.hidden = !abrir; botaoIdioma.setAttribute('aria-expanded', String(abrir)); }
botaoIdioma.addEventListener('click', (e) => { e.stopPropagation(); abrirMenuIdioma(menuIdioma.hidden); });
document.addEventListener('click', () => abrirMenuIdioma(false));
addEventListener('keydown', (e) => { if (e.key === 'Escape') abrirMenuIdioma(false); });
menuIdioma.addEventListener('click', (e) => {
  const b = e.target.closest('[data-lang]');
  if (!b) return;
  try { localStorage.setItem(CHAVE_IDIOMA, b.dataset.lang); } catch (erro) {  }
  location.reload();
});

const faixa = $('#faixa');
const nav = $('#nav');
let faixaFechada = false;
function atualizarTopo() {
  const recolher = faixaFechada || scrollY > 40;
  faixa.classList.toggle('recolhida', recolher);
  nav.classList.toggle('no-topo', recolher);
}
$('#faixaFechar').addEventListener('click', () => { faixaFechada = true; atualizarTopo(); });
addEventListener('scroll', atualizarTopo, { passive: true });
atualizarTopo();

const rotulo = $('#trilhoRotulo');
const rotuloTexto = $('#trilhoTexto');
const secoes = document.querySelectorAll('.secao');
const revelador = new IntersectionObserver((entradas) => {
  entradas.forEach((e) => { if (e.isIntersecting) e.target.classList.add('visivel'); });
}, { threshold: 0.15 });
secoes.forEach((s) => revelador.observe(s));
const vigia = new IntersectionObserver((entradas) => {
  entradas.forEach((e) => {
    if (e.intersectionRatio > 0.5) {
      rotulo.style.top = `${e.target.dataset.pos}%`;
      rotuloTexto.textContent = e.target.dataset.rotulo;
    }
  });
}, { threshold: [0.5, 0.51] });
secoes.forEach((s) => vigia.observe(s));

const PERGUNTAS = [
  'Qual a diferença entre inflação e deflação?',
  'Explique fotossíntese em tópicos, para a prova de amanhã.',
  'Por que meu código Python dá erro na linha 2?',
  'Como pedir um café em italiano?',
];
if (TXT) PERGUNTAS.splice(0, PERGUNTAS.length, ...TXT.perguntas);
const digitando = $('#digitando');
const proximo = $('#proximo');
(function digitar(i = 0) {
  const texto = PERGUNTAS[i];
  proximo.textContent = PERGUNTAS[(i + 1) % PERGUNTAS.length];
  if (reduzir) { digitando.textContent = texto; return; }
  let n = 0;
  const escrever = setInterval(() => {
    digitando.textContent = texto.slice(0, ++n);
    if (n >= texto.length) {
      clearInterval(escrever);
      setTimeout(() => {
        const apagar = setInterval(() => {
          n = Math.max(0, n - 2);
          digitando.textContent = texto.slice(0, n);
          if (n === 0) { clearInterval(apagar); setTimeout(() => digitar((i + 1) % PERGUNTAS.length), 250); }
        }, 14);
      }, 2600);
    }
  }, 38);
})();

const RECURSOS = [
  'Chat sobre qualquer assunto',
  'Revisão de código',
  'Explicação de erros, passo a passo',
  'Anexo de arquivos de código',
  'Blocos de código com “Copiar”',
  'Respostas em tópicos',
  'Histórico salvo no navegador',
  'Modo anônimo',
  'Tema claro e escuro',
  'Chat sobre qualquer assunto',
];
if (TXT) RECURSOS.splice(0, RECURSOS.length, ...TXT.recursosLista, TXT.recursosLista[0]);
const trilhoAbas = $('#abasTrilho');
const CANTOS = '<i class="canto c1"></i><i class="canto c2"></i><i class="canto c3"></i><i class="canto c4"></i>';
trilhoAbas.innerHTML = RECURSOS.map((r, i) =>
  `<div class="aba"><span class="aba-num">${String(i + 1).padStart(2, '0')}</span><span class="aba-txt">${r}</span>${CANTOS}</div>`
).join('');
const abas = [...trilhoAbas.children];
let abaAtual = 0;
function mostrarAba() {
  abas.forEach((a, i) => { a.classList.toggle('ativa', i === abaAtual); a.classList.toggle('passou', i < abaAtual); });
  trilhoAbas.style.transform = `translateX(${-abaAtual * abas[0].offsetWidth}px)`;
}
mostrarAba();
if (!reduzir) {
  setInterval(() => {
    abaAtual += 1;
    mostrarAba();
    if (abaAtual === abas.length - 1) {
      setTimeout(() => {
        trilhoAbas.classList.add('sem-transicao');
        abaAtual = 0;
        mostrarAba();
        void trilhoAbas.offsetWidth;
        trilhoAbas.classList.remove('sem-transicao');
      }, 950);
    }
  }, 2400);
}
addEventListener('resize', mostrarAba);

const EXEMPLOS = [
  { tema: 'ECONOMIA', texto: '“Qual a diferença entre inflação e deflação? Explique com um exemplo do dia a dia.' },
  { tema: 'PROGRAMAÇÃO', texto: '“Revise este código e me diga por que a comparação na linha 2 dá erro.' },
  { tema: 'ESTUDOS', texto: '“Me explique fotossíntese em tópicos, como se fosse para uma prova.' },
  { tema: 'IDIOMAS', texto: '“Como pedir um café em italiano? E como se pronuncia?' },
  { tema: 'HISTÓRIA', texto: '“Por que a Revolução Francesa começou? Resuma em cinco pontos.' },
  { tema: 'MATEMÁTICA', texto: '“Como calcular juros compostos? Me mostre a fórmula com um exemplo.' },
  { tema: 'CARREIRA', texto: '“Como escrever um resumo profissional para o meu LinkedIn?' },
  { tema: 'BANCO DE DADOS', texto: '“Qual a diferença entre INNER JOIN e LEFT JOIN em SQL?' },
  { tema: 'CIÊNCIA', texto: '“Como funciona um eclipse solar? Explique de um jeito simples.' },
  { tema: 'SEGURANÇA', texto: '“O que é SQL injection e como proteger o meu site contra isso?' },
  { tema: 'ESCRITA', texto: '“Revise este parágrafo e deixe o texto mais claro e direto.' },
  { tema: 'JAVASCRIPT', texto: '“Qual a diferença entre let, const e var? Quando usar cada um?' },
  { tema: 'SAÚDE', texto: '“Quantas horas de sono um adulto precisa por noite, em média?' },
  { tema: 'PYTHON', texto: '“Como ler um arquivo CSV em Python e somar uma das colunas?' },
];
if (TXT) EXEMPLOS.splice(0, EXEMPLOS.length, ...TXT.exemplosLista.map(([tema, texto]) => ({ tema, texto: '“' + texto })));
for (let i = EXEMPLOS.length - 1; i > 0; i--) {
  const j = Math.floor(Math.random() * (i + 1));
  [EXEMPLOS[i], EXEMPLOS[j]] = [EXEMPLOS[j], EXEMPLOS[i]];
}
const exTema = $('#exTema');
const exTexto = $('#exTexto');
const exNumero = $('#exNumero');
const exFantasma = $('#exFantasma');
const trocaveis = [exTema, exTexto, $('#exTipo')];
trocaveis.forEach((el) => el.classList.add('troca'));
let exAtual = 0;
function preencherExemplo() {
  const ex = EXEMPLOS[exAtual];
  exTema.textContent = ex.tema;
  exTexto.textContent = ex.texto;
  exNumero.textContent = String(exAtual + 1).padStart(2, '0');
  exFantasma.textContent = EXEMPLOS[(exAtual + 1) % EXEMPLOS.length].texto;
}
function trocarExemplo(passo) {
  trocaveis.forEach((el) => el.classList.add('saindo'));
  setTimeout(() => {
    exAtual = (exAtual + passo + EXEMPLOS.length) % EXEMPLOS.length;
    preencherExemplo();
    trocaveis.forEach((el) => el.classList.remove('saindo'));
  }, 450);
}
let autoExemplo = null;
function agendarExemplo() {
  clearInterval(autoExemplo);
  if (!reduzir) autoExemplo = setInterval(() => trocarExemplo(1), 5000);
}
$('#exAnterior').addEventListener('click', () => { trocarExemplo(-1); agendarExemplo(); });
$('#exProximo').addEventListener('click', () => { trocarExemplo(1); agendarExemplo(); });
agendarExemplo();
preencherExemplo();

const canvas = $('#cena');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
} catch (erro) {
  renderer = null;
}

if (renderer) iniciarRobo();

function iniciarRobo() {
  const celular = innerWidth < 900;
  const largura = () => innerWidth;
  const altura = () => innerHeight;
  const VAGAS = [0.46, 0.47, 0.56];
  matchMedia('(max-width: 899px)').addEventListener('change', () => location.reload());
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(largura(), altura(), false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const cena = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  cena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  cena.environmentIntensity = 0.9;

  const camera = new THREE.PerspectiveCamera(30, largura() / altura(), 0.1, 100);

  const hemi = new THREE.HemisphereLight(0xf1f4fb, 0x2a2b30, 0.7);
  cena.add(hemi);
  const chave = new THREE.DirectionalLight(0xf4f6fb, 1.7);
  chave.position.set(-3, 5, 4);
  chave.castShadow = true;
  chave.shadow.mapSize.set(1024, 1024);
  chave.shadow.radius = 6;
  chave.shadow.bias = -0.0005;
  cena.add(chave);
  const contra = new THREE.DirectionalLight(0xe8eefb, 1.2);
  contra.position.set(4, 2, -4);
  cena.add(contra);
  const preenchimento = new THREE.PointLight(0x92a8d1, 2.2, 6);
  preenchimento.position.set(-3.2, 1.2, 0.6);
  cena.add(preenchimento);

  const estrelaMat = new THREE.MeshPhysicalMaterial({
    color: 0x92a8d1, roughness: 0.22, metalness: 0.08, clearcoat: 1, clearcoatRoughness: 0.12,
    emissive: 0x6f88b8, emissiveIntensity: 0.18,
  });

  const CONTORNO = [0.8238,0.8165,0.8043,0.7903,0.7751,0.7600,0.7461,0.7321,0.7171,0.7014,0.6824,0.6637,0.6458,0.6252,0.6039,0.5818,0.5591,0.5347,0.5073,0.4806,0.4567,0.4354,0.4158,0.4021,0.3992,0.4059,0.4187,0.4343,0.4516,0.4672,0.4817,0.4970,0.5122,0.5292,0.5464,0.5612,0.5762,0.5924,0.6084,0.6236,0.6380,0.6540,0.6713,0.6864,0.6981,0.7091,0.7228,0.7372,0.7502,0.7618,0.7731,0.7854,0.7965,0.8033,0.8030,0.7959,0.7874,0.7792,0.7685,0.7532,0.7350,0.7172,0.6954,0.6680,0.6364,0.5992,0.5616,0.5237,0.4809,0.4419,0.4113,0.3845,0.3689,0.3682,0.3751,0.3849,0.3957,0.4068,0.4173,0.4271,0.4390,0.4533,0.4655,0.4759,0.4876,0.5005,0.5138,0.5276,0.5404,0.5509,0.5628,0.5774,0.5911,0.6039,0.6158,0.6280,0.6415,0.6540,0.6657,0.6777,0.6901,0.7012,0.7112,0.7231,0.7351,0.7448,0.7549,0.7664,0.7772,0.7848,0.7833,0.7718,0.7573,0.7408,0.7223,0.7043,0.6858,0.6662,0.6441,0.6194,0.5927,0.5606,0.5156,0.4431,0.3721,0.3481,0.3528,0.3580,0.3617,0.3652,0.3693,0.3729,0.3779,0.3833,0.3873,0.3909,0.3949,0.3999,0.4051,0.4086,0.4119,0.4160,0.4200,0.4245,0.4291,0.4322,0.4360,0.4412,0.4455,0.4484,0.4525,0.4581,0.4637,0.4683,0.4720,0.4752,0.4787,0.4827,0.4868,0.4911,0.4957,0.5010,0.5069,0.5131,0.5185,0.5230,0.5281,0.5333,0.5382,0.5438,0.5499,0.5552,0.5609,0.5674,0.5729,0.5786,0.5854,0.5919,0.5975,0.6033,0.6117,0.6201,0.6270,0.6358,0.6444,0.6511,0.6590,0.6680,0.6777,0.6883,0.6990,0.7094,0.7211,0.7339,0.7475,0.7618,0.7710,0.7708,0.7623,0.6607,0.4762,0.3889,0.3923,0.3959,0.4010,0.4067,0.4118,0.4154,0.4187,0.4231,0.4278,0.4332,0.4386,0.4433,0.4480,0.4527,0.4584,0.4651,0.4709,0.4760,0.4819,0.4888,0.4950,0.4996,0.5050,0.5121,0.5185,0.5250,0.5332,0.5415,0.5484,0.5548,0.5621,0.5702,0.5782,0.5865,0.5949,0.6033,0.6121,0.6221,0.6329,0.6437,0.6538,0.6635,0.6742,0.6858,0.6976,0.7096,0.7221,0.7347,0.7474,0.7605,0.7745,0.7894,0.8050,0.8213,0.8389,0.8574,0.8741,0.8915,0.9125,0.9336,0.9540,0.9760,0.9942,0.9985,0.9892,0.9713,0.9467,0.9072,0.7685,0.5633,0.4771,0.4888,0.5006,0.5128,0.5253,0.5380,0.5514,0.5650,0.5785,0.5923,0.6068,0.6216,0.6365,0.6506,0.6640,0.6789,0.6940,0.7083,0.7231,0.7352,0.7466,0.7611,0.7757,0.7879,0.7966,0.7974,0.7888,0.7760,0.7614,0.7450,0.7281,0.7111,0.6924,0.6702,0.6454,0.6191,0.5930,0.5660,0.5367,0.5078,0.4765,0.4442,0.4176,0.3921,0.3626,0.3299,0.3009,0.2774,0.2594,0.2527,0.2547,0.2600,0.2670,0.2744,0.2822,0.2907,0.2998,0.3093,0.3193,0.3298,0.3413,0.3539,0.3674,0.3817,0.3963,0.4084,0.4188,0.4298,0.4414,0.4550,0.4672,0.4798,0.4935,0.5035,0.5137,0.5262,0.5383,0.5498,0.5627,0.5769,0.5893,0.5998,0.6107,0.6211,0.6318,0.6452,0.6570,0.6649,0.6708,0.6706,0.6622,0.6496,0.6377,0.6278,0.6172,0.6072,0.5967,0.5831,0.5706,0.5598,0.5485,0.5371,0.5248,0.5117,0.4999,0.4900,0.4792,0.4674,0.4541,0.4399,0.4283,0.4175,0.4073,0.3963,0.3827,0.3690,0.3562,0.3440,0.3328,0.3225,0.3126,0.3033,0.2946,0.2864,0.2786,0.2712,0.2642,0.2577,0.2528,0.2580,0.2764,0.2980,0.3263,0.3623,0.3958,0.4266,0.4567,0.4872,0.5199,0.5529,0.5817,0.6059,0.6305,0.6562,0.6809,0.7032,0.7220,0.7383,0.7538,0.7696,0.7855,0.7973,0.7994,0.7931,0.7820,0.7685,0.7554,0.7430,0.7307,0.7170,0.7027,0.6890,0.6741,0.6594,0.6464,0.6325,0.6176,0.6032,0.5889,0.5749,0.5615,0.5473,0.5330,0.5203,0.5081,0.4962,0.4846,0.4730,0.5766,0.8070,0.9432,0.9690,0.9868,0.9987,1.0000,0.9862,0.9631,0.9405,0.9204,0.9004,0.8818,0.8637,0.8450,0.8279,0.8131,0.7995,0.7848,0.7685,0.7538,0.7411,0.7274,0.7150,0.7050,0.6942,0.6823,0.6707,0.6592,0.6487,0.6393,0.6295,0.6201,0.6115,0.6019,0.5925,0.5840,0.5758,0.5687,0.5616,0.5529,0.5445,0.5377,0.5316,0.5248,0.5176,0.5112,0.5048,0.4980,0.4919,0.4862,0.4809,0.4750,0.4694,0.4647,0.4590,0.4533,0.4486,0.4439,0.4385,0.4324,0.4280,0.4243,0.4196,0.4151,0.4100,0.4051,0.4002,0.3951,0.3918,0.4792,0.6619,0.7635,0.7740,0.7749,0.7653,0.7508,0.7372,0.7236,0.7113,0.7016,0.6918,0.6814,0.6717,0.6627,0.6546,0.6477,0.6394,0.6310,0.6242,0.6159,0.6075,0.6008,0.5941,0.5873,0.5807,0.5759,0.5710,0.5638,0.5576,0.5521,0.5459,0.5403,0.5355,0.5309,0.5259,0.5202,0.5137,0.5082,0.5038,0.4993,0.4946,0.4902,0.4859,0.4809,0.4760,0.4723,0.4693,0.4659,0.4612,0.4556,0.4505,0.4470,0.4437,0.4387,0.4337,0.4298,0.4253,0.4209,0.4177,0.4140,0.4099,0.4058,0.4013,0.3971,0.3929,0.3890,0.3842,0.3790,0.3752,0.3705,0.3662,0.3634,0.3588,0.3530,0.3638,0.4114,0.4777,0.5303,0.5689,0.6021,0.6277,0.6497,0.6739,0.6962,0.7139,0.7309,0.7480,0.7635,0.7776,0.7863,0.7852,0.7772,0.7663,0.7547,0.7447,0.7350,0.7230,0.7111,0.7010,0.6899,0.6775,0.6644,0.6517,0.6402,0.6266,0.6121,0.6001,0.5883,0.5746,0.5602,0.5459,0.5330,0.5218,0.5085,0.4942,0.4822,0.4702,0.4588,0.4478,0.4348,0.4219,0.4100,0.3986,0.3887,0.3808,0.3738,0.3695,0.3766,0.3998,0.4338,0.4704,0.5053,0.5426,0.5825,0.6202,0.6542,0.6813,0.7047,0.7267,0.7456,0.7619,0.7741,0.7831,0.7921,0.8004,0.8051,0.8036,0.7953,0.7836,0.7719,0.7598,0.7460,0.7321,0.7182,0.7052,0.6924,0.6773,0.6608,0.6452,0.6304,0.6158,0.6004,0.5837,0.5663,0.5507,0.5359,0.5187,0.5014,0.4858,0.4700,0.4553,0.4420,0.4279,0.4135,0.4025,0.4027,0.4157,0.4344,0.4550,0.4776,0.5024,0.5285,0.5520,0.5756,0.6020,0.6236,0.6418,0.6609,0.6780,0.6934,0.7094,0.7251,0.7404,0.7546,0.7686,0.7836,0.7979,0.8111,0.8216];
  const R = 1.25;
  const forma = new THREE.Shape();
  CONTORNO.forEach((r, i) => {
    const a = (i / CONTORNO.length) * Math.PI * 2;
    const x = Math.cos(a) * r * R, y = Math.sin(a) * r * R;
    if (i === 0) forma.moveTo(x, y); else forma.lineTo(x, y);
  });
  forma.closePath();
  const geoEstrela = new THREE.ExtrudeGeometry(forma, {
    depth: 0.26, bevelEnabled: true, bevelThickness: 0.07, bevelSize: 0.05, bevelSegments: 6, curveSegments: 4,
  });
  geoEstrela.center();
  geoEstrela.computeVertexNormals();

  const simbolo = new THREE.Group();
  simbolo.position.y = 1.0;
  cena.add(simbolo);
  const estrela3d = new THREE.Mesh(geoEstrela, estrelaMat);
  estrela3d.castShadow = true;
  simbolo.add(estrela3d);
  const copias = celular ? [0].map(() => {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(geoEstrela, estrelaMat));
    cena.add(g);
    return g;
  }) : [];
  if (celular) simbolo.visible = false;

  function temaDaCena() {
    const claro = temaClaro();
    hemi.groundColor.set(claro ? 0xd9d6cf : 0x2a2b30);
    hemi.intensity = claro ? 0.8 : 0.7;
    renderer.toneMappingExposure = claro ? 1.0 : 1.05;
  }
  temaDaCena();
  aoMudarTema.push(temaDaCena);

  const ESTADOS = [
    { camZ: 11.6, camY: 1.1, olharY: 0.35, olharX: -0.55, giro: -0.35, inclina: 0.18 },
    { camZ: 6.2, camY: 1.35, olharY: 1.0, olharX: -0.2, giro: 0.0, inclina: 0.0 },
    { camZ: 6.6, camY: 1.35, olharY: 1.0, olharX: -0.95, giro: 0, inclina: 0 },
  ];
  const suave = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const mix = (a, b, t) => a + (b - a) * t;
  let p = 0;
  const mouse = { x: 0, y: 0, sx: 0, sy: 0 };
  addEventListener('pointermove', (e) => {
    mouse.x = (e.clientX / innerWidth) * 2 - 1;
    mouse.y = (e.clientY / innerHeight) * 2 - 1;
  }, { passive: true });

  function ajustar() {
    renderer.setSize(largura(), altura(), false);
    camera.aspect = largura() / altura();
    camera.updateProjectionMatrix();
  }
  addEventListener('resize', ajustar);

  const relogio = new THREE.Clock();
  function quadro(agora) {
    const t = relogio.getElapsedTime();
    const alvo = Math.min(2, Math.max(0, scrollY / innerHeight));
    p += (alvo - p) * (reduzir ? 1 : 0.08);
    mouse.sx += (mouse.x - mouse.sx) * 0.06;
    mouse.sy += (mouse.y - mouse.sy) * 0.06;

    const i = Math.min(1, Math.floor(p));
    const k = suave(Math.min(1, p - i));
    const lista = ESTADOS;
    const a = lista[i], b = lista[i + 1];
    const e = {};
    Object.keys(a).forEach((chaveEstado) => { e[chaveEstado] = mix(a[chaveEstado], b[chaveEstado], k); });

    const mov = reduzir ? 0 : 1;
    if (celular) {
      const dist = 16;
      camera.position.set(0, 0, dist);
      camera.lookAt(0, 0, 0);
      const alturaVista = 2 * dist * Math.tan(THREE.MathUtils.degToRad(15));
      const pxPorUnidade = innerHeight / alturaVista;
      const alvoPx = Math.min(innerWidth * 0.72, innerHeight * 0.42);
      const escala = alvoPx / (2.5 * pxPorUnidade);
      const copia = copias[0];
      copia.position.set(0, -0.04 * alturaVista + Math.sin(t * 1.2) * 0.06 * mov, 0);
      const malhaCopia = copia.children[0];
      malhaCopia.rotation.set(Math.sin(t * 0.8) * 0.06 * mov, p * Math.PI + Math.sin(t * 0.6) * 0.12 * mov, 0);
      malhaCopia.scale.setScalar((1 + Math.sin(t * 2.2) * 0.035 * mov) * escala);
    } else {
      const desvio = e.olharX;
      camera.position.set(desvio + mouse.sx * 0.25 * mov, e.camY - mouse.sy * 0.1 * mov, e.camZ);
      camera.lookAt(desvio, e.olharY, 0);
      simbolo.position.set(0, 1.0 + Math.sin(t * 1.2) * 0.08 * mov, 0);
    }
    const fim = suave(Math.max(0, Math.min(1, p - 1)));
    const giro = fim * Math.PI * 2;
    const livre = (1 - fim) * mov;
    if (!celular) estrela3d.rotation.set(
      e.inclina + mouse.sy * 0.25 * livre,
      e.giro + giro + mouse.sx * 0.5 * livre,
      Math.sin(t * 0.6) * 0.04 * livre
    );
    if (!celular) estrela3d.scale.setScalar(1 + Math.sin(t * 2.2) * 0.035 * mov);
    estrelaMat.emissiveIntensity = 0.18 + (Math.sin(t * 2.2) * 0.5 + 0.5) * 0.25 * mov;

    renderer.render(cena, camera);
    requestAnimationFrame(quadro);
  }
  ajustar();
  requestAnimationFrame(quadro);
}

document.querySelectorAll('a[href="/app"]').forEach((link) => {
  link.addEventListener('click', (e) => {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0 || !window.AstraCarregando) return;
    e.preventDefault();
    AstraCarregando.ir('/app', 'abrindo');
  });
});
