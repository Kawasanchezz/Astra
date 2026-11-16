package dev.astra.gateway.client;

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
