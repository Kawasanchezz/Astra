# Política de Segurança

A segurança deste projeto e dos dados de quem o utiliza é prioridade. Este documento reúne **(1)** como reportar vulnerabilidades e **(2)** o checklist de segurança que o projeto segue. Agradecemos a quem reporta de forma responsável.

## Sumário

- [Versões suportadas](#versões-suportadas)
- [Como reportar uma vulnerabilidade](#como-reportar-uma-vulnerabilidade)
- [O que incluir no relato](#o-que-incluir-no-relato)
- [Prazos de resposta](#prazos-de-resposta)
- [Classificação de severidade](#classificação-de-severidade)
- [Divulgação coordenada](#divulgação-coordenada)
- [Escopo](#escopo)
- [Fora do escopo](#fora-do-escopo)
- [Pesquisa de boa-fé (safe harbor)](#pesquisa-de-boa-fé-safe-harbor)
- [Segredos e credenciais expostos](#segredos-e-credenciais-expostos)
- [Checklist de segurança do projeto](#checklist-de-segurança-do-projeto)
- [Cabeçalhos de segurança](#cabeçalhos-de-segurança)
- [Antes de cada deploy](#antes-de-cada-deploy)
- [Como testar como um estranho](#como-testar-como-um-estranho)
- [Auditoria de segurança (etapas E1–E9)](#auditoria-de-segurança-etapas-e1e9)
- [Se o projeto ganhar backend, login ou formulário](#se-o-projeto-ganhar-backend-login-ou-formulário)
- [Reconhecimento](#reconhecimento)

---

## Versões suportadas

| Versão                         | Suporte de segurança |
| ------------------------------ | -------------------- |
| Branch `main` (versão atual)   | ✅ Sim               |
| Branches antigas, forks e tags | ❌ Não               |

Apenas a versão mais recente, na branch `main`, recebe correções de segurança. Se encontrou um problema em versão antiga, confirme se ele ainda ocorre na `main` antes de reportar.

## Como reportar uma vulnerabilidade

> ⚠️ **Não abra uma issue pública, pull request ou discussão** para relatar uma vulnerabilidade. Isso expõe o problema antes de ele ser corrigido.

**Canal principal: relato privado do GitHub**

1. Abra a aba **Security** deste repositório.
2. Clique em **Report a vulnerability**.
3. Preencha o formulário com os detalhes da próxima seção.

Somente você e os mantenedores têm acesso ao relato. Também é possível abrir diretamente em `https://github.com/<usuario>/<repositorio>/security/advisories/new`.

## O que incluir no relato

- **Resumo** objetivo da vulnerabilidade.
- **Componente afetado**: página, rota, endpoint, arquivo ou função.
- **Passos para reproduzir**, de preferência com prova de conceito (PoC) mínima.
- **Impacto**: o que um atacante consegue fazer.
- **Pré-requisitos**: autenticação, papel específico ou interação da vítima.
- **Ambiente**: navegador, sistema operacional, commit/versão testada.
- **Sugestão de correção** (opcional).

Não inclua dados pessoais reais de terceiros. Use contas e dados de teste.

## Prazos de resposta

| Etapa                                 | Prazo alvo                                          |
| ------------------------------------- | --------------------------------------------------- |
| Confirmação de recebimento            | até **7 dias corridos**                             |
| Triagem e classificação inicial       | até **14 dias corridos**                            |
| Atualizações de andamento             | pelo menos a cada **14 dias** até a resolução       |
| Correção de vulnerabilidades críticas | o mais rápido possível, priorizada sobre o restante |

São metas de boa-fé de um projeto mantido com recursos limitados, não garantias contratuais. Se o prazo de confirmação passar sem retorno, reenvie o relato.

## Classificação de severidade

Usamos o [CVSS v3.1](https://www.first.org/cvss/) como referência, considerando impacto e facilidade de exploração.

| Severidade  | Exemplos                                                                                                                      |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Crítica** | Execução remota de código, vazamento de segredos ou de dados de outros usuários em larga escala, bypass total de autenticação |
| **Alta**    | Escalonamento de privilégios, acesso indevido a dados de outros usuários, injeção (SQL/NoSQL/comando), SSRF com impacto real  |
| **Média**   | XSS armazenado ou refletido, CSRF em ações sensíveis, exposição limitada de informações, falhas de autorização pontuais       |
| **Baixa**   | Vazamento de informação de baixo risco, má configuração de difícil exploração, sem impacto demonstrável                       |

A severidade final é definida pelos mantenedores; explicaremos o raciocínio se divergir do relato.

## Divulgação coordenada

1. O relato é recebido e validado em privado.
2. A correção é desenvolvida e publicada na `main`.
3. Depois da correção, publicamos um **security advisory** com problema, impacto e versão corrigida, com crédito a quem reportou (se desejado).

Pedimos que **não divulgue detalhes publicamente** até a correção estar disponível. Como referência, adotamos até **90 dias** a partir da confirmação. Se precisarmos de mais tempo, combinaremos um novo prazo com você de forma transparente. Se não houver resposta nossa dentro dos prazos acima, você pode seguir com a divulgação pública responsável.

## Escopo

Estão no escopo falhas no código e na configuração **deste repositório** e do site/aplicação publicado a partir dele, por exemplo:

- Falhas de autenticação, sessão ou controle de acesso.
- Injeções (SQL, NoSQL, comando, template) e XSS (incluindo via parâmetros de URL).
- CSRF, SSRF e redirecionamentos abertos exploráveis.
- Exposição de dados sensíveis, segredos ou informações pessoais.
- Falhas de lógica de negócio com impacto em segurança.
- Dependências vulneráveis **comprovadamente exploráveis** no projeto.
- Contorno de limites de requisição com impacto real.
- Prompt injection (se o projeto usar IA) que resulte em falha técnica concreta: vazamento de dados, acesso a segredos ou ações não autorizadas.
- Política CSP/cabeçalhos que permitam exploração demonstrável.

## Fora do escopo

- Ataques de negação de serviço por volume.
- Falhas que exijam acesso físico ao dispositivo da pessoa usuária.
- Problemas em serviços de terceiros (hospedagem, CDN, provedores de IA, GitHub etc.); reporte diretamente a eles.
- Respostas incorretas ou inadequadas de IA sem falha técnica (descreva em uma issue normal).
- Engenharia social, phishing ou ataques contra mantenedores e usuários.
- Relatos de scanners automatizados sem validação ou prova de exploração.
- Ausência de cabeçalhos ou flags de boas práticas sem impacto demonstrável.
- Vulnerabilidades em versões antigas ou já corrigidas na `main`.
- Testes que degradem o serviço ou afetem outros usuários.

## Pesquisa de boa-fé (safe harbor)

Não tomaremos medidas legais contra quem pesquisar e reportar de boa-fé, desde que você:

- Siga esta política e use o canal de relato privado.
- Não viole a privacidade de terceiros nem destrua ou altere dados que não sejam seus.
- Interrompa o teste e reporte ao encontrar dados de outras pessoas.
- Use apenas contas e dados de teste criados por você.
- Não realize negação de serviço, spam ou engenharia social.
- Não exija pagamento ou vantagem em troca do relato ou do silêncio.
- Dê tempo razoável para a correção antes de divulgar.

Esta seção expressa a intenção do projeto, não substitui a legislação aplicável e não vincula terceiros.

## Segredos e credenciais expostos

Se encontrar chave de API, senha, token ou outra credencial exposta (código, histórico do Git, logs ou respostas da aplicação):

- Avise imediatamente pelo canal privado.
- **Não use, teste, valide nem divulgue** o segredo.
- Não copie além do necessário; mascare no relato (ex.: `sk-****abcd`).

O segredo será **revogado e rotacionado** e o histórico avaliado para limpeza, quando aplicável.

---

## Checklist de segurança do projeto

Marque o status de cada item ao copiar este arquivo para um projeto: ✅ feito · ➖ não se aplica (explique o motivo) · ❌ pendente.

| #  | Item | O que garantir | Status |
| -- | ---- | -------------- | ------ |
| 1  | Chave de API protegida | Nenhuma chave privada no front-end. Chaves ficam no servidor/variáveis de ambiente. Em Vite/Next, nunca usar `VITE_*`/`NEXT_PUBLIC_*` para segredos (ficam visíveis no navegador) | ☐ |
| 2  | `.env` nunca exposto | `.env`, `.env.*`, `*.pem`, `*.key`, `.npmrc`, dumps e credenciais no `.gitignore` | ☐ |
| 3  | Nada de senha no código | Nenhuma senha, token ou segredo no código nem no histórico do Git | ☐ |
| 4  | Login de verdade | Autenticação robusta: hash de senha (Argon2/bcrypt/Identity), JWT/sessão seguros, expiração e refresh | ☐ |
| 5  | Permissão no servidor | Autorização sempre validada no servidor, nunca só escondendo botões na tela | ☐ |
| 6  | Não confia no ID da tela | Parâmetros de URL/ID validados contra lista permitida (ex.: `Object.hasOwn`), sem acesso a `__proto__` | ☐ |
| 7  | Cada um só vê o seu | Isolamento por usuário (checar dono do recurso em toda consulta) | ☐ |
| 8  | Banco travado | Sem acesso público ao banco, usuário com privilégio mínimo, backups e conexão criptografada | ☐ |
| 9  | Firebase/Supabase/storage | Regras de acesso restritivas (RLS/Security Rules), buckets privados, service accounts fora do Git | ☐ |
| 10 | Admin protegido | Painel admin com papel dedicado, autenticação forte (2FA quando possível) e rota não pública | ☐ |
| 11 | Debug desligado | Sem `console.log`/modo debug em produção, sem `debugger`, sem source maps públicos | ☐ |
| 12 | Erro sem detalhe | Nenhum stack trace ou erro técnico exibido ao visitante; páginas de erro genéricas | ☐ |
| 13 | Valida tudo no servidor | Validação de entrada no servidor (a do cliente é só UX e deve ser repetida no servidor) | ☐ |
| 14 | Limpa o que o usuário manda | `textContent` em vez de `innerHTML`; escape em templates; remoção de caracteres de controle; `form-action` restrito | ☐ |
| 15 | Upload protegido | Validar tipo real, tamanho e extensão; renomear arquivos; armazenar fora do webroot; varrer malware | ☐ |
| 16 | Sem injeção de SQL | Consultas parametrizadas/ORM (ex.: EF Core), nunca SQL montado por concatenação | ☐ |
| 17 | Limite de tentativas | Rate limiting no servidor/CDN (login, formulários, APIs); no cliente apenas como UX; honeypot anti-bot | ☐ |
| 18 | Git sem senha vazada | `.gitignore` reforçado, varredura de segredos (secret scanning), `npm audit` sem vulnerabilidades | ☐ |
| 19 | Headers e CORS certos | Cabeçalhos da seção abaixo; CORS restrito a origens conhecidas (nunca `*` com credenciais) | ☐ |
| 20 | Testa como um estranho | Testes da seção "Como testar" executados em aba anônima, sem login | ☐ |
| 21 | Auditoria completa | `npm audit`/`dotnet list package --vulnerable` + revisão de código; repetir a cada mudança relevante | ☐ |

**Dependências externas (CDN):** use versão fixa e **SRI** (`integrity` + `crossorigin="anonymous"`), e libere na CSP apenas os domínios necessários.

## Cabeçalhos de segurança

Configure no servidor/hospedagem. Ajuste a CSP aos domínios que o projeto realmente usa.

| Cabeçalho | Valor recomendado | Função |
| --------- | ----------------- | ------ |
| `Content-Security-Policy` | veja exemplo abaixo | Bloqueia scripts e recursos não autorizados (mitiga XSS) |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Força HTTPS |
| `X-Content-Type-Options` | `nosniff` | Impede adivinhação de tipo MIME |
| `X-Frame-Options` | `DENY` | Impede clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limita vazamento de URL |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=()` | Desliga recursos do navegador não usados |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isola a janela de outras origens |
| `Cross-Origin-Resource-Policy` | `same-origin` | Impede que outros sites carreguem seus recursos |

**Exemplo de CSP estrita** (sem `unsafe-inline` em scripts):

```
default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests
```

Se usar Google Fonts, acrescente `https://fonts.googleapis.com` em `style-src` e `https://fonts.gstatic.com` em `font-src`. Se usar CDN para scripts, acrescente o domínio em `script-src` (com SRI). Sites sem formulário podem usar `form-action 'none'`.

**Vercel (`vercel.json`):**

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests" },
        { "key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=(), payment=(), usb=()" },
        { "key": "Cross-Origin-Opener-Policy", "value": "same-origin" },
        { "key": "Cross-Origin-Resource-Policy", "value": "same-origin" }
      ]
    }
  ]
}
```

**Netlify / Cloudflare Pages (`public/_headers`):**

```
/*
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Resource-Policy: same-origin
```

**ASP.NET Core:** aplique os mesmos cabeçalhos em um middleware e use `app.UseHsts()`, `app.UseHttpsRedirection()` e `AddRateLimiter` para o item 17.

**Hospedagem sem suporte a cabeçalhos (ex.: GitHub Pages):** inclua a CSP no `index.html` como `<meta http-equiv="Content-Security-Policy" content="...">`. Nesse caso `frame-ancestors` e os demais cabeçalhos **não funcionam**.

## Antes de cada deploy

1. `npm audit` com 0 vulnerabilidades (se não, `npm audit fix`). Em .NET: `dotnet list package --vulnerable`.
2. `npm run lint` e `npm run build` sem erros.
3. Publicar apenas com HTTPS.
4. Abrir o site publicado em aba anônima: tudo carrega e o console não mostra violações de CSP.
5. Conferir os cabeçalhos em [securityheaders.com](https://securityheaders.com) e [observatory.mozilla.org](https://observatory.mozilla.org).
6. Conferir que não há segredos no repositório (secret scanning do GitHub ativo).
7. Ativar verificação em duas etapas (2FA) nas contas de GitHub e da hospedagem.
8. Ativar Dependabot para alertas e atualizações de dependências.

## Como testar como um estranho

- Abra o site em aba anônima e confira o console: nenhuma violação de CSP.
- Tente `?id=<script>alert(1)</script>` e `?id=__proto__` em páginas que leem parâmetros: devem cair em "não encontrado", sem executar nada.
- Envie formulários com HTML, emoji e texto gigante: deve ser rejeitado ou exibido como texto puro.
- Tente acessar rotas protegidas e dados de outro usuário sem login ou com outra conta: deve ser negado pelo servidor.
- Verifique se erros não exibem stack trace nem caminhos internos.
- Tente acessar `/.env`, `/.git/config` e arquivos de backup na URL publicada: deve retornar 404.

## Auditoria de segurança (etapas E1–E9)

Revisão feita sobre o próprio código, com correções e testes automatizados (o LLM é sempre simulado nos testes; nenhum teste chama a API real). **Isto não é uma garantia de que o sistema seja seguro**: é o registro do que foi corrigido, do que foi medido e do que continua em aberto.

### O que foi corrigido

| Área | Problema | Correção |
| --- | --- | --- |
| Entrada | Regex com custo quadratico (`_URL_COM_SENHA`) permitia DoS; JSON muito aninhado dava 500; mensagem só com caracteres invisíveis passava; 413 incorreto com texto multibyte; surrogates quebravam a chamada | Regex limitada, `RecursionError` vira 400, sanitização antes da checagem de vazio, limite de corpo calculado em bytes, remoção de surrogates |
| Abuso | Sem teto de gasto, sem limite na API do RAG nem no gateway Java | Orçamento diário de tokens, limites por IP/dia/global, semáforo de concorrência, `RateLimitFilter` (30/min por IP) no gateway |
| Erros da LLM | Falhas viravam 200 com texto de erro; timeout×retries podia passar do limite da Vercel | HTTP próprio por falha (400/429/502/503/504, `Retry-After`), prazo total derivado, resposta vazia vira 502 |
| Injeção de prompt | Guarda com lacunas; trechos recuperados do RAG podiam forjar o delimitador | Guarda ampliada (66 testes originais mantidos), delimitador aleatório por requisição, prompt versionado |
| Saída | DOMPurify permissivo (forms, img, svg, style); imagem markdown servia para exfiltrar dados | Configuração restrita, remoção de imagens fora de blocos de código, 22 testes de XSS no navegador |
| Web | Cookie e `SECRET_KEY` sem validação, CORS sem validar origens, CSP incompleta, cabeçalho `Server` com versão, gateway Java sem cabeçalhos | `SECRET_KEY` forte exigida em produção, origens exatas, cookie `HttpOnly`/`SameSite`/`Secure`/`__Host-`, CSP e Permissions-Policy completas, `SecurityHeadersFilter` no Java |
| Logs | Sem id de correlação no Flask; id do cliente aceitava `\n` (injeção de linha no log); segredo podia ir parar no log | `X-Request-ID` em toda resposta, `fullmatch` no id, filtro que mascara chave, token e e-mail; erros sem traceback nem caminho |
| Dependências | Instalação sem versão nem hash na imagem; base Docker por tag; `pytest` na imagem; Dependabot só em pip; bandit B613 (caracteres bidi literais) | `requirements-rag.lock` com hashes e `--require-hashes`, bases por digest, `requirements-dev.txt`, Dependabot em pip/maven/docker/actions, escapes no lugar de literais invisíveis |
| Segredos | Risco de commitar `servidor/.env` | `.gitignore`, `.dockerignore`, `.gitleaks.toml`, `.env.example` sem valores; histórico sem vazamentos |

### Como repetir a validação

```bash
pip install -r requirements-dev.txt && playwright install chromium
ruff check .                                   # lint
mypy servidor                                  # tipos
pytest -q                                      # ~433 testes (inclui abuso, injeção, XSS no navegador; com CI=true, falha sem navegador)
bandit -r servidor app.py -ll                  # análise estática (0 High/Medium)
pip-audit -r requirements.txt                  # CVEs
pip-audit -r requirements-rag.lock --no-deps --disable-pip
gitleaks git --config .gitleaks.toml           # histórico (gitleaks dir . também acusa o servidor/.env local, que não é versionado)
cd ai-gateway-java && mvn test                 # 34 testes do gateway (ou via Docker, maven:3.9-eclipse-temurin-21)
```

Testes de abuso, por arquivo: `tests/test_abuso.py` (entradas extremas, requisições em massa, orçamento), `tests/test_injection.py` e `tests/test_seguranca.py` (injeção de prompt e vazamento do prompt de sistema), `tests/test_saida_front.py` (XSS no navegador), `tests/test_web.py` (cabeçalhos, cookies, CORS, erros), `tests/test_logs.py`, `tests/test_supply.py`.

### Riscos que permanecem

- **Injeção de prompt não é eliminável.** A guarda é heurística: 5 variantes conhecidas passam e estão marcadas como `xfail(strict=True)` (avó/roleplay, ROT13, chinês, "modo desenvolvedor", entre outras). Um atacante criativo pode contorná-la. O que limita o dano é a arquitetura (o modelo não tem ferramentas nem acesso a dados privados), não a guarda.
- **Alucinação.** O modelo pode responder errado com confiança. No RAG, a última avaliação (`docs/avaliacao.md`) acertou a fonte em 7 de 8 casos esperados; trate respostas como apoio, não como fonte final.
- **Detecção de vazamento do prompt** compara 8 palavras seguidas; paráfrase ou tradução passam. O prompt de sistema não contém segredos.
- **Contadores em memória** (`memory://`): por processo, zerados a cada deploy e não compartilhados entre instâncias. Poucos IPs podem esgotar o limite global.
- **O histórico da conversa vem do cliente** e pode ser forjado (o limite de tamanho e a guarda se aplicam a ele, mas o conteúdo não é confiável).
- **Sem sessão nem login**: por isso não há CSRF a mitigar. Se isso mudar, será preciso token CSRF e revisão de autorização.
- **Cabeçalho `Server`** não pode ser removido sob gunicorn/Vercel. O log de acesso do servidor WSGI fica fora do filtro de segredos.
- **Dependências:** o `requirements.txt` da Vercel usa faixas (piso e teto), não versões exatas; o lock com hashes vale só para a imagem do RAG e é regenerado à mão. O CI roda pip-audit, bandit, lint, tipos, testes (Python e Java) e Trivy nas duas imagens.
- **Spring Framework 6.2.19 no gateway (CRÍTICO, aberto):** `CVE-2026-47884` e `CVE-2026-47890` só têm correção na linha 7.0.9, que exige Spring Boot 4. O código não usa XSLT, SSE nem `View`, mas o componente continua na imagem e o job `imagens` do CI fica vermelho até a migração ou uma aceitação de risco documentada.
- **bandit:** 6 achados Low em `servidor/servidor_seguro.py`, lançador só de Windows (risco aceito).
- **Chave exposta:** a chave Groq de `servidor/.env` apareceu sem máscara numa transcrição local; deve ser revogada e rotacionada no painel da Groq (não é algo que o código resolve).
- Nada disso foi testado contra um ambiente de produção real (Vercel, proxy TLS); a verificação ao vivo foi local.

## Se o projeto ganhar backend, login ou formulário

Os itens 4 a 17 passam a ser obrigatórios. Em especial:

- Nunca colocar chaves privadas em variáveis expostas ao navegador.
- Validar e limpar tudo no servidor, nunca só no navegador.
- Usar consultas parametrizadas, nunca SQL montado por texto.
- Limitar tentativas de login e envio (rate limiting no servidor).
- Proteger rotas de admin e dados de cada usuário no servidor.
- Armazenar senhas apenas com hash forte (Argon2/bcrypt/ASP.NET Identity).
- Proteger formulários e cookies de sessão contra CSRF (`SameSite`, `HttpOnly`, `Secure`, tokens anti-forgery).
- Registrar logs de segurança sem gravar dados sensíveis.

## Reconhecimento

Reconhecemos publicamente, no security advisory, quem reportar uma vulnerabilidade válida, salvo se preferir permanecer anônimo. Informe sua preferência no relato.

Este projeto **não mantém programa de recompensa financeira (bug bounty)**; o reconhecimento é por crédito público e agradecimento.

### Veredito da auditoria (E9)

**Não aprovada.** Um critério da auditoria não está cumprido: "nenhuma vulnerabilidade crítica conhecida permanece sem tratamento" (Spring Framework 6.2.19, ver acima). Os demais critérios têm evidência na tabela abaixo. Isso não significa que o sistema seja invulnerável.

| Critério | Situação | Evidência |
| --- | --- | --- |
| Testes obrigatórios passam | Cumprido | `pytest -q`: 433 passed, 1 skipped, 5 xfailed. Os 5 xfailed são variantes de injeção conhecidas, não testes desabilitados |
| Nenhum teste desabilitado | Cumprido | Nenhum `skip` novo para esconder falha. O fixture de navegador passou a falhar no CI em vez de pular |
| Nenhuma chave ativa exposta no código ou histórico | Cumprido no código; **pendente no painel** | `gitleaks git`: no leaks found. A chave antiga precisa ser revogada pelo mantenedor |
| Nenhuma vulnerabilidade crítica ou alta sem tratamento | **Não cumprido** | Spring Framework 6.2.19 (crítica, aberta). Tomcat, Jackson, zlib e pip da imagem foram tratados |
| Nenhum problema conhecido de isolamento entre usuários | Cumprido com ressalva | Conversas do front isoladas por chat (E2). Contadores são por processo (ver riscos) |
| Nenhum problema crítico de consumo sem mitigação | Parcial | Teto diário e limites por IP existem e são barrados em produção sem teto (E4). Contadores não são globais entre instâncias |
| Nenhuma falha de XSS conhecida | Cumprido | 22 testes de XSS no navegador passam (`test_saida_front.py`) |
| Nenhuma configuração insegura de produção sem justificativa | Cumprido | Trava de `SECRET_KEY`, origem, orçamento e `RAG_API_TOKEN` em produção |
| Nenhum scanner escondido | Cumprido | Trivy e bandit rodam no CI sem `ignore` para os achados; o `.trivyignore` não existe |
| Riscos residuais documentados | Cumprido | Esta seção |

#### Evidências desta rodada (E9)

- `ruff check .`: All checks passed.
- `mypy servidor`: Success, 25 arquivos.
- `bandit -r servidor app.py -ll`: 0 High, 0 Medium (6 Low em `servidor/servidor_seguro.py`, lançador de Windows).
- `pip-audit -r requirements.txt` e `pip-audit -r requirements-rag.lock --no-deps --disable-pip`: No known vulnerabilities found.
- `gitleaks git`: no leaks found.
- Trivy, imagem RAG: sem achados CRITICAL/HIGH com correção disponível.
- Trivy, imagem do gateway: 2 CRITICAL (`spring-webmvc` 6.2.19).
- Java: `mvn test`, 35 testes, BUILD SUCCESS.
- Linux com `CI=true` e Chromium: 433 passed, 1 skipped, 5 xfailed.
- Ao vivo (servidor local, sem chamadas à Groq): corpo de 5 MB → 413; JSON com 5000 níveis → 400; tipos errados → 400; rajada além do limite → 429 a partir da 6ª requisição; cabeçalhos presentes; 404 e 405 em JSON; nenhum `gsk_` nem `Traceback` no log.

#### Desvio desta rodada

Durante a verificação ao vivo, uma requisição com caracteres invisíveis foi enviada à Groq com a chave local de teste (fictícia). A API respondeu 401 (`AuthenticationError`), registrado como `credencial_recusada`. Não houve cobrança nem vazamento. A causa foi a forma como o shell do Windows transmitiu os bytes do corpo da requisição, o que impediu que o caso fosse testado como pretendido. O mesmo caso foi reproduzido sem rede com o test client, e retornou 400.

#### Como o teste ao vivo deve ser feito

Para não repetir o desvio acima: use `ia.client = None` (modo demo) ou a suíte com a API simulada, e não um servidor com chave real ou fictícia. Mande corpos com `printf` para arquivo, e não pela linha de comando do Windows.
