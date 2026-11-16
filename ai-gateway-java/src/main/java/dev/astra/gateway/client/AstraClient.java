package dev.astra.gateway.client;

import java.net.SocketTimeoutException;
import java.net.http.HttpConnectTimeoutException;
import java.net.http.HttpTimeoutException;

import com.fasterxml.jackson.annotation.JsonInclude;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/**
 * Chama o POST /ask do Astra. A ordem das anotações importa: o Retry fica por fora e o CircuitBreaker por
 * dentro, então cada tentativa conta para o circuito e, com o circuito aberto, o retry nem insiste.
 */
@Component
public class AstraClient {

    private final RestClient rest;

    public AstraClient(@Qualifier("astraRestClient") RestClient rest) {
        this.rest = rest;
    }

    @Retry(name = "astra")
    @CircuitBreaker(name = "astra")
    public AstraResposta perguntar(String pergunta, Integer k, String idRequisicao) {
        try {
            AstraResposta resposta = rest.post()
                    .uri("/ask")
                    .header("X-Request-ID", idRequisicao)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(new Pedido(pergunta, k))
                    .retrieve()
                    .body(AstraResposta.class);
            if (resposta == null) {
                throw new AstraFalhaTransitoriaException("O Astra devolveu um corpo vazio", false, null);
            }
            return resposta;
        } catch (HttpClientErrorException e) {
            throw new AstraRejeitouException(e.getStatusCode().value());
        } catch (HttpServerErrorException e) {
            throw new AstraFalhaTransitoriaException("O Astra respondeu " + e.getStatusCode().value(), false, e);
        } catch (ResourceAccessException e) {
            throw new AstraFalhaTransitoriaException("O Astra está inacessível", houveTimeout(e), e);
        } catch (RestClientException e) {
            throw new AstraRespostaInvalidaException(e);
        }
    }

    /** Só estouro de leitura é 504. Não conseguir conectar é indisponibilidade (503), não demora. */
    private static boolean houveTimeout(Throwable erro) {
        for (Throwable t = erro; t != null; t = t.getCause()) {
            if (t instanceof HttpConnectTimeoutException) {
                return false;
            }
            if (t instanceof HttpTimeoutException || t instanceof SocketTimeoutException) {
                return true;
            }
        }
        return false;
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    record Pedido(String pergunta, Integer k) {
    }
}
