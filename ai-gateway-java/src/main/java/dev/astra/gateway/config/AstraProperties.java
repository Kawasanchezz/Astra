package dev.astra.gateway.config;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "astra")
public record AstraProperties(String baseUrl, String token, Duration timeoutConexao, Duration timeoutLeitura) {

    @Override
    public String toString() {
        String tokenMascarado = token == null || token.isBlank() ? "" : "****";
        return "AstraProperties[baseUrl=" + baseUrl + ", token=" + tokenMascarado
                + ", timeoutConexao=" + timeoutConexao + ", timeoutLeitura=" + timeoutLeitura + "]";
    }
}
