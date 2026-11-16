package dev.astra.gateway.web.dto;

import java.util.List;

import dev.astra.gateway.client.AstraResposta;

import io.swagger.v3.oas.annotations.media.Schema;

public record PerguntaResponse(
        @Schema(description = "Identificador da requisição, o mesmo do cabeçalho X-Request-ID e dos logs")
        String idRequisicao,
        String resposta,
        @Schema(description = "false quando nenhum trecho passou do score mínimo e o LLM nem foi chamado")
        boolean usouLlm,
        List<Fonte> fontes,
        String versaoPrompt) {

    public record Fonte(String arquivo, String secao, double score) {
    }

    public static PerguntaResponse de(String idRequisicao, AstraResposta astra) {
        List<Fonte> fontes = astra.fontes() == null ? List.of()
                : astra.fontes().stream().map(f -> new Fonte(f.arquivo(), f.secao(), f.score())).toList();
        return new PerguntaResponse(idRequisicao, astra.resposta(), astra.usouLlm(), fontes, astra.versaoPrompt());
    }
}
