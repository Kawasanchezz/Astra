package dev.astra.gateway.client;

/** O Astra respondeu 4xx. Repetir a mesma chamada daria o mesmo erro, então não há retry. */
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
