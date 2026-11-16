# SQL básico

## SELECT e filtros

`SELECT` lê linhas de uma tabela. Use `WHERE` para filtrar linhas antes do agrupamento e `ORDER BY` para ordenar o resultado. `LIMIT` (ou `FETCH FIRST` em alguns bancos) restringe a quantidade de linhas devolvidas.

```sql
SELECT nome, saldo FROM contas WHERE saldo > 1000 ORDER BY saldo DESC LIMIT 10;
```

## JOIN

`INNER JOIN` devolve só as linhas que têm correspondência nas duas tabelas. `LEFT JOIN` devolve todas as linhas da tabela da esquerda e preenche com `NULL` quando não há correspondência na direita. Prefira sempre a condição `ON` explícita para evitar produto cartesiano.

## GROUP BY e HAVING

`GROUP BY` agrupa linhas para usar funções de agregação como `COUNT`, `SUM` e `AVG`. `WHERE` filtra antes de agrupar; `HAVING` filtra depois, sobre o resultado das agregações.

## Índices

Um índice acelera buscas e junções em colunas muito consultadas, mas deixa `INSERT`, `UPDATE` e `DELETE` mais lentos e ocupa espaço. Crie índices nas colunas usadas em `WHERE` e `JOIN`, e confira o plano de execução com `EXPLAIN` antes de assumir que ajudou.

## Chave primária e chave estrangeira

A chave primária identifica uma linha de forma única e não aceita `NULL`. A chave estrangeira garante que o valor aponte para uma linha existente em outra tabela, mantendo a integridade referencial.
