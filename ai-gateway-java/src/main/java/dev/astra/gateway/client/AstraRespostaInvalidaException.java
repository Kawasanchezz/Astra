package dev.astra.gateway.client;

/** O Astra respondeu 200, mas o corpo não tem o formato esperado. */
public class AstraRespostaInvalidaException extends RuntimeException {

    public AstraRespostaInvalidaException(Throwable causa) {
        super("Resposta do Astra fora do formato esperado", causa);
    }
}
