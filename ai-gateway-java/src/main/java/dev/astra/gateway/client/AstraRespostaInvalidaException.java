package dev.astra.gateway.client;

public class AstraRespostaInvalidaException extends RuntimeException {

    public AstraRespostaInvalidaException(Throwable causa) {
        super("Resposta do Astra fora do formato esperado", causa);
    }
}
