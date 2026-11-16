package dev.astra.gateway.config;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "astra")
public record AstraProperties(String baseUrl, String token, Duration timeoutConexao, Duration timeoutLeitura) {
}
