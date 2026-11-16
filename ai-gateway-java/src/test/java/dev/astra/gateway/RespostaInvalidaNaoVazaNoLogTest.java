package dev.astra.gateway;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;

import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.classic.spi.IThrowableProxy;
import ch.qos.logback.core.read.ListAppender;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

@SpringBootTest(properties = {
        "gateway.limite-por-minuto=100000",
        "resilience4j.retry.instances.astra.wait-duration=10ms",
        "resilience4j.retry.instances.astra.enable-exponential-backoff=false"
})
@AutoConfigureMockMvc
class RespostaInvalidaNaoVazaNoLogTest {

    private static final String SEGREDO_DO_MODELO = "texto-privado-do-modelo-XYZ123";
    private static HttpServer servidorFalso;

    @Autowired
    MockMvc mvc;

    @BeforeAll
    static void subirAstraFalso() throws IOException {
        servidorFalso = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        servidorFalso.createContext("/ask", troca -> {
            byte[] corpo = ("{\"resposta\":\"" + SEGREDO_DO_MODELO + "\", \"fontes\": xyz}").getBytes(StandardCharsets.UTF_8);
            troca.getResponseHeaders().add("Content-Type", "application/json");
            troca.sendResponseHeaders(200, corpo.length);
            troca.getResponseBody().write(corpo);
            troca.close();
        });
        servidorFalso.start();
    }

    @AfterAll
    static void derrubarAstraFalso() {
        servidorFalso.stop(0);
    }

    @DynamicPropertySource
    static void apontarParaAstraFalso(DynamicPropertyRegistry registro) {
        registro.add("astra.base-url", () -> "http://127.0.0.1:" + servidorFalso.getAddress().getPort());
    }

    @Test
    void respostaMalformadaDoModeloNaoApareceEmNenhumLog() throws Exception {
        Logger logger = (Logger) LoggerFactory.getLogger("dev.astra.gateway");
        ListAppender<ILoggingEvent> captura = new ListAppender<>();
        captura.start();
        logger.addAppender(captura);
        try {
            mvc.perform(MockMvcRequestBuilders.post("/api/v1/perguntas")
                            .contentType(MediaType.APPLICATION_JSON).content("{\"pergunta\":\"oi\"}"))
                    .andExpect(status().isBadGateway());

            List<ILoggingEvent> eventos = captura.list;
            assertThat(eventos).isNotEmpty();
            for (ILoggingEvent evento : eventos) {
                assertThat(evento.getFormattedMessage()).doesNotContain(SEGREDO_DO_MODELO);
                for (IThrowableProxy causa = evento.getThrowableProxy(); causa != null; causa = causa.getCause()) {
                    assertThat(causa.getMessage()).doesNotContain(SEGREDO_DO_MODELO);
                }
            }
        } finally {
            logger.detachAppender(captura);
        }
    }
}
