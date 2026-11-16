package dev.astra.gateway.client;

/** O Astra não respondeu direito (5xx, rede ou prazo). É o único erro que o retry repete e o circuit breaker conta. */
public class AstraFalhaTransitoriaException extends RuntimeException {

    private final boolean timeout;

    public AstraFalhaTransitoriaException(String mensagem, boolean timeout, Throwable causa) {
        super(mensagem, causa);
        this.timeout = timeout;
    }

    public boolean isTimeout() {
        return timeout;
    }
}
