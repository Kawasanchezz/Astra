# Transações e ACID

## O que é uma transação

Uma transação agrupa várias operações que precisam acontecer juntas ou não acontecer. Em um sistema bancário, uma transferência debita uma conta e credita outra: se o crédito falhar, o débito deve ser desfeito.

## Propriedades ACID

- **Atomicidade**: a transação é tudo ou nada. Se uma etapa falha, o banco desfaz as anteriores (`ROLLBACK`).
- **Consistência**: a transação leva o banco de um estado válido a outro, respeitando restrições como chaves e `CHECK`.
- **Isolamento**: transações concorrentes não enxergam resultados parciais umas das outras, no grau definido pelo nível de isolamento.
- **Durabilidade**: depois do `COMMIT`, o resultado persiste mesmo se o sistema cair.

## Níveis de isolamento

Quanto mais forte o isolamento, menos anomalias e menos concorrência. `READ COMMITTED` evita leitura suja. `REPEATABLE READ` evita também leitura não repetível. `SERIALIZABLE` evita também leitura fantasma, com o maior custo de desempenho. O padrão varia entre bancos.

## Concorrência

Dois usuários alterando o mesmo saldo ao mesmo tempo podem causar perda de atualização. Soluções comuns são bloqueio pessimista (`SELECT ... FOR UPDATE`) e bloqueio otimista com uma coluna de versão que é conferida no `UPDATE`.
