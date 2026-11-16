package dev.astra.gateway;

import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

/** Nada escuta na porta 1: o Astra está fora do ar, e o gateway precisa responder 503 (indisponível), não 504 (demorou). */
@SpringBootTest(properties = {
        "astra.base-url=http://127.0.0.1:1",
        "astra.timeout-conexao=1s",
        "resilience4j.retry.instances.astra.wait-duration=10ms",
        "resilience4j.retry.instances.astra.enable-exponential-backoff=false"
})
@AutoConfigureMockMvc
class AstraForaDoArTest {

    @Autowired
    MockMvc mvc;

    @Test
    void astraForaDoArDevolve503EnaoDevolve504() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post("/api/v1/perguntas")
                        .contentType(MediaType.APPLICATION_JSON).content("{\"pergunta\":\"oi\"}"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.detail").value("O serviço de IA está indisponível no momento."))
                .andExpect(jsonPath("$.idRequisicao").isNotEmpty());

    }
}
