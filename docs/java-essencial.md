# Java essencial

## Orientação a objetos

Encapsulamento esconde o estado interno atrás de métodos. Herança reaproveita comportamento de uma classe pai. Polimorfismo permite tratar objetos de classes diferentes pela mesma interface. Prefira composição à herança quando a relação não for realmente "é um".

## Coleções

`List` mantém ordem e aceita repetidos (`ArrayList` é o mais usado). `Set` não aceita repetidos (`HashSet`). `Map` associa chave a valor (`HashMap`). Para dinheiro, use `BigDecimal`, nunca `double`, porque ponto flutuante binário não representa decimais com exatidão.

## Optional

`Optional<T>` representa um valor que pode estar ausente e evita `NullPointerException`. Use `orElse`, `orElseThrow` e `map` em vez de comparar com `null`. Não use `Optional` como campo de entidade nem como parâmetro.

## Tratamento de exceções

Exceções verificadas (`checked`) precisam ser declaradas ou tratadas; as não verificadas (`RuntimeException`) não. Use `try-with-resources` para fechar recursos como conexões e streams automaticamente.

## Spring Boot

O Spring Boot configura uma aplicação web com mínimo de código. Controladores anotados com `@RestController` expõem endpoints, a injeção de dependência monta os objetos e `application.yml` guarda a configuração. Testes de camada web usam `@WebMvcTest`.
