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