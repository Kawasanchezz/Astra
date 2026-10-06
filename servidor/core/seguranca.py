"""
Guarda de segurança: primeira camada, determinística, ANTES do modelo.

O que faz
- Recusa, sem gastar uma chamada ao modelo, só os casos INEQUÍVOCOS: pedido do
  prompt interno, jailbreak imperativo, conteúdo sexual/+18, sexualização de
  menores, ferramenta de ataque, saída gigante.
- Mascara segredos (chaves, tokens, senhas) antes de a mensagem sair do servidor.

O que NÃO faz
- Não decide por palavra solta. Cada regra combina uma INTENÇÃO (verbo de pedido)
  com um OBJETO, e é desligada por contexto técnico/educacional legítimo
  ("filtro de moderação", "como detectar keylogger"). Nesses casos a mensagem
  segue para o modelo, que avalia a intenção com a conversa inteira (ver
  core/prompt_mestre.py).
- Não é a única defesa. Regex sempre tem lacunas; ela barra o óbvio barato e o
  prompt e o validador cobrem o resto.
"""
from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from dataclasses import dataclass

CAT_PROMPT = "prompt_interno"
CAT_JAILBREAK = "jailbreak"
CAT_SEXUAL = "sexual"
CAT_MENORES = "menores"
CAT_OFENSIVO = "ofensivo"
CAT_TAMANHO = "tamanho"

RESPOSTAS = {
    CAT_PROMPT: (
        "Não posso fornecer minhas instruções internas, mas posso explicar de forma "
        "geral como funciono e quais tipos de tarefas consigo realizar."
    ),
    CAT_JAILBREAK: (
        "Não posso alterar minhas regras, mas posso ajudar com programação, "
        "tecnologia ou outro assunto. O que você precisa?"
    ),
    CAT_SEXUAL: (
        "Não posso ajudar com esse tipo de conteúdo. Posso ajudar com outro assunto."
    ),
    CAT_MENORES: (
        "Não posso ajudar com isso. Posso ajudar com outro assunto."
    ),
    CAT_OFENSIVO: (
        "Não posso ajudar a criar ferramentas de ataque. Posso ajudar com o lado "
        "defensivo: como detectar, mitigar ou corrigir esse tipo de ameaça."
    ),
    CAT_TAMANHO: (
        "Esse volume não se justifica numa única resposta. Posso gerar um recorte "
        "útil ou dividir em partes menores: me diga o objetivo."
    ),
}


@dataclass(frozen=True)
class Veredito:
    """Resultado da avaliação de uma mensagem."""

    bloqueado: bool = False
    categoria: str | None = None
    resposta: str | None = None
    # Texto de injeção dentro de código/dados (ou numa mensagem longa de
    # discussão): não bloqueia, mas o modelo precisa tratá-lo como dado.
    dado_com_instrucao: bool = False


def _bloqueio(categoria: str) -> Veredito:
    return Veredito(bloqueado=True, categoria=categoria, resposta=RESPOSTAS[categoria])


# ── normalização ─────────────────────────────────────────────────────────────
# Letras cirílicas/gregas que parecem latinas (ataque de homóglifos) e leetspeak.
_CONFUSAVEIS = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y",
    "і": "i", "ѕ": "s", "ο": "o", "α": "a", "ε": "e", "ι": "i", "ρ": "p",
})
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
                       "@": "a", "$": "s", "!": "i"})
_INVISIVEIS = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
# "s.e.x.o", "p-o-r-n": letras soltas separadas por pontuacao viram a palavra
_LETRAS_SEPARADAS = re.compile(r"\b(?:\w[.\-_*]){3,}\w\b")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem caracteres invisíveis e sem homóglifos."""
    t = _INVISIVEIS.sub("", texto).translate(_CONFUSAVEIS)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = _LETRAS_SEPARADAS.sub(lambda m: re.sub(r"[.\-_*]", "", m.group(0)), t)
    return re.sub(r"\s+", " ", t.lower()).strip()


_BLOCO_CODIGO = re.compile(r"```.*?(?:```|\Z)", re.DOTALL)
_CODIGO_INLINE = re.compile(r"`[^`\n]*`")
# Trecho entre aspas duplas = texto citado/colado ("resuma este texto: '...'"),
# ou seja, DADO. Só aspas duplas: a aspa simples também é apóstrofo.
_TRECHO_CITADO = re.compile(r'"[^"\n]{12,}"|“[^”\n]{12,}”|«[^»\n]{12,}»')
_LINHA_COMENTARIO = re.compile(r"^\s*(?:#|//|--|/\*|\*|<!--).*$", re.MULTILINE)


def _sem_codigo(texto: str) -> str:
    """O que a pessoa escreveu FORA de código, comentários e trechos citados."""
    t = _BLOCO_CODIGO.sub(" ", texto)
    t = _CODIGO_INLINE.sub(" ", t)
    t = _TRECHO_CITADO.sub(" ", t)
    return _LINHA_COMENTARIO.sub(" ", t)


def _decodificar_base64(texto: str) -> list[str]:
    """Textos legíveis escondidos em Base64 (o formato não muda o conteúdo)."""
    achados: list[str] = []
    for token in re.findall(r"[A-Za-z0-9+/]{24,}={0,2}", texto)[:3]:
        try:
            bruto = base64.b64decode(token + "=" * (-len(token) % 4), validate=True)
            decodificado = bruto.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue
        legivel = sum(c.isprintable() or c.isspace() for c in decodificado)
        if len(decodificado) >= 10 and legivel / len(decodificado) > 0.9:
            achados.append(decodificado)
    return achados


# ── regras ───────────────────────────────────────────────────────────────────
# Contexto técnico/educacional que DESLIGA o bloqueio automático: a mensagem
# segue para o modelo, que julga a intenção. Sem isso, "gere uma lista de
# palavras para o filtro de conteúdo adulto" seria recusada por engano.
_CONTEXTO_LEGITIMO = re.compile(
    r"\b(filtr\w*|moderac\w*|moderar|detect\w*|bloque\w*|classific\w*|denunci\w*|"
    r"proteg\w*|defend\w*|defesa|mitig\w*|preven\w*|analis\w*|remov\w*|identific\w*|"
    r"antivirus|antimalware|sandbox|lgpd|compliance|educac\w*|biolog\w*|anatomi\w*|"
    r"pubert\w*|saude|pediatr\w*|psicolog\w*|escola)\b"
)

_VERBO_PEDIDO = (
    r"(?:escrev\w+|gere|gerar|gera|crie|criar|cria|faca|fazer|conte|contar|descrev\w+|"
    r"narr\w+|mostr\w+|mand\w+|envi\w+|me\s+d[ea]|quero|preciso|simul\w+|finj\w+|"
    r"continu\w+|traduz\w+|produz\w+|retorn\w+|imprim\w+|exib\w+|elabor\w+|redij\w+|"
    r"forne\w+|write|generate|create|make|tell|describe|show|send|give|roleplay|"
    r"pretend|i\s+want)"
)

_OBJETO_SEXUAL = (
    r"(?:conto\s+erotic\w*|historia\s+(?:erotic\w*|sexual|safada|hot|picante)|"
    r"cena\s+(?:de\s+sexo|sexual|erotic\w*|hot)|pornograf\w+|porno\w*|\bporn\b|\bnudes?\b|"
    r"fotos?\s+(?:nua|nuas|nu|nus|pelad\w+)|"
    r"conteudo\s+(?:sexual|adulto|\+?18|18\+|explicito|erotico|safado|nsfw)|"
    r"sexo\s+explicito|sexting|fanfic\w*\s+(?:erotic\w*|sexual|hentai)|hentai|\bnsfw\b|"
    r"\bxxx\b|\berotic\w*|sexually\s+explicit|dirty\s+talk|"
    r"conversa\s+(?:safada|sexual|erotica|picante)|texto\s+(?:erotico|safado|sexual|picante)|"
    r"roleplay\s+(?:sexual|erotic\w*)|sexual\s+roleplay|me\s+excit\w+|"
    r"transar\s+comigo|sexo\s+comigo)"
)
# pedido direto ("escreva um conto erotico") ou o objeto antes do verbo
# ("sexo explicito: escreva uma cena")
_PEDIDO_SEXUAL = re.compile(
    rf"\b{_VERBO_PEDIDO}\b.{{0,60}}{_OBJETO_SEXUAL}"
    rf"|{_OBJETO_SEXUAL}.{{0,30}}\b(?:escrev\w+|gere|crie|descrev\w+|write|generate|describe)\b"
)

# Menor + termo sexual EXPLÍCITO. "Educação sexual para adolescentes" não casa:
# "sexual" sozinho não está na lista de termos explícitos.
_MENOR = (
    r"(?:crianc\w+|menin[ao]s?|garot[ao]s?|adolescent\w*|infantil|infantis|loli\w*|shota|"
    r"underage|\bminors?\b|child\w*|\bkids?\b|teen\w*|novinh[ao]s?|"
    r"menor(?:es)?\s+de\s+idade|\b(?:[0-9]|1[0-7])\s*anos\b|\b(?:[0-9]|1[0-7])\s*years?\s*old)"
)
_SEXUAL_EXPLICITO = (
    r"(?:erotic\w*|porn\w*|nude\w*|\bnsfw\b|hentai|pelad[ao]s?|\bnu[ao]s?\b|safad[ao]s?|"
    r"(?:cena|conto|historia|texto|conteudo|relato)s?\s+sexual\w*|"
    r"excit\w+|sexy|sensual\w*|sexo\s+(?:explicito|com)|transar|seduz\w*)"
)
_MENOR_SEXUAL = re.compile(
    rf"{_MENOR}.{{0,50}}{_SEXUAL_EXPLICITO}|{_SEXUAL_EXPLICITO}.{{0,50}}{_MENOR}"
)

_OBJETO_OFENSIVO = (
    r"(?:ransomware|keylogger|\bmalware\b|trojan|cavalo\s+de\s+troia|botnet|backdoor|"
    r"rootkit|infostealer|\bstealer\b|spyware|\bddos\b|dos\s+attack|"
    r"ataque\s+de\s+negacao|credential\s+stuffing|phishing\s+(?:kit|page|site)|"
    r"pagina\s+falsa\s+de\s+(?:login|banco)|exploit\s+(?:funcional|zero)|"
    r"payload\s+(?:de\s+ataque|malicios\w+)|"
    r"brute[\s-]?force\s+(?:tool|ferramenta|script|attack)|"
    r"forca\s+bruta\s+(?:em|contra|ferramenta|script))"
)
_VERBO_CRIAR = (
    r"(?:escrev\w+|crie|criar|cria|gere|gerar|faca|fazer|desenvolv\w+|programe|"
    r"construa|monte|me\s+d[ea]|write|create|build|generate|make|develop|code)"
)
_PEDIDO_OFENSIVO = re.compile(rf"\b{_VERBO_CRIAR}\b.{{0,40}}{_OBJETO_OFENSIVO}")
_INVASAO = re.compile(
    r"\bcomo\s+(?:se\s+)?(?:roubar|hackear|invadir|clonar)\b.{0,30}"
    r"\b(?:senha|conta|wi-?fi|instagram|facebook|whatsapp|cartao|servidor|sistema)\b"
)

_PEDIDOS_OVERRIDE = (
    re.compile(r"\bignor\w*\s+(?:todas?\s+)?(?:as\s+|suas\s+|essas\s+|estas\s+)?"
               r"(?:regras|instrucoes|instrucao|diretrizes|restricoes)\b"),
    re.compile(r"\bignore\s+(?:all\s+|any\s+)?(?:the\s+)?(?:previous|prior|above|earlier|your)"
               r"\s+(?:instructions|rules|prompts?|guidelines)"),
    re.compile(r"\b(?:esqueca|esquece|desconsidere|descarte|disregard|forget)\s+"
               r"(?:tudo|todas?|all|everything)\b.{0,30}"
               r"(?:regras|instrucoes|rules|instructions|acima|anteriores|antes|above|previous|before)"),
    re.compile(r"\b(?:voce|you)\s+(?:agora\s+)?(?:e|sera|are|is)\s+(?:agora\s+)?(?:o\s+)?dan\b"),
    re.compile(r"\bsystem\s*override\b|\bdo\s+anything\s+now\b"),
    re.compile(r"\b(?:voce|you)\s+(?:agora\s+)?(?:esta|e|are|is)\s+(?:agora\s+)?(?:em\s+|no\s+|in\s+)?"
               r"(?:modo|mode)\s+(?:\w+\s+)?"
               r"(?:dan|deus|god|sem\s+(?:restricoes|filtros?|regras|limites)|irrestrito|"
               r"unrestricted|unfiltered|jailbreak|desenvolvedor|developer|admin|debug)\b"),
    re.compile(r"\b(?:ative|ativar|habilite|entre\s+em|enter|activate|enable)\b.{0,20}"
               r"\b(?:modo|mode)\s+(?:dan|deus|god|sem\s+(?:restricoes|filtros?|regras|limites)|"
               r"irrestrito|unrestricted|unfiltered)\b"),
    re.compile(r"\b(?:responda|aja|act|respond|answer)\b.{0,25}\b(?:sem|without)\s+"
               r"(?:nenhum\s+|any\s+)?(?:filtros?|restricoes|regras|limites|censura|"
               r"restrictions|filters|rules|censorship)\b"),
    re.compile(r"\b(?:finja|pretend|aja\s+como|you\s+are\s+now)\b.{0,40}"
               r"\b(?:sem\s+(?:filtros?|restricoes|regras|limites|etica)|dan|"
               r"unrestricted|unfiltered|evil|malicios\w+)\b"),
)

_PEDIDOS_PROMPT = (
    re.compile(r"\b(?:mostr\w+|revel\w+|exib\w+|imprim\w+|repit\w+|copi\w+|diga|digam|"
               r"me\s+d[ea]|passe|liste|cite|transcrev\w+|show|reveal|print|repeat|output|"
               r"display|leak|tell\s+me|give\s+me|recite|what\s+(?:is|are))\b.{0,40}"
               r"\b(?:seu|sua|seus|suas|teu|tua|your|its)\s+(?:system\s*)?"
               r"(?:prompts?|instruc\w+|regras|diretrizes|configurac\w+|instructions|rules|guidelines)"),
    re.compile(r"\bqual\s+(?:e|eh|sao)\s+(?:o\s+|as\s+)?(?:seu|sua|seus|suas)\s+"
               r"(?:system\s*)?(?:prompt|instruc\w+|regras)"),
    re.compile(r"\b(?:system\s*prompt|prompt\s+(?:mestre|do\s+sistema|interno|inicial|oculto))\b"
               r".{0,40}\b(?:acima|inteiro|completo|literal|palavra\s+por\s+palavra|"
               r"verbatim|na\s+integra)"),
    re.compile(r"\b(?:repeat|repita|reescreva)\b.{0,20}\b(?:everything|tudo|text|texto)\b"
               r".{0,15}\b(?:above|acima)\b"),
)

# Mensagens longas que contêm a frase costumam ser discussão ou texto colado
# (ex.: "como me proteger de 'ignore as instruções anteriores'?"). Nelas a
# frase vira dado para o modelo julgar, não motivo de recusa automática.
_LIMITE_IMPERATIVO = 300

_PEDIDO_VOLUME = re.compile(
    r"\b(?:gere|gerar|escreva|crie|imprima|repita|liste|write|generate|print|repeat|list)\b"
    r".{0,40}?(\d[\d.,]*)\s*(mil\s+)?"
    r"(?:linhas|vezes|palavras|paragrafos|itens|times|lines|words|paragraphs|items)\b"
)
_SEM_FIM = re.compile(
    r"\b(?:continue|repita|escreva|gere|keep|repeat|write|generate)\b.{0,25}"
    r"\b(?:indefinidamente|infinitamente|para\s+sempre|sem\s+parar|forever|infinitely|endlessly)\b"
)
_LIMITE_VOLUME = 5000


def _volume_excessivo(texto: str) -> bool:
    if _SEM_FIM.search(texto):
        return True
    for achado in _PEDIDO_VOLUME.finditer(texto):
        digitos = re.sub(r"[.,]", "", achado.group(1))
        if not digitos:
            continue
        quantidade = int(digitos) * (1000 if achado.group(2) else 1)
        if quantidade >= _LIMITE_VOLUME:
            return True
    return False


def _casa(regras, texto: str) -> bool:
    return any(regra.search(texto) for regra in regras)


def _avaliar_texto(texto: str) -> Veredito:
    inteiro = normalizar(texto)
    fora = normalizar(_sem_codigo(texto))
    # variantes com leetspeak ("p0rn0") só para as regras de intenção; os números
    # originais ficam intactos para a regra de volume
    inteiro_leet = inteiro.translate(_LEET)
    fora_leet = fora.translate(_LEET)
    legitimo = bool(_CONTEXTO_LEGITIMO.search(inteiro))

    if _MENOR_SEXUAL.search(inteiro) or _MENOR_SEXUAL.search(inteiro_leet):
        return _bloqueio(CAT_MENORES)

    if not legitimo and (_PEDIDO_SEXUAL.search(fora) or _PEDIDO_SEXUAL.search(fora_leet)):
        return _bloqueio(CAT_SEXUAL)

    # Prompt interno e jailbreak: bloqueia o pedido imperativo escrito pela
    # pessoa. Se a frase só aparece dentro de código, ou numa mensagem longa de
    # discussão, passa como DADO e o modelo é avisado.
    for categoria, regras in ((CAT_PROMPT, _PEDIDOS_PROMPT), (CAT_JAILBREAK, _PEDIDOS_OVERRIDE)):
        if _casa(regras, fora) or _casa(regras, fora_leet):
            if len(fora) <= _LIMITE_IMPERATIVO:
                return _bloqueio(categoria)
            return Veredito(dado_com_instrucao=True)
        if _casa(regras, inteiro):
            return Veredito(dado_com_instrucao=True)

    if not legitimo and (_PEDIDO_OFENSIVO.search(fora) or _INVASAO.search(fora)):
        return _bloqueio(CAT_OFENSIVO)

    if _volume_excessivo(fora):
        return _bloqueio(CAT_TAMANHO)

    return Veredito()


def avaliar_mensagem(texto: str) -> Veredito:
    """Avalia a mensagem (e qualquer Base64 legível dentro dela)."""
    pior = Veredito()
    for candidato in (texto, *_decodificar_base64(texto)):
        veredito = _avaliar_texto(candidato)
        if veredito.bloqueado:
            return veredito
        if veredito.dado_com_instrucao:
            pior = veredito
    return pior


# ── segredos ────────────────────────────────────────────────────────────────
_SEGREDOS_COM_PREFIXO = (
    re.compile(r"\b(gsk_)[A-Za-z0-9]{20,}"),
    re.compile(r"\b(sk-(?:proj-|ant-)?)[A-Za-z0-9_-]{20,}"),
    re.compile(r"\b(AKIA)[0-9A-Z]{16}\b"),
    re.compile(r"\b(ghp_|gho_|ghs_|ghu_|github_pat_)[A-Za-z0-9_]{30,}"),
    re.compile(r"\b(xox[abprs]-)[A-Za-z0-9-]{10,}"),
    re.compile(r"\b(AIza)[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\b(eyJ)[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
)
_CHAVE_PRIVADA = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)", re.DOTALL
)
_URL_COM_SENHA = re.compile(r"\b([a-z][a-z0-9+.-]*://[^\s:/@]+:)([^\s@/]+)(@)", re.IGNORECASE)
_ATRIBUICAO = re.compile(
    r"(?i)\b(password|passwd|senha|secret|client_secret|api[_-]?key|apikey|"
    r"access[_-]?token|auth[_-]?token|token|private[_-]?key)\b(\s*[:=]\s*)(['\"]?)([^\s'\";,]{8,})\3"
)
# valor que é só marcador/leitura do ambiente, não um segredo de verdade
_PLACEHOLDER = re.compile(
    r"(?i)coloque|your|seu_|sua_|xxx|\*{3,}|example|exemplo|changeme|placeholder|"
    r"[<>{}]|\$|%|environ|getenv|process\.env|^(?:null|none|true|false)$"
)
_MASCARA = "********"


def _mascarar_atribuicao(achado: re.Match) -> str:
    nome, separador, aspas, valor = achado.groups()
    if _PLACEHOLDER.search(valor):
        return achado.group(0)
    return f"{nome}{separador}{aspas}{_MASCARA}{aspas}"


def mascarar_segredos(texto: str) -> tuple[str, bool]:
    """Troca segredos por marcadores. Devolve (texto_mascarado, achou_algum)."""
    original = texto
    for regra in _SEGREDOS_COM_PREFIXO:
        texto = regra.sub(lambda m: m.group(1) + "****", texto)
    texto = _CHAVE_PRIVADA.sub("[chave privada removida]", texto)
    texto = _URL_COM_SENHA.sub(lambda m: m.group(1) + _MASCARA + m.group(3), texto)
    texto = _ATRIBUICAO.sub(_mascarar_atribuicao, texto)
    return texto, texto != original
