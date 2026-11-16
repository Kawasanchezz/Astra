# Git básico

## Fluxo diário

`git status` mostra o que mudou. `git add arquivo` coloca a mudança na área de preparação. `git commit -m "mensagem"` registra um commit. `git push` envia os commits ao repositório remoto e `git pull` traz os novos.

## Branches

Uma branch é uma linha de desenvolvimento independente. Crie com `git switch -c minha-feature` e volte à principal com `git switch main`. Trabalhar em branch evita quebrar a `main` enquanto a funcionalidade não está pronta.

## Mensagens de commit

Escreva no imperativo e descreva uma mudança por commit, por exemplo "Valida tamanho da mensagem". Commits pequenos são mais fáceis de revisar e de reverter.

## Desfazendo coisas

`git restore arquivo` descarta mudanças ainda não preparadas. `git revert <commit>` cria um novo commit que desfaz outro, sem reescrever a história. Evite `git push --force` em branches compartilhadas.

## .gitignore

Liste arquivos que não devem ser versionados, como `.env` com segredos, ambientes virtuais e arquivos gerados. Um segredo que já entrou no histórico continua exposto mesmo depois de apagado: é preciso revogá-lo.
