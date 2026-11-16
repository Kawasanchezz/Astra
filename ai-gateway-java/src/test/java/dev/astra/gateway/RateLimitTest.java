package dev.astra.gateway;

import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

@SpringBootTest(properties = "gateway.limite-por-minuto=3")
@AutoConfigureMockMvc
class RateLimitTest {

    @Autowired
    MockMvc mvc;

    private ResultActions pedir(String ip, String encaminhadoPor) throws Exception {
        var pedido = MockMvcRequestBuilders.post("/api/v1/perguntas")
                .contentType(MediaType.APPLICATION_JSON).content("{\"pergunta\":\"\"}")
                .with(req -> {
                    req.setRemoteAddr(ip);
                    return req;
                });
        if (encaminhadoPor != null) {
            pedido.header("X-Forwarded-For", encaminhadoPor);
        }
        return mvc.perform(pedido);
    }

    @Test
    void depoisDoLimiteODevolve429ComRetryAfterEProblemJson() throws Exception {
        for (int i = 0; i < 3; i++) {
            pedir("10.1.0.1", null).andExpect(status().isBadRequest());
        }

        pedir("10.1.0.1", null)
                .andExpect(status().isTooManyRequests())
                .andExpect(header().string("Retry-After", "60"))
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.status").value(429))
                .andExpect(jsonPath("$.idRequisicao").isNotEmpty());
    }

    @Test
    void cadaIpTemOSeuProprioLimite() throws Exception {
        for (int i = 0; i < 4; i++) {
            pedir("10.2.0.1", null);
        }

        pedir("10.2.0.1", null).andExpect(status().isTooManyRequests());
        pedir("10.2.0.2", null).andExpect(status().isBadRequest());
    }

    @Test
    void xForwardedForNaoBurlaOLimiteSemProxyConfiavel() throws Exception {
        for (int i = 0; i < 3; i++) {
            pedir("10.3.0.1", "203.0.113." + i).andExpect(status().isBadRequest());
        }

        pedir("10.3.0.1", "203.0.113.200").andExpect(status().isTooManyRequests());
    }

    @Test
    void healthNaoEntraNoLimite() throws Exception {
        for (int i = 0; i < 10; i++) {
            mvc.perform(MockMvcRequestBuilders.get("/actuator/health").with(req -> {
                req.setRemoteAddr("10.4.0.1");
                return req;
            })).andExpect(status().isOk());
        }
    }
}
