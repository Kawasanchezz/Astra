# HTTP e APIs REST

## Verbos

`GET` lê um recurso e não deve alterar estado. `POST` cria um recurso ou executa uma ação. `PUT` substitui um recurso inteiro. `PATCH` altera parte dele. `DELETE` remove.

## Idempotência

Uma operação é idempotente quando repetir a chamada produz o mesmo resultado final. `GET`, `PUT` e `DELETE` são idempotentes; `POST` normalmente não é. Em pagamentos, use uma chave de idempotência enviada pelo cliente para que uma retentativa não cobre duas vezes.

## Códigos de status

- `200 OK`: sucesso. `201 Created`: recurso criado. `204 No Content`: sucesso sem corpo.
- `400 Bad Request`: requisição inválida. `401 Unauthorized`: sem autenticação válida. `403 Forbidden`: autenticado, mas sem permissão. `404 Not Found`: recurso inexistente. `429 Too Many Requests`: limite de uso excedido.
- `500 Internal Server Error`: falha no servidor. `502`, `503` e `504`: falha de um serviço de que este depende, indisponibilidade ou timeout.

## Boas práticas

Valide a entrada e limite o tamanho do corpo. Defina timeout em toda chamada a outro serviço. Devolva erros em formato consistente e sem detalhes internos. Versione a API (por exemplo `/v1/`) para evoluir sem quebrar clientes.
