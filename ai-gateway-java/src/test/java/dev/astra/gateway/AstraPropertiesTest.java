package dev.astra.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Duration;

import dev.astra.gateway.config.AstraProperties;

import org.junit.jupiter.api.Test;

class AstraPropertiesTest {

    @Test
    void toStringNaoExpoeOToken() {
        AstraProperties propriedades = new AstraProperties("http://astra:8000", "segredo-super-secreto",
                Duration.ofSeconds(2), Duration.ofSeconds(30));

        assertThat(propriedades.toString())
                .doesNotContain("segredo-super-secreto")
                .contains("token=****")
                .contains("http://astra:8000");
    }

    @Test
    void semTokenNaoMostraAsteriscos() {
        AstraProperties propriedades = new AstraProperties("http://astra:8000", "", Duration.ofSeconds(2),
                Duration.ofSeconds(30));

        assertThat(propriedades.toString()).contains("token=,");
    }
}
