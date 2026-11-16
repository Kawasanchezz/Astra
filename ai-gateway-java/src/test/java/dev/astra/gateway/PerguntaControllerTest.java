package dev.astra.gateway;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.containing;
import static com.github.tomakehurst.wiremock.client.WireMock.equalTo;
import static com.github.tomakehurst.wiremock.client.WireMock.matchingJsonPath;
import static com.github.tomakehurst.wiremock.client.WireMock.notMatching;
import static com.github.tomakehurst.wiremock.client.WireMock.okJson;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.postRequestedFor;
import static com.github.tomakehurst.wiremock.client.WireMock.serverError;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static com.github.tomakehurst.wiremock.stubbing.Scenario.STARTED;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import com.github.tomakehurst.wiremock.junit5.WireMockExtension;

import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.RegisterExtension;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

@SpringBootTest(properties = {
        "gateway.limite-por-minuto=100000",
        "astra.token=token-de-teste",
        "astra.timeout-leitura=1s",
        "resilience4j.retry.instances.astra.wait-duration=10ms",
        "resilience4j.retry.instances.astra.enable-exponential-backoff=false",
        "resilience4j.circuitbreaker.instances.astra.sliding-window-size=4",
        "resilience4j.circuitbreaker.instances.astra.minimum-number-of-calls=4"
})
@AutoConfigureMockMvc
class PerguntaControllerTest {

    private static final String RESPOSTA_ASTRA = """
            {"id":"abc","resposta":"Idempotência é repetir a chamada e obter o mesmo resultado [1].",
             "usou_llm":true,
             "fontes":[{"arquivo":"http-e-rest.md","secao":"HTTP e APIs REST > Idempotência","score":0.657}],
             "versao_prompt":"9443c9e176"}""";

    @RegisterExtension
    static WireMockExtension astra = WireMockExtension.newInstance()
            .options(wireMockConfig().dynamicPort()).build();

    @DynamicPropertySource
    static void propriedades(DynamicPropertyRegistry registro) {
        registro.add("astra.base-url", astra::baseUrl);
    }

    @Autowired
    MockMvc mvc;

    @Autowired
    CircuitBreakerRegistry circuitos;

    @BeforeAll
    static void aquecer() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(okJson(RESPOSTA_ASTRA)));
        HttpClient http = HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();
        HttpRequest pedido = HttpRequest.newBuilder(URI.create(astra.baseUrl() + "/ask"))
                .timeout(Duration.ofSeconds(60)).header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString("{\"pergunta\":\"aquecimento\"}")).build();
        http.send(pedido, HttpResponse.BodyHandlers.ofString());
    }

    @BeforeEach
    void limpar() {
        astra.resetAll();
        circuitos.circuitBreaker("astra").reset();
    }

    private ResultActions perguntar(String json) throws Exception {
        return mvc.perform(MockMvcRequestBuilders.post("/api/v1/perguntas").contentType(MediaType.APPLICATION_JSON).content(json));
    }

    private static void astraResponde(int status) {
        astra.stubFor(post(urlEqualTo("/ask"))
                .willReturn(aResponse().withStatus(status).withHeader("Content-Type", "application/json")
                        .withBody("{\"erro\":{\"codigo\":\"x\"}}")));
    }

    private static int chamadasAoAstra() {
        return astra.findAll(postRequestedFor(urlEqualTo("/ask"))).size();
    }

    @Test
    void devolveARespostaMapeandoOsCamposDoAstra() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(okJson(RESPOSTA_ASTRA)));

        perguntar("{\"pergunta\":\"O que é idempotência?\",\"k\":3}")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.resposta").value(containsText("Idempotência")))
                .andExpect(jsonPath("$.usouLlm").value(true))
                .andExpect(jsonPath("$.fontes[0].arquivo").value("http-e-rest.md"))
                .andExpect(jsonPath("$.fontes[0].score").value(0.657))
                .andExpect(jsonPath("$.versaoPrompt").value("9443c9e176"))
                .andExpect(header().exists("X-Request-ID"));

        astra.verify(1, postRequestedFor(urlEqualTo("/ask"))
                .withHeader("Authorization", equalTo("Bearer token-de-teste"))
                .withHeader("Content-Type", containing("application/json"))
                .withRequestBody(matchingJsonPath("$.pergunta", equalTo("O que é idempotência?")))
                .withRequestBody(matchingJsonPath("$.k", equalTo("3"))));
    }

    @Test
    void naoEnviaKAoAstraQuandoOClienteNaoInformou() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(okJson(RESPOSTA_ASTRA)));

        perguntar("{\"pergunta\":\"O que é idempotência?\"}").andExpect(status().isOk());

        astra.verify(1, postRequestedFor(urlEqualTo("/ask")).withRequestBody(notMatching(".*\"k\".*")));
    }

    @Test
    void oIdDeRequisicaoDoClienteVaiParaAResposta_ParaOAstraEParaOCorpo() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(okJson(RESPOSTA_ASTRA)));

        mvc.perform(MockMvcRequestBuilders.post("/api/v1/perguntas").header("X-Request-ID", "gateway-123")
                        .contentType(MediaType.APPLICATION_JSON).content("{\"pergunta\":\"oi\"}"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Request-ID", "gateway-123"))
                .andExpect(jsonPath("$.idRequisicao").value("gateway-123"));

        astra.verify(1, postRequestedFor(urlEqualTo("/ask")).withHeader("X-Request-ID", equalTo("gateway-123")));
    }

    @Test
    void idDeRequisicaoComFormatoSuspeitoEhSubstituido() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(okJson(RESPOSTA_ASTRA)));
        String forjado = "a\"} {\"nivel\": \"ERROR\"}";

        String recebido = mvc.perform(MockMvcRequestBuilders.post("/api/v1/perguntas").header("X-Request-ID", forjado)
                        .contentType(MediaType.APPLICATION_JSON).content("{\"pergunta\":\"oi\"}"))
                .andExpect(status().isOk()).andReturn().getResponse().getHeader("X-Request-ID");

        assertThat(recebido).isNotEqualTo(forjado).hasSize(16).matches("[0-9a-f]{16}");
    }

    @ParameterizedTest(name = "{0}")
    @CsvSource(delimiter = '|', value = {
            "pergunta em branco|{\"pergunta\":\"   \"}|pergunta",
            "pergunta ausente|{}|pergunta",
            "k zero|{\"pergunta\":\"oi\",\"k\":0}|k",
            "k acima do limite|{\"pergunta\":\"oi\",\"k\":11}|k",
    })
    void recusaEntradaInvalidaSemChamarOAstra(String caso, String json, String campo) throws Exception {
        perguntar(json)
                .andExpect(status().isBadRequest())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.campos." + campo).exists())
                .andExpect(jsonPath("$.idRequisicao").isNotEmpty());

        assertThat(chamadasAoAstra()).isZero();
    }

    @Test
    void recusaPerguntaMaiorQueOLimite() throws Exception {
        perguntar("{\"pergunta\":\"" + "a".repeat(501) + "\"}")
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.campos.pergunta").value("A pergunta deve ter no máximo 500 caracteres."));
        assertThat(chamadasAoAstra()).isZero();
    }

    @Test
    void jsonQuebradoDevolve400EmProblemDetail() throws Exception {
        perguntar("{quebrado")
                .andExpect(status().isBadRequest())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.idRequisicao").isNotEmpty());
        assertThat(chamadasAoAstra()).isZero();
    }

    @Test
    void repeteQuandoOAstraFalhaUmaVezEDepoisResponde() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).inScenario("instavel").whenScenarioStateIs(STARTED)
                .willReturn(serverError()).willSetStateTo("recuperado"));
        astra.stubFor(post(urlEqualTo("/ask")).inScenario("instavel").whenScenarioStateIs("recuperado")
                .willReturn(okJson(RESPOSTA_ASTRA)));

        perguntar("{\"pergunta\":\"oi\"}").andExpect(status().isOk());

        assertThat(chamadasAoAstra()).isEqualTo(2);
    }

    @Test
    void desisteDepoisDeTresTentativasEDevolve503() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(serverError()));

        perguntar("{\"pergunta\":\"oi\"}")
                .andExpect(status().isServiceUnavailable())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.idRequisicao").isNotEmpty())
                .andExpect(jsonPath("$.detail").value(org.hamcrest.Matchers.not(containsText("500"))));

        assertThat(chamadasAoAstra()).isEqualTo(3);
    }

    @Test
    void naoRepeteQuandoOAstraRecusaARequisicao_E_Devolve502() throws Exception {
        astraResponde(400);

        perguntar("{\"pergunta\":\"oi\"}")
                .andExpect(status().isBadGateway())
                .andExpect(jsonPath("$.idRequisicao").isNotEmpty());

        assertThat(chamadasAoAstra()).isEqualTo(1);
    }

    @Test
    void tokenRecusadoPeloAstraTambemEhErroDeConfiguracao_502SemRetry() throws Exception {
        astraResponde(401);

        perguntar("{\"pergunta\":\"oi\"}").andExpect(status().isBadGateway());

        assertThat(chamadasAoAstra()).isEqualTo(1);
    }

    @Test
    void estouroDoPrazoDeLeituraDevolve504EAindaTentaTresVezes() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(okJson(RESPOSTA_ASTRA).withFixedDelay(1800)));

        perguntar("{\"pergunta\":\"oi\"}")
                .andExpect(status().isGatewayTimeout())
                .andExpect(jsonPath("$.status").value(504));

        assertThat(chamadasAoAstra()).isEqualTo(3);
    }

    @Test
    void circuitoAbreDepoisDeFalhasEPassaARecusarSemChamarOAstra() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(serverError()));

        perguntar("{\"pergunta\":\"oi\"}").andExpect(status().isServiceUnavailable());
        perguntar("{\"pergunta\":\"oi\"}").andExpect(status().isServiceUnavailable());
        assertThat(circuitos.circuitBreaker("astra").getState()).isEqualTo(CircuitBreaker.State.OPEN);
        int antes = chamadasAoAstra();

        perguntar("{\"pergunta\":\"oi\"}")
                .andExpect(status().isServiceUnavailable())
                .andExpect(header().string("Retry-After", "10"))
                .andExpect(jsonPath("$.detail").value(containsText("circuito")));

        assertThat(chamadasAoAstra()).isEqualTo(antes);
        assertThat(antes).isEqualTo(4);
    }

    @Test
    void erroDeQuemChamouNaoAbreOCircuito() throws Exception {
        astraResponde(400);

        for (int i = 0; i < 6; i++) {
            perguntar("{\"pergunta\":\"oi\"}").andExpect(status().isBadGateway());
        }

        assertThat(circuitos.circuitBreaker("astra").getState()).isEqualTo(CircuitBreaker.State.CLOSED);
        assertThat(chamadasAoAstra()).isEqualTo(6);
    }

    @Test
    void respostaDoAstraForaDoFormatoDevolve502SemRetry() throws Exception {
        astra.stubFor(post(urlEqualTo("/ask")).willReturn(okJson("[1,2,3]")));

        perguntar("{\"pergunta\":\"oi\"}").andExpect(status().isBadGateway());

        assertThat(chamadasAoAstra()).isEqualTo(1);
    }

    @Test
    void openApiDescreveOEndpointDePerguntas() throws Exception {
        mvc.perform(get("/v3/api-docs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.info.title").value("AI Gateway"))
                .andExpect(jsonPath("$.paths['/api/v1/perguntas'].post.summary").exists())
                .andExpect(jsonPath("$.paths['/api/v1/perguntas'].post.responses['503']").exists())
                .andExpect(jsonPath("$.components.schemas.PerguntaRequest.properties.pergunta.maxLength").value(500));
    }

    @Test
    void swaggerUiEstaDisponivel() throws Exception {
        mvc.perform(get("/swagger-ui/index.html")).andExpect(status().isOk());
    }

    @Test
    void endpointsQueExporiamConfiguracaoNaoEstaoDisponiveis() throws Exception {
        for (String caminho : new String[] {"/actuator/env", "/actuator/configprops", "/actuator/beans"}) {
            mvc.perform(get(caminho)).andExpect(status().isNotFound());
        }
    }

    @Test
    void healthResponde200() throws Exception {
        mvc.perform(get("/actuator/health")).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("UP"));
    }

    private static org.hamcrest.Matcher<String> containsText(String trecho) {
        return org.hamcrest.Matchers.containsString(trecho);
    }
}
