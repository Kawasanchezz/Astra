package dev.astra.gateway.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    OpenAPI openApi() {
        return new OpenAPI().info(new Info()
                .title("AI Gateway")
                .version("0.1.0")
                .description("Gateway Java que repassa perguntas ao Astra (RAG em Python) com timeout, "
                        + "retry e circuit breaker. Erros seguem o formato RFC 9457 (application/problem+json)."));
    }
}
