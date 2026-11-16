package dev.astra.gateway.client;

public class AstraRejeitouException extends RuntimeException {

    private final int statusAstra;

    public AstraRejeitouException(int statusAstra) {
        super("O Astra recusou a requisição com status " + statusAstra);
        this.statusAstra = statusAstra;
    }

    public int getStatusAstra() {
        return statusAstra;
    }
}
