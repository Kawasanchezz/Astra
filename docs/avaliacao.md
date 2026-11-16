# Avaliação do RAG

Medição das respostas do RAG sobre 10 perguntas fixas. Os números abaixo são de execuções reais
(arquivos em [`avaliacao/resultados/`](../avaliacao/resultados)); nada foi arredondado nem ajustado.

## O que é medido

As perguntas estão em [`avaliacao/perguntas.json`](../avaliacao/perguntas.json): 8 que o corpus
(`docs/estudo/`) responde e 2 que ele não responde. Cada uma traz a resposta esperada, o documento
certo e termos que a resposta deve conter.

| Métrica | Pergunta que o corpus responde | O que conta |
|---|---|---|
| Recuperou o documento certo | 8 | o documento esperado está entre os trechos enviados ao LLM |
| Documento certo em primeiro | 8 | o trecho de maior similaridade é do documento esperado |
| **Citou a fonte certa** | 8 | a resposta cita `[n]` e o trecho `n` vem do documento esperado |
| Citação no formato | 8 | usou `[n]` e não `【n】` |
| Termos esperados | 8 | todos os grupos de termos aparecem (sem acento e sem diferenciar caixa) |
| Recusou indevidamente | 8 | respondeu "não sei" a uma pergunta coberta (quanto menor, melhor) |
| Recusou corretamente | 2 que o corpus não cobre | respondeu "não sei" |

Uma pergunta é **aprovada** se: recuperou o documento certo, citou a fonte certa, não citou trecho
inexistente, tem os termos esperados e não recusou (ou, nas 2 sem resposta, se recusou). O formato
`【n】` não reprova a pergunta; é contado à parte.

## Resultado (2 execuções, mesmos prompts `9443c9e176`, `openai/gpt-oss-120b`, k=4, score mínimo 0,35)

| | Execução 1 | Execução 2 |
|---|---|---|
| Perguntas aprovadas | **9 de 10** | **9 de 10** |
| Recuperou o documento certo | 7 de 8 | 7 de 8 |
| Documento certo em primeiro | 6 de 8 | 6 de 8 |
| **Citou a fonte certa** | **7 de 8** | **7 de 8** |
| Citação no formato `[n]` | 5 de 8 | 3 de 8 |
| Termos esperados | 7 de 8 | 7 de 8 |
| Recusou indevidamente | 1 de 8 | 1 de 8 |
| Recusou corretamente (sem resposta no corpus) | 2 de 2 | 2 de 2 |

Resposta direta: **7 das 8 respostas citaram o contexto certo** nas duas execuções. A recuperação
é determinística; só o texto do LLM varia entre as execuções, e o que variou foi o formato da citação.

## Falhas

1. **q02 "Qual a diferença entre WHERE e HAVING?": falha de recuperação (nas duas execuções).**
   O trecho certo (`SQL básico > GROUP BY e HAVING`) ficou na **6ª posição, com similaridade 0,148**.
   Nada passou do score mínimo (0,35), então o sistema respondeu "Não encontrei isso nos documentos"
   sem chamar o LLM. O corpus tem a resposta e o sistema não a achou. O que sei: o modelo de embedding
   (`paraphrase-multilingual-MiniLM-L12-v2`) deu pouca similaridade entre a pergunta e o trecho. O que
   não testei: a causa (palavras-chave SQL em maiúsculas, trecho curto, ou o modelo ser treinado para
   paráfrase e não para busca). Uma busca híbrida com palavras-chave (BM25) ou outro modelo seriam as
   hipóteses a testar; não foram implementadas.
2. **q04 "chave de idempotência": acertou por pouco.** O trecho certo ficou em **4º lugar (0,382)**,
   acima do corte de 0,35 por 0,032, e o primeiro foi de outro documento (Python, 0,438). Com `k=3` ou
   score mínimo 0,40, essa pergunta também falharia.
3. **Formato da citação.** O modelo usa `【1】` em vez de `[1]` de forma recorrente (q04 e q07 nas duas
   execuções; q06 e q08 só na 2ª). A citação continua correta no conteúdo, mas quebraria um parser que
   procure `[n]`. O prompt pede `[n]`, e o modelo não obedece sempre.
4. **Documento certo em primeiro: 6 de 8.** Além da q02, a q04 teve outro documento na frente.

## Limites desta avaliação

- **Amostra mínima:** 8 perguntas respondíveis e 2 recusáveis; 1 falha equivale a 12,5 pontos
  percentuais. Não dá para tirar conclusão estatística.
- **Viés a favor do sistema:** o corpus e as perguntas foram escritos pela mesma pessoa, com o corpus
  aberto, em texto curto e de assunto bem separado. Um corpus real, repetitivo e com temas misturados
  tende a recuperar pior.
- **Corretude só por palavras-chave.** "Termos esperados" detecta a presença de palavras, não se a
  resposta está certa. Não mede o que o LLM acrescenta além do contexto, falha já vista na E2 (detalhes
  sobre `@WebMvcTest` que não estavam no trecho).
- **"Citou a fonte certa" não prova suporte:** confirma que o trecho citado é do documento esperado,
  não que a frase esteja de fato naquele trecho.
- **As 2 perguntas sem resposta não testam o LLM.** Ambas (q09 e q10) foram barradas pelo score mínimo,
  antes de chamar o modelo. A recusa feita pelo próprio LLM (quando o contexto é parecido, mas não
  responde) não é exercitada por este conjunto.
- **Duas execuções, um modelo, temperatura 0,2.** Mostram que o formato varia; não bastam para
  estimar a variação do resto.

## Como rodar

```bash
cd servidor
../.venv/Scripts/python -m rag indexar
../.venv/Scripts/python -m rag avaliar --saida ../avaliacao/resultados/minha-execucao.json
```

Usa a Groq de verdade (precisa de `GROQ_API_KEY` em `servidor/.env`) e faz até 8 chamadas por execução.
Os testes do script (`pytest tests/test_avaliacao.py`) usam LLM e embeddings falsos.
