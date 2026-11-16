# Segurança em aplicações web

## Injeção de SQL

Ocorre quando a entrada do usuário é concatenada em uma consulta. A defesa é usar consultas parametrizadas (prepared statements), em que o valor nunca é interpretado como código SQL.

## XSS

Cross-Site Scripting acontece quando dados do usuário são inseridos na página sem escape e executam como script. Escape a saída de acordo com o contexto, sanitize HTML quando precisar aceitá-lo e use uma Content Security Policy restritiva.

## CSRF

Cross-Site Request Forgery faz o navegador do usuário autenticado enviar uma requisição que ele não pretendia. Mitigue com tokens anti-CSRF, cookies `SameSite` e verificação do cabeçalho `Origin`.

## Senhas

Nunca guarde senhas em texto puro. Use um algoritmo de hash lento e com salt, como Argon2id, bcrypt ou scrypt, e não hashes rápidos como MD5 ou SHA-1 puros.

## Segredos e logs

Mantenha chaves de API em variáveis de ambiente, fora do código e do repositório. Não registre senhas, tokens nem dados pessoais completos em logs, e mascare o que for necessário registrar.

## Limitação de uso

Aplique rate limiting para conter abuso e força bruta, valide o tamanho e o formato de toda entrada e devolva mensagens de erro genéricas, sem expor detalhes internos.
