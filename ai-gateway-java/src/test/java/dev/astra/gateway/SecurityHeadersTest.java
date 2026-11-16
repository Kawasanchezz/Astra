package dev.astra.gateway;

import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

@SpringBootTest(properties = "gateway.limite-por-minuto=100000")
@AutoConfigureMockMvc
class SecurityHeadersTest {

    @Autowired
    MockMvc mvc;

    @Test
    void respostasDaApiTrazemOsCabecalhosDefensivos() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post("/api/v1/perguntas")
                        .contentType(MediaType.APPLICATION_JSON).content("{\"pergunta\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(header().string("X-Content-Type-Options", "nosniff"))
                .andExpect(header().string("X-Frame-Options", "DENY"))
                .andExpect(header().string("Referrer-Policy", "no-referrer"))
                .andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(header().string("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"));
    }

    @Test
    void healthTambemNaoPodeSerGuardadoNemEmbutido() throws Exception {
        mvc.perform(MockMvcRequestBuilders.get("/actuator/health"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Frame-Options", "DENY"))
                .andExpect(header().string("Cache-Control", "no-store"));
    }

    @Test
    void documentacaoOpenApiMantemOsCabecalhosBasicos() throws Exception {
        mvc.perform(MockMvcRequestBuilders.get("/v3/api-docs"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Content-Type-Options", "nosniff"))
                .andExpect(header().string("X-Frame-Options", "DENY"));
    }

    @Test
    void preflightDeOutroSiteNaoRecebeNenhumaPermissaoDeCors() throws Exception {
        mvc.perform(MockMvcRequestBuilders.options("/api/v1/perguntas")
                        .header("Origin", "https://evil.test")
                        .header("Access-Control-Request-Method", "POST"))
                .andExpect(header().doesNotExist("Access-Control-Allow-Origin"))
                .andExpect(header().doesNotExist("Access-Control-Allow-Credentials"));
    }

    @Test
    void postComOrigemDeOutroSiteNaoRecebeAllowOrigin() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post("/api/v1/perguntas")
                        .header("Origin", "https://evil.test")
                        .contentType(MediaType.APPLICATION_JSON).content("{\"pergunta\":\"\"}"))
                .andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
    }
}
