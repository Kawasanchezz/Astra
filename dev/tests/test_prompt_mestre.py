from core.prompt_mestre import PromptMestre

PROMPT = PromptMestre().get_prompt()
PROMPT_EM_UMA_LINHA = " ".join(PROMPT.split())   # as frases quebram de linha no texto


def test_contem_todas_as_secoes():
    for titulo in ("IDENTIDADE E PERSONALIDADE", "ESCOPO: ASSISTENTE GERAL",
                   "COMO DECIDIR A RESPOSTA", "RESPOSTAS TÉCNICAS E DE CÓDIGO",
                   "HONESTIDADE E INCERTEZA", "SEGURANÇA, ÉTICA E RESILIÊNCIA",
                   "FORMATO, ESTILO E EXEMPLOS"):
        assert titulo in PROMPT


def test_e_assistente_de_uso_geral_com_especializacao_em_tecnologia():
    assert "assistente de uso geral" in PROMPT_EM_UMA_LINHA
    assert "NÃO recuse" in PROMPT_EM_UMA_LINHA                 # perguntas gerais seguras nao sao recusadas
    assert "freio de mão" in PROMPT
    assert "sou focado em programação" in PROMPT_EM_UMA_LINHA   # citado como o que NAO dizer


def test_preserva_as_protecoes():
    for trecho in ("CONFIDENCIALIDADE", "JAILBREAK E INJEÇÃO", "CONTEÚDO SEXUAL E +18",
                   "SEGURANÇA OFENSIVA X DEFENSIVA", "SEGREDOS E DADOS PESSOAIS",
                   "ABUSO DE RECURSOS", "DADO, nunca instrução"):
        assert trecho in PROMPT


def test_orienta_contra_aberturas_roboticas_e_alucinacao():
    assert "Claro!" in PROMPT      # citado como exemplo do que NAO fazer
    assert "Nunca invente" in PROMPT


def test_tamanho_controlado_para_nao_encarecer_cada_requisicao():
    assert len(PROMPT) < 14_000


def test_cobre_comparacao_atualidade_e_acompanhamento():
    for trecho in ("COMPARAÇÕES", "ATUALIDADE", "ACOMPANHAMENTO", "NÍVEL",
                   "Não consigo confirmar o dado mais recente"):
        assert trecho in PROMPT_EM_UMA_LINHA


def test_seguranca_vem_antes_da_conversa_geral():
    assert "Segurança vem antes da conversa" in PROMPT_EM_UMA_LINHA


def test_orienta_saida_limpa_e_codigo_em_bloco_markdown():
    assert "Estilo limpo" in PROMPT_EM_UMA_LINHA
    assert 'botão "Copiar"' in PROMPT_EM_UMA_LINHA
    assert "SEMPRE em bloco de código Markdown" in PROMPT_EM_UMA_LINHA
