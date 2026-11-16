package dev.astra.gateway.client;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record AstraResposta(
        String resposta,
        @JsonProperty("usou_llm") boolean usouLlm,
        List<Fonte> fontes,
        @JsonProperty("versao_prompt") String versaoPrompt) {

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Fonte(String arquivo, String secao, double score) {
    }
}
