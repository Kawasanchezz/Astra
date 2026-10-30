const $ = (sel) => document.querySelector(sel);

function lsGet(chave, padrao = null) {
  try { return localStorage.getItem(chave) ?? padrao; } catch { return padrao; }
}
function lsSet(chave, valor) {
  try { valor === null ? localStorage.removeItem(chave) : localStorage.setItem(chave, valor); }
  catch {  }
}

function icons() { if (window.lucide) lucide.createIcons(); }
icons();

const els = {
  app: $('.app'),
  hero: $('#hero'),
  chat: $('#chat'),
  messages: $('#messages'),
  anchor: $('#chatAnchor'),
  input: $('#promptInput'),
  send: $('#sendBtn'),
  attach: $('#attachBtn'),
  fileInput: $('#fileInput'),
  attachTags: $('#attachTags'),
  sidebar: $('#sidebar'),
  veil: $('#sidebarVeil'),
  historyList: $('#historyList'),
  toast: $('#toast'),
};

const STORE_KEY = 'credix_landing_chats';
const MODEL_KEY = 'horus_model';
let modeloEscolhido = lsGet(MODEL_KEY, '');
let history = [];
let chatId = Date.now().toString();
let chats = loadChats();
let attachments = [];
let sending = false;
let anonimo = false;
const isServed = location.protocol.startsWith('http');
const AVISOS = {
  pt: { falha: 'Não consegui responder agora. Tente de novo em alguns segundos.' },
  en: { falha: "I couldn't reply right now. Please try again in a few seconds." },
  es: { falha: 'No pude responder ahora. Inténtalo de nuevo en unos segundos.' },
};
const aviso = () => AVISOS[(lsGet('astra_idioma', 'pt') || 'pt').slice(0, 2)] || AVISOS.pt;
const MAX_PAYLOAD = 7500;
const MAX_HISTORY_PAYLOAD = 10000;
const MAX_FILE_BYTES = 200 * 1024;
const MAX_FILE_CHARS = 7000;

const orb = $('#orb');
const MAX_TILT = 8;
let tX = 0, tY = 0, cX = 0, cY = 0;
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function animateOrb() {
  cX += (tX - cX) * 0.08;
  cY += (tY - cY) * 0.08;
  if (orb) orb.style.transform = `rotateY(${cX}deg) rotateX(${cY}deg)`;
  requestAnimationFrame(animateOrb);
}
function pointer(x, y) {
  const cx = innerWidth / 2, cy = innerHeight / 2;
  tX = ((x - cx) / cx) * MAX_TILT;
  tY = -((y - cy) / cy) * MAX_TILT;
}
if (orb && !reduceMotion) {
  addEventListener('mousemove', (e) => pointer(e.clientX, e.clientY));
  addEventListener('mouseleave', () => { tX = 0; tY = 0; });
  animateOrb();
}

function toast(msg, ms = 2600) {
  els.toast.textContent = msg;
  els.toast.hidden = false;
  els.toast.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => {
    els.toast.classList.remove('show');
    setTimeout(() => (els.toast.hidden = true), 250);
  }, ms);
}

let _confirmCb = null;
function confirmModal(title, msg, onOk) {
  $('#confirmTitle').textContent = title;
  $('#confirmMsg').textContent = msg;
  _confirmCb = onOk;
  $('#confirmModal').hidden = false;
  icons();
  setTimeout(() => $('#confirmCancel').focus(), 30);
}
function closeConfirm() { $('#confirmModal').hidden = true; _confirmCb = null; }

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

if (typeof DOMPurify !== 'undefined') {
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A' && node.hasAttribute('href')) {
      node.setAttribute('target', '_blank');
      node.setAttribute('rel', 'noopener noreferrer');
    }
  });
}

function renderMarkdown(text) {
  if (typeof marked === 'undefined') return escapeHtml(text);
  try {
    const html = marked.parse(text);
    return (typeof DOMPurify !== 'undefined') ? DOMPurify.sanitize(html) : escapeHtml(text);
  } catch { return escapeHtml(text); }
}

function scrollBottom() {
  if (els.anchor) els.anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function autoGrow() {
  els.input.style.height = 'auto';
  els.input.style.height = Math.min(els.input.scrollHeight, 160) + 'px';
}

function enterChatMode() {
  if (!els.chat.hidden) return;
  els.hero.hidden = true;
  els.chat.hidden = false;
  els.app.classList.add('is-chatting');
}
function goHome() {
  els.chat.hidden = true;
  els.hero.hidden = false;
  els.app.classList.remove('is-chatting');
}

function resetConversa() {
  history = [];
  chatId = Date.now().toString();
  els.messages.innerHTML = '';
  clearAttachments();
  renderHistoryList();
  goHome();
}

function newChat() {
  saveCurrent();
  resetConversa();
  els.input.focus();
}

function appendMsg(classe, html, id) {
  const row = document.createElement('div');
  row.className = classe;
  if (id) row.id = id;
  row.innerHTML = html;
  row.querySelectorAll('.markdown pre').forEach(decorarBlocoDeCodigo);
  els.messages.appendChild(row);
  icons();
  scrollBottom();
  return row;
}

async function copiarTexto(texto) {
  try {
    await navigator.clipboard.writeText(texto);
    return true;
  } catch {  }
  const area = document.createElement('textarea');
  area.value = texto;
  area.className = 'clipboard-fallback';
  document.body.appendChild(area);
  area.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch {  }
  area.remove();
  return ok;
}

function decorarBlocoDeCodigo(pre) {
  const code = pre.querySelector('code');
  const linguagem = (code?.className.match(/language-([\w+#.-]+)/) || [])[1] || 'código';

  const bloco = document.createElement('div');
  bloco.className = 'codeblock';
  const cabecalho = document.createElement('div');
  cabecalho.className = 'codeblock__head';
  const rotulo = document.createElement('span');
  rotulo.textContent = linguagem;
  const botao = document.createElement('button');
  botao.type = 'button';
  botao.className = 'codeblock__copy';
  botao.textContent = 'Copiar';
  botao.setAttribute('aria-label', 'Copiar código');

  botao.onclick = async () => {
    const ok = await copiarTexto((code || pre).textContent.trimEnd());
    botao.textContent = ok ? 'Copiado!' : 'Não copiou';
    botao.classList.toggle('is-done', ok);
    setTimeout(() => { botao.textContent = 'Copiar'; botao.classList.remove('is-done'); }, 1600);
  };

  cabecalho.append(rotulo, botao);
  pre.replaceWith(bloco);
  bloco.append(cabecalho, pre);
}

function addUserMsg(text, files = []) {
  const tags = files.length
    ? `<div class="msg__files">${files.map(f => `<span><i data-lucide="file"></i>${escapeHtml(f.name)}</span>`).join('')}</div>`
    : '';
  appendMsg('msg msg--user',
    `<div class="msg__bubble">${tags}${escapeHtml(text).replace(/\n/g, '<br>')}</div>`);
}

function addBotMsg(text, isError = false) {
  appendMsg('msg msg--bot',
    `<div class="msg__bubble markdown ${isError ? 'is-error' : ''}">${renderMarkdown(text)}</div>`);
}

function showThinking() {
  appendMsg('msg msg--bot',
    `<div class="msg__bubble"><span class="dots"><span>.</span><span>.</span><span>.</span></span></div>`, 'thinking');
}
function hideThinking() { const t = $('#thinking'); if (t) t.remove(); }

function historicoParaEnvio() {
  const recorte = [];
  let orcamento = MAX_HISTORY_PAYLOAD;
  for (let i = history.length - 1; i >= 0; i--) {
    const tamanho = (history[i].content || '').length;
    if (tamanho > orcamento) break;
    recorte.push(history[i]);
    orcamento -= tamanho;
  }
  return recorte.reverse();
}

function montarPayload(text, arquivos) {
  let payload = text;
  if (arquivos.length) {
    payload += '\n\n' + arquivos
      .map(f => `Conteúdo do arquivo "${f.name}":\n\`\`\`\n${f.content}\n\`\`\``)
      .join('\n\n');
  }

  if (payload.length > MAX_PAYLOAD) payload = payload.slice(0, MAX_PAYLOAD) + '\n…(conteúdo truncado)';

  return payload;
}

function tratarResposta(data, textoEnviado) {
  if (data.erro) {
    addBotMsg(`Erro: ${data.erro}`, true);
    return;
  }
  addBotMsg(data.resposta);
  history.push({ role: 'user', content: textoEnviado || '(arquivo anexado)' });
  history.push({ role: 'assistant', content: data.resposta });
  saveCurrent();
  renderHistoryList();
}

async function send(presetText) {
  if (sending) return;
  const text = (presetText ?? els.input.value).trim();
  if (!text && attachments.length === 0) { els.input.focus(); return; }

  enterChatMode();

  const sentFiles = [...attachments];
  addUserMsg(text || '(arquivo anexado)', sentFiles);
  contarUso();

  const payload = montarPayload(text, sentFiles);

  const prevHistory = historicoParaEnvio();
  els.input.value = '';
  autoGrow();
  clearAttachments();

  sending = true;
  els.send.disabled = true;
  showThinking();

  if (!isServed) {
    hideThinking();
    addBotMsg('⚠️ Abra a página pelo servidor Python (`http://127.0.0.1:5000`) para conversar com a IA. Pelo `file://` o navegador bloqueia a conexão.', true);
    sending = false; els.send.disabled = false;
    return;
  }

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mensagem: payload,
        historico: prevHistory,
        ...(modeloEscolhido ? { modelo: modeloEscolhido } : {}),
        idioma: idiomaEscolhido
      })
    });
    const data = await res.json();
    hideThinking();
    tratarResposta(data, text);
  } catch (e) {
    hideThinking();
    addBotMsg(aviso().falha, true);
  } finally {
    sending = false;
    els.send.disabled = false;
    scrollBottom();
  }
}

function loadChats() {
  try { return JSON.parse(lsGet(STORE_KEY)) || {}; }
  catch { return {}; }
}
function saveCurrent() {
  if (anonimo) return;
  if (history.length === 0) return;
  const title = chats[chatId]?.title || (history[0].content.slice(0, 32) + (history[0].content.length > 32 ? '…' : ''));
  const pinned = chats[chatId]?.pinned || false;
  chats[chatId] = { id: chatId, title, messages: [...history], ts: Date.now(), pinned };
  salvarChats();
}
function salvarChats() {
  lsSet(STORE_KEY, JSON.stringify(chats));
}

function renderHistoryList() {
  const ids = Object.keys(chats).sort((a, b) => {
    const pa = chats[a].pinned ? 1 : 0, pb = chats[b].pinned ? 1 : 0;
    if (pa !== pb) return pb - pa;
    return (chats[b].ts || b) - (chats[a].ts || a);
  });

  if (ids.length === 0) {
    els.historyList.innerHTML = `<p class="muted history-empty">Nenhuma conversa ainda.</p>`;
    return;
  }

  els.historyList.innerHTML = '';
  ids.forEach(id => {
    const item = document.createElement('div');
    item.className = 'history-item' + (id === chatId ? ' is-active' : '');
    item.dataset.id = id;
    item.innerHTML = `
      ${chats[id].pinned ? '<i data-lucide="pin" class="history-item__pin"></i>' : ''}
      <span class="history-item__title">${escapeHtml(chats[id].title)}</span>
      <button class="history-item__more" title="Mais ações" aria-label="Mais ações" aria-haspopup="menu">
        <i data-lucide="more-vertical"></i>
      </button>`;
    item.querySelector('.history-item__title')?.addEventListener('click', () => loadChat(id));
    item.querySelector('.history-item__more')?.addEventListener('click', (e) => {
      e.stopPropagation();
      abrirMenuChat(id, e.currentTarget);
    });
    els.historyList.appendChild(item);
  });
  icons();
}

let menuChatId = null;

function abrirMenuChat(id, botao) {
  menuChatId = id;
  const menu = $('#chatMenu');
  $('#chatMenuPinLabel').textContent = chats[id]?.pinned ? 'Desafixar' : 'Fixar';

  menu.hidden = false;
  icons();

  const r = botao.getBoundingClientRect();
  const m = menu.getBoundingClientRect();
  let top = r.bottom + 6;
  let left = r.right - m.width;
  if (top + m.height > innerHeight - 8) top = Math.max(8, r.top - m.height - 6);
  if (left < 8) left = 8;
  menu.style.top = `${top}px`;
  menu.style.left = `${left}px`;
}

function fecharMenuChat() {
  $('#chatMenu').hidden = true;
  menuChatId = null;
}

function fixarChat(id) {
  if (!chats[id]) return;
  chats[id].pinned = !chats[id].pinned;
  salvarChats();
  renderHistoryList();
  toast(chats[id].pinned ? 'Conversa fixada.' : 'Conversa desafixada.', 1400);
}

function renomearChat(id) {
  const item = els.historyList.querySelector(`.history-item[data-id="${id}"]`);
  if (!item || !chats[id]) return;
  const span = item.querySelector('.history-item__title');

  const input = document.createElement('input');
  input.className = 'history-item__input';
  input.value = chats[id].title;
  input.maxLength = 80;
  span.replaceWith(input);
  input.focus();
  input.select();

  let encerrado = false;
  const confirmar = (salvar) => {
    if (encerrado) return;
    encerrado = true;
    const novo = input.value.trim();
    if (salvar && novo && novo !== chats[id].title) {
      chats[id].title = novo;
      salvarChats();
      toast('Nome alterado.', 1400);
    }
    renderHistoryList();
  };
  input.onkeydown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); confirmar(true); }
    else if (e.key === 'Escape') { e.preventDefault(); confirmar(false); }
  };
  input.onblur = () => confirmar(true);
  input.onclick = (e) => e.stopPropagation();
}
function loadChat(id) {
  if (!chats[id]) return;
  if (anonimo) setAnonimo(false);
  saveCurrent();
  chatId = id;
  history = [...chats[id].messages];
  els.messages.innerHTML = '';
  history.forEach(m => m.role === 'user' ? addUserMsg(m.content) : addBotMsg(m.content));
  enterChatMode();
  closeSidebarIfMobile();
  renderHistoryList();
}
function deleteChat(id) {
  confirmModal('Excluir conversa?', 'Esta conversa será excluída permanentemente. Isso não pode ser desfeito.', () => doDeleteChat(id));
}
function doDeleteChat(id) {
  delete chats[id];
  salvarChats();
  if (id === chatId) { history = []; newChat(); }
  renderHistoryList();
  toast('Conversa apagada.');
}
const SIDEBAR_KEY = 'horus_sidebar_open';
const DRAWER_BP = 900;
const isDrawer = () => window.matchMedia(`(max-width: ${DRAWER_BP}px)`).matches;
const sidebarIsOpen = () => els.app.classList.contains('is-sidebar-open');

function setSidebar(open) {
  els.app.classList.toggle('is-sidebar-open', open);
  els.veil.hidden = !(open && isDrawer());
  $('#sidebarToggle').setAttribute('aria-expanded', String(open));
  if (!open) toggleAccountMenu(false);
  if (!isDrawer()) lsSet(SIDEBAR_KEY, open ? '1' : '0');
}

function closeSidebarIfMobile() { if (isDrawer()) setSidebar(false); }

function toggleAccountMenu(forcar) {
  const menu = $('#accountMenu');
  const abrir = forcar === undefined ? menu.hidden : forcar;
  menu.hidden = !abrir;
  $('#accountBtn').setAttribute('aria-expanded', String(abrir));
  if (abrir) icons();
}

const PREF = { theme: 'horus_theme', font: 'horus_font', motion: 'horus_motion' };
const raiz = document.documentElement;

const lerPref = (k, padrao) => lsGet(PREF[k], padrao);
const gravarPref = (k, v) => lsSet(PREF[k], v || null);

function aplicarTema(v) {
  raiz.setAttribute('data-theme', v);
  gravarPref('theme', v);
  marcarSeg('#themeSeg', 'theme', v);
}
const FONTES = ['', 'georgia', 'verdana', 'mono'];

function aplicarFonte(v) {
  if (!FONTES.includes(v)) v = '';
  if (v) raiz.setAttribute('data-font', v); else raiz.removeAttribute('data-font');
  gravarPref('font', v);
  $('#fontSelect').value = v;
}
function aplicarMovimento(v) {
  if (v === 'reduced') raiz.setAttribute('data-motion', 'reduced');
  else raiz.removeAttribute('data-motion');
  gravarPref('motion', v);
  marcarSeg('#motionSeg', 'motion', v);
}
function marcarSeg(sel, attr, v) {
  $(sel).querySelectorAll('button').forEach(b =>
    b.classList.toggle('is-active', b.dataset[attr] === v));
}

async function carregarModelos() {
  const sel = $('#modelSelect');
  if (!isServed) { sel.disabled = true; return; }
  try {
    const r = await fetch('/models');
    const { modelos = [], padrao } = await r.json();
    const alternativas = modelos.filter(m => m !== padrao);
    alternativas.forEach(m => {
      const o = document.createElement('option');
      o.value = m;
      o.textContent = m;
      sel.appendChild(o);
    });
    sel.value = alternativas.includes(modeloEscolhido) ? modeloEscolhido : '';
    if (sel.value !== modeloEscolhido) {
      modeloEscolhido = '';
      lsSet(MODEL_KEY, null);
    }
  } catch {
    sel.disabled = true;
  }
}

function setAnonimo(on) {
  if (on) saveCurrent();

  anonimo = on;
  els.app.classList.toggle('is-anon', on);
  document.documentElement.classList.toggle('is-anon', on);
  $('#incognitoBtn').setAttribute('aria-pressed', String(on));
  $('#anonBar').hidden = !on;
  $('#anonNote').hidden = !on;
  $('#headlineNormal').hidden = on;
  $('#headlineAnon').hidden = !on;
  if (on) {
    setSidebar(false);
    icons();
  }

  resetConversa();

}

function clearAllHistory() {
  confirmModal('Apagar todo o histórico?', 'Todas as conversas salvas serão excluídas permanentemente. Isso não pode ser desfeito.', () => {
    chats = {};
    lsSet(STORE_KEY, null);
    $('#settingsModal').hidden = true;
    newChat();
    renderHistoryList();
    toast('Histórico apagado.');
  });
}

function renderAttachTags() {
  els.attachTags.innerHTML = attachments.map((f, i) =>
    `<span class="attach-tag"><i data-lucide="file"></i>${escapeHtml(f.name)}
       <button data-i="${i}" title="Remover"><i data-lucide="x"></i></button></span>`
  ).join('');
  els.attachTags.querySelectorAll('button').forEach(b =>
    b.onclick = () => { attachments.splice(+b.dataset.i, 1); renderAttachTags(); });
  icons();
}
function clearAttachments() { attachments = []; els.attachTags.innerHTML = ''; }

els.attach.onclick = () => els.fileInput.click();
els.fileInput.onchange = (e) => {
  const files = Array.from(e.target.files || []);
  files.forEach(file => {
    if (file.size > MAX_FILE_BYTES) { toast(`"${file.name}" é grande demais (máx. ${MAX_FILE_BYTES / 1024}KB).`); return; }
    const reader = new FileReader();
    reader.onload = () => { attachments.push({ name: file.name, content: String(reader.result).slice(0, MAX_FILE_CHARS) }); renderAttachTags(); };
    reader.readAsText(file);
  });
  els.fileInput.value = '';
};

els.send.onclick = () => send();
els.input.addEventListener('input', autoGrow);
els.input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});

$('#newChatBtn').onclick = () => { newChat(); closeSidebarIfMobile(); };

$('#incognitoBtn').onclick = () => setAnonimo(true);
$('#anonClose').onclick = () => setAnonimo(false);
$('#sidebarOpen').onclick = () => setSidebar(true);
$('#sidebarToggle').onclick = () => setSidebar(false);
els.veil.onclick = () => setSidebar(false);
addEventListener('resize', () => { els.veil.hidden = !(sidebarIsOpen() && isDrawer()); });

const ACOES_CHAT = { pin: fixarChat, rename: renomearChat, delete: deleteChat };

function executarAcaoChat(acao) {
  const id = menuChatId;
  fecharMenuChat();
  ACOES_CHAT[acao]?.(id);
}

$('#chatMenu').querySelectorAll('.chat-menu__item').forEach(b => {
  b.onclick = (e) => { e.stopPropagation(); executarAcaoChat(b.dataset.act); };
});
addEventListener('keydown', (e) => {
  if (menuChatId === null || e.ctrlKey || e.altKey || e.metaKey) return;
  const acao = { p: 'pin', r: 'rename', d: 'delete' }[e.key.toLowerCase()];
  if (!acao) return;
  e.preventDefault();
  executarAcaoChat(acao);
});

$('#accountBtn').onclick = (e) => { e.stopPropagation(); toggleAccountMenu(); };
$('#menuSettings').onclick = () => { toggleAccountMenu(false); $('#settingsModal').hidden = false; };
$('#menuClear').onclick = () => { toggleAccountMenu(false); clearAllHistory(); };
document.addEventListener('click', (e) => {
  if (!e.target.closest('.sidebar__foot')) toggleAccountMenu(false);
  if (!e.target.closest('#chatMenu')) fecharMenuChat();
});
addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (menuChatId !== null) fecharMenuChat();
  else if (!$('#accountMenu').hidden) toggleAccountMenu(false);
  else closeSidebarIfMobile();
});
els.historyList.addEventListener('scroll', fecharMenuChat);
addEventListener('resize', fecharMenuChat);

$('#settingsClose').onclick = $('#settingsDone').onclick = () => { $('#settingsModal').hidden = true; };

$('#themeSeg').querySelectorAll('button').forEach(b =>
  b.onclick = () => aplicarTema(b.dataset.theme));
$('#motionSeg').querySelectorAll('button').forEach(b =>
  b.onclick = () => aplicarMovimento(b.dataset.motion));
$('#fontSelect').onchange = (e) => aplicarFonte(e.target.value);

$('#modelSelect').onchange = (e) => {
  modeloEscolhido = e.target.value;
  lsSet(MODEL_KEY, modeloEscolhido || null);
  toast(modeloEscolhido ? `Modelo: ${modeloEscolhido}` : 'Usando o modelo padrão do servidor.', 1600);
};

$('#confirmOk').onclick = () => { const cb = _confirmCb; closeConfirm(); if (cb) cb(); };
$('#confirmCancel').onclick = closeConfirm;
$('#confirmModal').addEventListener('click', (e) => { if (e.target.id === 'confirmModal') closeConfirm(); });
$('#settingsModal').addEventListener('click', (e) => {
  if (e.target.id === 'settingsModal') $('#settingsModal').hidden = true;
});

renderHistoryList();

setSidebar(!isDrawer() && lsGet(SIDEBAR_KEY) === '1');

aplicarTema(lerPref('theme', 'dark'));
aplicarFonte(lerPref('font', ''));
aplicarMovimento(lerPref('motion', 'system'));

carregarModelos().catch(() => {});

const IDIOMAS = [
  ['pt-BR', 'Português (Brasil)', 'Portuguese (Brazil)'], ['pt-PT', 'Português (Portugal)', 'Portuguese (Portugal)'],
  ['en-US', 'English (United States)', 'English (United States)'], ['en-GB', 'English (United Kingdom)', 'English (United Kingdom)'],
  ['es-419', 'Español (Latinoamérica)', 'Spanish (Latin America)'], ['es-ES', 'Español (España)', 'Spanish (Spain)'],
  ['fr-FR', 'Français (France)', 'French (France)'], ['de-DE', 'Deutsch (Deutschland)', 'German (Germany)'],
  ['it-IT', 'Italiano (Italia)', 'Italian (Italy)'], ['nl-NL', 'Nederlands', 'Dutch'],
  ['da-DK', 'Dansk', 'Danish'], ['sv-SE', 'Svenska', 'Swedish'], ['nb-NO', 'Norsk bokmål', 'Norwegian'],
  ['fi-FI', 'Suomi', 'Finnish'], ['pl-PL', 'Polski', 'Polish'], ['cs-CZ', 'Čeština', 'Czech'],
  ['ro-RO', 'Română', 'Romanian'], ['hu-HU', 'Magyar', 'Hungarian'], ['el-GR', 'Ελληνικά', 'Greek'],
  ['ru-RU', 'Русский', 'Russian'], ['uk-UA', 'Українська', 'Ukrainian'], ['tr-TR', 'Türkçe', 'Turkish'],
  ['ar', 'العربية', 'Arabic'], ['he-IL', 'עברית', 'Hebrew'], ['fa-IR', 'فارسی', 'Persian'], ['ur-PK', 'اردو', 'Urdu'],
  ['hi-IN', 'हिन्दी (भारत)', 'Hindi (India)'], ['bn-BD', 'বাংলা', 'Bangla'], ['bho-IN', 'भोजपुरी', 'Bhojpuri'],
  ['gu-IN', 'ગુજરાતી', 'Gujarati'], ['mr-IN', 'मराठी', 'Marathi'], ['pa-IN', 'ਪੰਜਾਬੀ', 'Punjabi'],
  ['ta-IN', 'தமிழ்', 'Tamil'], ['te-IN', 'తెలుగు', 'Telugu'], ['kn-IN', 'ಕನ್ನಡ', 'Kannada'],
  ['ml-IN', 'മലയാളം', 'Malayalam'], ['ne-NP', 'नेपाली', 'Nepali'],
  ['zh-CN', '中文（简体）', 'Chinese (Simplified)'], ['zh-TW', '中文（繁體）', 'Chinese (Traditional)'],
  ['ja-JP', '日本語 (日本)', 'Japanese (Japan)'], ['ko-KR', '한국어 (대한민국)', 'Korean (South Korea)'],
  ['id-ID', 'Indonesia (Indonesia)', 'Indonesian (Indonesia)'], ['ms-MY', 'Bahasa Melayu', 'Malay'],
  ['fil-PH', 'Filipino', 'Filipino'], ['th-TH', 'ไทย', 'Thai'], ['vi-VN', 'Tiếng Việt', 'Vietnamese'],
  ['sw', 'Kiswahili', 'Swahili'], ['am-ET', 'አማርኛ', 'Amharic'], ['ha', 'Hausa', 'Hausa'],
  ['yo', 'Yorùbá', 'Yoruba'], ['zu', 'isiZulu', 'Zulu'],
];

const TEXTOS = {
  pt: {
    uso: 'Uso', idioma: 'Idioma', usoHoje: 'Mensagens hoje', usoTotal: 'mensagens enviadas', usoConversas: 'conversas salvas',
    escolhaIdioma: 'Escolha seu idioma', idiomaNota: 'O Astra passa a responder no idioma escolhido.',
    busca: 'Pesquisar idiomas', nada: 'Nenhum idioma encontrado.',
    limite: (d, m) => `Limite: ${d} mensagens por dia e ${m} por minuto.`, trocado: (n) => `Idioma: ${n}`,
  },
  en: {
    uso: 'Usage', idioma: 'Language', usoHoje: 'Messages today', usoTotal: 'messages sent', usoConversas: 'saved chats',
    escolhaIdioma: 'Choose your language', idiomaNota: 'Astra will reply in the language you choose.',
    busca: 'Search languages', nada: 'No language found.',
    limite: (d, m) => `Limit: ${d} messages per day and ${m} per minute.`, trocado: (n) => `Language: ${n}`,
  },
  es: {
    uso: 'Uso', idioma: 'Idioma', usoHoje: 'Mensajes hoy', usoTotal: 'mensajes enviados', usoConversas: 'conversaciones guardadas',
    escolhaIdioma: 'Elige tu idioma', idiomaNota: 'Astra responderá en el idioma elegido.',
    busca: 'Buscar idiomas', nada: 'Ningún idioma encontrado.',
    limite: (d, m) => `Límite: ${d} mensajes por día y ${m} por minuto.`, trocado: (n) => `Idioma: ${n}`,
  },
};

IDIOMAS.sort((a, b) => a[2].localeCompare(b[2]));
let idiomaEscolhido = lsGet('astra_idioma', 'pt-BR');
if (!IDIOMAS.some(([c]) => c === idiomaEscolhido)) idiomaEscolhido = 'pt-BR';
const txt = () => TEXTOS[idiomaEscolhido.slice(0, 2)] || TEXTOS.pt;

function aplicarIdioma() {
  const t = txt();
  document.documentElement.lang = idiomaEscolhido;
  document.querySelectorAll('[data-t]').forEach((el) => {
    if (typeof t[el.dataset.t] === 'string') el.textContent = t[el.dataset.t];
  });
  $('#idiomaBusca').placeholder = t.busca;
  const atual = IDIOMAS.find(([c]) => c === idiomaEscolhido);
  $('#idiomaAtual').textContent = atual ? atual[1].replace(/\s*[（(].*[)）]$/, '') : '';
}

function montarIdiomas(filtro = '') {
  const f = filtro.trim().toLowerCase();
  const lista = IDIOMAS.filter(([, n, e]) => !f || n.toLowerCase().includes(f) || e.toLowerCase().includes(f));
  $('#idiomaGrade').innerHTML = lista.length
    ? lista.map(([c, n, e]) => `<button type="button" class="idioma-item${c === idiomaEscolhido ? ' is-ativo' : ''}" data-codigo="${c}" role="option" aria-selected="${c === idiomaEscolhido}"><strong>${escapeHtml(n)}</strong><span>${escapeHtml(e)}</span></button>`).join('')
    : `<p class="idioma-vazio">${txt().nada}</p>`;
}

$('#idiomaGrade').addEventListener('click', (e) => {
  const item = e.target.closest('.idioma-item');
  if (!item) return;
  idiomaEscolhido = item.dataset.codigo;
  lsSet('astra_idioma', idiomaEscolhido);
  aplicarIdioma();
  $('#idiomaModal').hidden = true;
  toast(txt().trocado(IDIOMAS.find(([c]) => c === idiomaEscolhido)[1]), 1600);
});
$('#idiomaBusca').addEventListener('input', (e) => montarIdiomas(e.target.value));
$('#menuIdioma').onclick = () => {
  toggleAccountMenu(false);
  $('#idiomaBusca').value = '';
  montarIdiomas();
  $('#idiomaModal').hidden = false;
  icons();
  setTimeout(() => $('#idiomaBusca').focus(), 50);
};

const hojeISO = () => new Date().toISOString().slice(0, 10);
function lerUso() {
  let u;
  try { u = JSON.parse(lsGet('astra_uso', '{}')) || {}; } catch { u = {}; }
  if (u.dia !== hojeISO()) u = { dia: hojeISO(), hoje: 0, total: u.total || 0 };
  return u;
}
function contarUso() {
  const u = lerUso();
  u.hoje += 1;
  u.total = (u.total || 0) + 1;
  lsSet('astra_uso', JSON.stringify(u));
}
const numeroDoLimite = (texto) => parseInt((String(texto).match(/\d+/) || ['0'])[0], 10);
async function abrirUso() {
  toggleAccountMenu(false);
  const u = lerUso();
  $('#usoHoje').textContent = u.hoje;
  $('#usoTotal').textContent = u.total || 0;
  $('#usoConversas').textContent = Object.keys(chats).length;
  $('#usoLimite').textContent = '';
  $('#usoBarra').style.width = '0';
  $('#usoModal').hidden = false;
  icons();
  if (!isServed) return;
  try {
    const l = await (await fetch('/limites')).json();
    const porDia = numeroDoLimite(l.por_dia);
    const porMinuto = numeroDoLimite(l.por_minuto);
    $('#usoHoje').textContent = `${u.hoje} / ${porDia}`;
    $('#usoLimite').textContent = txt().limite(porDia, porMinuto);
    $('#usoBarra').style.width = `${Math.min(100, (u.hoje / (porDia || 1)) * 100)}%`;
  } catch {  }
}
$('#menuUso').onclick = abrirUso;

[['usoModal', 'usoFechar'], ['idiomaModal', 'idiomaFechar']].forEach(([modal, botao]) => {
  $('#' + botao).onclick = () => { $('#' + modal).hidden = true; };
  $('#' + modal).addEventListener('click', (e) => { if (e.target.id === modal) $('#' + modal).hidden = true; });
});
addEventListener('keydown', (e) => {
  if (e.key === 'Escape') ['usoModal', 'idiomaModal'].forEach((m) => { $('#' + m).hidden = true; });
});

aplicarIdioma();

(() => {
  const Reconhecimento = window.SpeechRecognition || window.webkitSpeechRecognition;
  const botao = $('#micBtn');
  if (!Reconhecimento || !botao) return;
  botao.hidden = false;

  let rec = null;
  let base = '';

  function parar() { if (rec) rec.stop(); }
  function marcar(ouvindo) {
    botao.classList.toggle('is-ouvindo', ouvindo);
    botao.setAttribute('aria-pressed', String(ouvindo));
    botao.title = ouvindo ? 'Parar' : 'Falar';
  }

  botao.addEventListener('click', () => {
    if (rec) { parar(); return; }
    rec = new Reconhecimento();
    rec.lang = idiomaEscolhido;
    rec.interimResults = true;
    rec.continuous = true;
    base = els.input.value ? els.input.value.replace(/\s*$/, ' ') : '';

    rec.onresult = (e) => {
      let falado = '';
      for (let i = 0; i < e.results.length; i++) falado += e.results[i][0].transcript;
      els.input.value = (base + falado).slice(0, 4000);
      autoGrow();
    };
    rec.onerror = (e) => {
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') toast('Permita o uso do microfone para falar.', 2200);
      else if (e.error === 'no-speech') toast('Não ouvi nada. Tente de novo.', 1600);
      else if (e.error !== 'aborted') toast('Não foi possível usar o microfone agora.', 2000);
    };
    rec.onend = () => { rec = null; marcar(false); els.input.focus(); };
    try { rec.start(); marcar(true); } catch { rec = null; }
  });

  els.send.addEventListener('click', parar, true);
  els.input.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) parar(); }, true);
})();

$('#logoBtn').onclick = () => {
  if (!window.AstraCarregando) { location.href = '/'; return; }
  AstraCarregando.ir('/', 'voltando');
};

const INTERFACE = {
  'Astra — Código, Revisão & Segurança': ['Astra — your AI for any question', 'Astra — tu IA para cualquier duda'],
  'Anônimo': ['Incognito', 'Incógnito'],
  'Sair do chat anônimo': ['Leave incognito chat', 'Salir del chat incógnito'],
  'Voltar para a página inicial': ['Back to home page', 'Volver a la página de inicio'],
  'Recolher menu': ['Collapse menu', 'Contraer menú'],
  'Abrir menu': ['Open menu', 'Abrir menú'],
  'Nova conversa': ['New chat', 'Nueva conversación'],
  'Recentes': ['Recents', 'Recientes'],
  'Configurações': ['Settings', 'Configuración'],
  'Apagar histórico': ['Delete history', 'Borrar historial'],
  '· Local': ['· Local', '· Local'],
  'Conversa anônima': ['Incognito chat', 'Conversación incógnita'],
  'Vamos programar': ["Let's get started", 'Empecemos'],
  'Você está no modo anônimo': ["You're in incognito mode", 'Estás en modo incógnito'],
  'Como posso ajudar você hoje?': ['How can I help you today?', '¿Cómo puedo ayudarte hoy?'],
  'Anexar arquivo': ['Attach file', 'Adjuntar archivo'],
  'Falar': ['Speak', 'Hablar'],
  'Parar': ['Stop', 'Detener'],
  'Enviar': ['Send', 'Enviar'],
  'Esta conversa não será salva no histórico deste navegador.': ["This chat won't be saved in this browser's history.", 'Esta conversación no se guardará en el historial de este navegador.'],
  'As mensagens continuam sendo enviadas ao servidor para gerar a resposta.': ['Messages are still sent to the server to generate the reply.', 'Los mensajes se siguen enviando al servidor para generar la respuesta.'],
  'Fechar': ['Close', 'Cerrar'],
  'Fechar configurações': ['Close settings', 'Cerrar configuración'],
  'Preferências': ['Preferences', 'Preferencias'],
  'Aparência': ['Appearance', 'Apariencia'],
  'Sistema': ['System', 'Sistema'],
  'Claro': ['Light', 'Claro'],
  'Escuro': ['Dark', 'Oscuro'],
  'Fonte do chat': ['Chat font', 'Fuente del chat'],
  'Monoespaçada': ['Monospace', 'Monoespaciada'],
  'Movimento': ['Motion', 'Movimiento'],
  'Reduzir animações da interface.': ['Reduce interface animations.', 'Reducir las animaciones de la interfaz.'],
  'Reduzido': ['Reduced', 'Reducido'],
  'Modelo': ['Model', 'Modelo'],
  'Modelo da IA': ['AI model', 'Modelo de IA'],
  'Vale para as próximas mensagens.': ['Applies to your next messages.', 'Se aplica a los próximos mensajes.'],
  'Padrão do servidor': ['Server default', 'Predeterminado del servidor'],
  'As conversas ficam salvas só no seu navegador.': ['Chats are saved only in your browser.', 'Las conversaciones se guardan solo en tu navegador.'],
  'Idiomas': ['Languages', 'Idiomas'],
  'Cancelar': ['Cancel', 'Cancelar'],
  'Apagar': ['Delete', 'Eliminar'],
  'Fixar': ['Pin', 'Fijar'],
  'Desafixar': ['Unpin', 'Desfijar'],
  'Mudar o nome': ['Rename', 'Cambiar el nombre'],
  'Remover': ['Remove', 'Quitar'],
  'Menu': ['Menu', 'Menú'],
  'Copiar': ['Copy', 'Copiar'],
  'Copiar código': ['Copy code', 'Copiar código'],
  'Copiado!': ['Copied!', '¡Copiado!'],
  'Não copiou': ["Couldn't copy", 'No se copió'],
  'Nenhuma conversa ainda.': ['No chats yet.', 'Aún no hay conversaciones.'],
  'Conversa fixada.': ['Chat pinned.', 'Conversación fijada.'],
  'Conversa desafixada.': ['Chat unpinned.', 'Conversación desfijada.'],
  'Nome alterado.': ['Name changed.', 'Nombre cambiado.'],
  'Conversa apagada.': ['Chat deleted.', 'Conversación eliminada.'],
  'Histórico apagado.': ['History deleted.', 'Historial borrado.'],
  'Excluir conversa?': ['Delete chat?', '¿Eliminar conversación?'],
  'Esta conversa será excluída permanentemente. Isso não pode ser desfeito.': ['This chat will be permanently deleted. This cannot be undone.', 'Esta conversación se eliminará permanentemente. Esto no se puede deshacer.'],
  'Apagar todo o histórico?': ['Delete all history?', '¿Borrar todo el historial?'],
  'Todas as conversas salvas serão excluídas permanentemente. Isso não pode ser desfeito.': ['All saved chats will be permanently deleted. This cannot be undone.', 'Todas las conversaciones guardadas se eliminarán permanentemente. Esto no se puede deshacer.'],
  'Usando o modelo padrão do servidor.': ['Using the server default model.', 'Usando el modelo predeterminado del servidor.'],
  'Permita o uso do microfone para falar.': ['Allow microphone access to speak.', 'Permite el uso del micrófono para hablar.'],
  'Não ouvi nada. Tente de novo.': ["I didn't hear anything. Try again.", 'No escuché nada. Inténtalo de nuevo.'],
  'Não foi possível usar o microfone agora.': ["Couldn't use the microphone right now.", 'No se pudo usar el micrófono ahora.'],
};
const ATRIBUTOS_TRADUZIVEIS = ['title', 'aria-label', 'placeholder'];
const originalDoTexto = new WeakMap();

function indiceInterface() {
  const l = idiomaEscolhido.slice(0, 2);
  return l === 'en' ? 0 : l === 'es' ? 1 : -1;
}
function eVersaoDe(valor, base) {
  const chave = base.trim();
  return valor === base || (INTERFACE[chave] || []).some((tr) => valor === base.replace(chave, tr));
}
function traduzirNo(no, i) {
  const pai = no.parentElement;
  if (!pai || (pai.closest('#messages') && !pai.closest('button'))) return;
  if (pai.closest('script, style, textarea')) return;
  let base = originalDoTexto.has(no) ? originalDoTexto.get(no) : no.nodeValue;
  if (!eVersaoDe(no.nodeValue, base)) base = no.nodeValue;
  const chave = base.trim();
  if (!INTERFACE[chave]) return;
  originalDoTexto.set(no, base);
  const valor = i < 0 ? base : base.replace(chave, INTERFACE[chave][i]);
  if (no.nodeValue !== valor) no.nodeValue = valor;
}
function traduzirAtributos(el, i) {
  ATRIBUTOS_TRADUZIVEIS.forEach((attr) => {
    if (!el.hasAttribute(attr)) return;
    const guardado = 'orig' + attr.replace(/-./g, (m) => m[1].toUpperCase()).replace(/^./, (m) => m.toUpperCase());
    const atual = el.getAttribute(attr);
    let base = el.dataset[guardado] ?? atual;
    if (!eVersaoDe(atual, base)) base = atual;
    if (!INTERFACE[base]) return;
    el.dataset[guardado] = base;
    const valor = i < 0 ? base : INTERFACE[base][i];
    if (el.getAttribute(attr) !== valor) el.setAttribute(attr, valor);
  });
}
function traduzirArvore(raiz, i = indiceInterface()) {
  if (raiz.nodeType === Node.TEXT_NODE) { traduzirNo(raiz, i); return; }
  if (raiz.nodeType !== Node.ELEMENT_NODE) return;
  if (!raiz.closest('#messages') || raiz.closest('button')) traduzirAtributos(raiz, i);
  raiz.querySelectorAll('[title], [aria-label], [placeholder]').forEach((el) => {
    if (!el.closest('#messages') || el.closest('button')) traduzirAtributos(el, i);
  });
  const andar = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
  while (andar.nextNode()) traduzirNo(andar.currentNode, i);
}
function traduzirInterface() {
  const i = indiceInterface();
  const tituloBase = document.documentElement.dataset.tituloOriginal || document.title;
  document.documentElement.dataset.tituloOriginal = tituloBase;
  document.title = i < 0 || !INTERFACE[tituloBase] ? tituloBase : INTERFACE[tituloBase][i];
  traduzirArvore(document.body, i);
}
new MutationObserver((mudancas) => {
  if (indiceInterface() < 0) return;
  mudancas.forEach((m) => {
    if (m.type === 'characterData') traduzirNo(m.target, indiceInterface());
    else if (m.type === 'attributes') traduzirAtributos(m.target, indiceInterface());
    else m.addedNodes.forEach((n) => traduzirArvore(n));
  });
}).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATRIBUTOS_TRADUZIVEIS });

const aplicarIdiomaSemInterface = aplicarIdioma;
aplicarIdioma = function () { aplicarIdiomaSemInterface(); traduzirInterface(); };
traduzirInterface();
