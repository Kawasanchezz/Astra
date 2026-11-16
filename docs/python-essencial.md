# Python essencial

## Estruturas de dados

Listas são mutáveis e ordenadas. Tuplas são imutáveis. Dicionários mapeiam chaves a valores e têm busca média em tempo constante. Conjuntos (`set`) guardam elementos únicos e testam pertinência rapidamente.

## Tratamento de exceções

Use `try/except` capturando exceções específicas, nunca um `except:` vazio. O bloco `finally` roda sempre, e `else` roda quando nenhuma exceção ocorreu. Levante erros com `raise` e crie exceções próprias herdando de `Exception` quando fizer sentido.

## Context managers

A instrução `with` garante a liberação de recursos, como fechar um arquivo mesmo se ocorrer erro. Qualquer objeto com `__enter__` e `__exit__` funciona, e `contextlib.contextmanager` permite escrever um com um gerador.

## Decorators

Um decorator é uma função que recebe uma função e devolve outra, acrescentando comportamento como log, cache ou verificação de permissão. A sintaxe `@decorador` acima da definição equivale a `f = decorador(f)`. Use `functools.wraps` para preservar o nome e a documentação da função original.

## Geradores

Uma função com `yield` devolve um gerador, que produz valores sob demanda sem guardar tudo na memória. Isso é útil para processar arquivos grandes linha a linha.

## Ambientes virtuais

Crie um ambiente isolado com `python -m venv .venv` e instale dependências com `pip install -r requirements.txt`. Assim cada projeto usa suas próprias versões de pacotes.
