package dev.astra.gateway.web;

import dev.astra.gateway.client.AstraClient;
import dev.astra.gateway.client.AstraResposta;
import dev.astra.gateway.web.dto.PerguntaRequest;
import dev.astra.gateway.web.dto.PerguntaResponse;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Perguntas")
public class PerguntaController {

    private static final Logger log = LoggerFactory.getLogger(PerguntaController.class);
    private static final String PROBLEM_JSON = "application/problem+json";

    private final AstraClient astra;

    public PerguntaController(AstraClient astra) {
        this.astra = astra;
    }

    @PostMapping("/perguntas")
    @Operation(summary = "Faz uma pergunta ao Astra",
            description = "Valida a pergunta, repassa ao serviço Python (RAG) e devolve a resposta com as fontes.")
    @ApiResponse(responseCode = "200", description = "Resposta gerada (ou recusa, se os documentos não cobrem o assunto)")
    @ApiResponse(responseCode = "400", description = "Pergunta vazia, longa demais ou k fora de 1 a 10",
            content = @Content(mediaType = PROBLEM_JSON))
    @ApiResponse(responseCode = "502", description = "O Astra recusou a requisição ou respondeu em formato inesperado",
            content = @Content(mediaType = PROBLEM_JSON))
    @ApiResponse(responseCode = "503", description = "O Astra está indisponível ou o circuito está aberto",
            content = @Content(mediaType = PROBLEM_JSON))
    @ApiResponse(responseCode = "504", description = "O Astra não respondeu dentro do prazo",
            content = @Content(mediaType = PROBLEM_JSON))
    public PerguntaResponse perguntar(@Valid @RequestBody PerguntaRequest pedido) {
        String id = MDC.get(RequestIdFilter.CHAVE_MDC);
        String pergunta = pedido.pergunta().strip();
        log.info("pergunta recebida chars={} k={}", pergunta.length(), pedido.k());
        AstraResposta resposta = astra.perguntar(pergunta, pedido.k(), id);
        log.info("resposta devolvida usouLlm={} fontes={}", resposta.usouLlm(),
                resposta.fontes() == null ? 0 : resposta.fontes().size());
        return PerguntaResponse.de(id, resposta);
    }
}
