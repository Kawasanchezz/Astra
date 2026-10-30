import os
import logging
import mimetypes
import signal
import sys
import threading
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from config import (
    ALLOWED_ORIGINS, FLASK_DEBUG, PORT,
    MAX_REQUEST_SIZE, RATE_LIMIT_DEFAULT, RATE_LIMIT_CHAT, RATE_LIMIT_DIARIO,
    MAX_INPUT_LENGTH, RATELIMIT_STORAGE_URI, FORCE_HTTPS, RATE_LIMIT_GLOBAL,
    TRUSTED_PROXY_COUNT, ALLOWED_MODELS, GROQ_MODEL, APP_ENV, GROQ_API_KEY,
    CHAT_ENABLED, GROQ_MAX_RETRIES, MAX_HISTORY_CHARS, MAX_CONCURRENT_REQUESTS,
    IS_PRODUCTION, IDIOMAS, validar_configuracao
)
from core.prompt_mestre import PromptMestre
from services.ia_service import obter_resposta_ia

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger(__name__)

validar_configuracao()

FRONTEND_DIR = os.environ.get("FRONTEND_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "landing-page")
)
logger.info("Servindo frontend de: %s", FRONTEND_DIR)

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")

app = Flask(__name__,
            static_folder=FRONTEND_DIR,
            static_url_path="")

if TRUSTED_PROXY_COUNT > 0:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=TRUSTED_PROXY_COUNT,
        x_proto=TRUSTED_PROXY_COUNT,
        x_host=TRUSTED_PROXY_COUNT,
        x_prefix=TRUSTED_PROXY_COUNT,
    )
    logger.info("ProxyFix ativo: confiando em %d proxy(s).", TRUSTED_PROXY_COUNT)
else:
    logger.info("ProxyFix desativado: X-Forwarded-* ignorado (IP real do socket).")
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_SIZE

CORS(app, origins=ALLOWED_ORIGINS, methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type"], supports_credentials=False, max_age=600)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT],
    storage_uri=RATELIMIT_STORAGE_URI
)

system_prompt = PromptMestre().get_prompt()

_vagas_ia = threading.BoundedSemaphore(MAX_CONCURRENT_REQUESTS)

@app.before_request
def enforce_https():
    if FORCE_HTTPS and not request.is_secure:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

_EXTENSOES_BLOQUEADAS = (".py", ".pyc", ".md", ".env", ".ini", ".cfg", ".toml",
                         ".yml", ".yaml", ".log", ".bak", ".sql", ".sqlite", ".db",
                         ".pem", ".key", ".map")

@app.before_request
def bloquear_arquivos_sensiveis():
    caminho = request.path.lower()
    partes = [p for p in caminho.split("/") if p]
    if any(p.startswith(".") for p in partes) or caminho.endswith(_EXTENSOES_BLOQUEADAS):
        return jsonify({"erro": "Nao encontrado"}), 404

@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=(self)"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    if FORCE_HTTPS or IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "font-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    return response

@app.route("/")
def index():
    return app.send_static_file("home.html")

@app.route("/app")
def aplicativo():
    return app.send_static_file("index.html")

def _ip_anonimo(ip):
    """Trunca o IP para log: identifica a origem sem guardar dado pessoal.

    203.0.113.42 -> 203.0.113.x   |   2001:db8:85a3::1 -> 2001:db8:85a3::
    """
    if not ip:
        return "?"
    if ":" in ip:
        return ":".join(ip.split(":")[:3]) + "::"
    partes = ip.split(".")
    return ".".join(partes[:3]) + ".x" if len(partes) == 4 else "?"

@app.route("/chat", methods=["POST"])
@limiter.limit(RATE_LIMIT_CHAT)
@limiter.limit(RATE_LIMIT_DIARIO)
@limiter.limit(RATE_LIMIT_GLOBAL, key_func=lambda: "global")
def chat():
    if not CHAT_ENABLED:
        return jsonify({"erro": "O chat esta temporariamente indisponivel."}), 503

    if IS_PRODUCTION:
        origem = request.headers.get("Origin")
        mesmo_site = request.host_url.rstrip("/")
        if origem not in ALLOWED_ORIGINS and origem != mesmo_site:
            return jsonify({"erro": "Origem nao permitida"}), 403

    dados = request.get_json(silent=True)

    if not dados or not isinstance(dados, dict):
        return jsonify({"erro": "Dados invalidos"}), 400

    mensagem = dados.get("mensagem", "")
    if not isinstance(mensagem, str):
        return jsonify({"erro": "Dados invalidos"}), 400
    mensagem = mensagem.strip()
    if not mensagem:
        return jsonify({"erro": "Mensagem vazia"}), 400

    if len(mensagem) > MAX_INPUT_LENGTH:
        return jsonify({"erro": "Texto muito longo"}), 400

    historico = dados.get("historico", [])
    modelo = dados.get("modelo")
    if not isinstance(modelo, str):
        modelo = None
    modelo_log = modelo if modelo in ALLOWED_MODELS else None
    idioma = dados.get("idioma")
    if not isinstance(idioma, str) or idioma not in IDIOMAS:
        idioma = None

    logger.info("chat ip=%s msg=%dch hist=%dmsg modelo=%s",
                _ip_anonimo(request.remote_addr),
                len(mensagem),
                len(historico) if isinstance(historico, list) else 0,
                modelo_log or "padrao")

    if not _vagas_ia.acquire(blocking=False):
        logger.warning("concorrencia no teto (%d chamadas simultaneas); recusando",
                       MAX_CONCURRENT_REQUESTS)
        return jsonify({"erro": "Muitas conversas ao mesmo tempo. Tente em instantes."}), 429

    try:
        resposta = obter_resposta_ia(system_prompt, mensagem, historico, modelo, idioma)
    finally:
        _vagas_ia.release()

    return jsonify({"resposta": resposta})

@app.route("/models")
def models():
    return jsonify({"modelos": sorted(ALLOWED_MODELS), "padrao": GROQ_MODEL})

@app.route("/limites")
def limites():
    return jsonify({
        "por_minuto": RATE_LIMIT_CHAT,
        "por_dia": RATE_LIMIT_DIARIO,
        "max_caracteres": MAX_INPUT_LENGTH,
    })

@app.route("/health")
def health():
    if IS_PRODUCTION:
        return jsonify({"status": "Online e Seguro!", "ia_configurada": bool(GROQ_API_KEY)})
    return jsonify({
        "status": "Online e Seguro!",
        "ambiente": APP_ENV,
        "proxies_confiaveis": TRUSTED_PROXY_COUNT,
        "rate_limit_ip": RATE_LIMIT_CHAT,
        "rate_limit_diario": RATE_LIMIT_DIARIO,
        "rate_limit_global": RATE_LIMIT_GLOBAL,
        "chat_ativo": CHAT_ENABLED,
        "max_historico_chars": MAX_HISTORY_CHARS,
        "max_request_kb": MAX_REQUEST_SIZE // 1024,
        "groq_max_retries": GROQ_MAX_RETRIES,
        "max_concorrencia": MAX_CONCURRENT_REQUESTS,
        "ia_configurada": bool(GROQ_API_KEY),
    })

@app.errorhandler(413)
def payload_too_large(e):
    return jsonify({"erro": "Requisicao muito grande"}), 413

@app.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({"erro": "Calma! Muitas mensagens. Espera um pouco."}), 429

@app.errorhandler(500)
def internal_error(e):
    logger.error("Erro interno: %s", type(e).__name__)
    return jsonify({"erro": "Ops, algo deu errado no servidor."}), 500

@app.errorhandler(HTTPException)
def erro_http(e):
    if e.code in (413, 429):
        return e
    return jsonify({"erro": "Requisicao invalida" if (e.code or 500) < 500 else "Erro no servidor"}), e.code or 500

@app.errorhandler(Exception)
def erro_inesperado(e):
    logger.error("Excecao nao tratada: %s", type(e).__name__)
    return jsonify({"erro": "Ops, algo deu errado no servidor."}), 500

def graceful_shutdown(sig, frame):
    logger.info("Desligando o servidor...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    logger.info("Bot rodando na porta %d", PORT)
    app.run(debug=FLASK_DEBUG, host="127.0.0.1", port=PORT)
