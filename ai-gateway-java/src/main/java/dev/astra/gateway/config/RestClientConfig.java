package dev.astra.gateway.config;

import java.net.http.HttpClient;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
public class RestClientConfig {

    @Bean
    RestClient astraRestClient(AstraProperties propriedades, RestClient.Builder builder) {
        HttpClient http = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(propriedades.timeoutConexao())
                .build();
        JdkClientHttpRequestFactory fabrica = new JdkClientHttpRequestFactory(http);
        fabrica.setReadTimeout(propriedades.timeoutLeitura());

        RestClient.Builder cliente = builder
                .baseUrl(propriedades.baseUrl())
                .requestFactory(fabrica)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE);
        if (propriedades.token() != null && !propriedades.token().isBlank()) {
            cliente.defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + propriedades.token());
        }
        return cliente.build();
    }
}
