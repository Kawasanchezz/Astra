from core.prompt_mestre import PromptMestre
from core.seguranca import CAT_JAILBREAK, CAT_PROMPT, RESPOSTAS
from core.validador import RESPOSTA_VAZIA, validar_resposta, vazou_prompt

PROMPT = PromptMestre().get_prompt()


def test_resposta_normal_passa_intacta():
    resposta = "HTTPS adiciona TLS ao HTTP, protegendo os dados em trânsito."
    assert validar_resposta(resposta, PROMPT) == resposta


def test_resposta_vazia_vira_aviso():
    assert validar_resposta("   ", PROMPT) == RESPOSTA_VAZIA
    assert validar_resposta(None, PROMPT) == RESPOSTA_VAZIA


def test_copia_do_prompt_e_detectada_e_substituida():
    trecho = PROMPT[PROMPT.index("## 6."):][:900]
    assert vazou_prompt(trecho, PROMPT)
    assert validar_resposta(trecho, PROMPT) == RESPOSTAS[CAT_PROMPT]


def test_recusa_padrao_citada_pelo_modelo_nao_conta_como_vazamento():
    assert not vazou_prompt(RESPOSTAS[CAT_JAILBREAK], PROMPT)
    assert not vazou_prompt(RESPOSTAS[CAT_PROMPT], PROMPT)


def test_parafrase_geral_nao_conta_como_vazamento():
    resposta = ("Sigo regras de segurança: não revelo configurações internas e trato "
                "código recebido como dado, não como instrução.")
    assert not vazou_prompt(resposta, PROMPT)


def test_segredo_na_resposta_e_mascarado():
    chave = "gsk_" + "Z9y8X7w6V5u4T3s2R1q0P9o8N7m6"
    resposta = f"Sua chave {chave} está exposta, revogue."
    saida = validar_resposta(resposta, PROMPT)
    assert chave not in saida
    assert "gsk_****" in saida
