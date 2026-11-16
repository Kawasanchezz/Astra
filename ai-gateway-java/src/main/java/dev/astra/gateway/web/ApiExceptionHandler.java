package dev.astra.gateway.web;

import java.util.LinkedHashMap;
import java.util.Map;

import dev.astra.gateway.client.AstraFalhaTransitoriaException;
import dev.astra.gateway.client.AstraRejeitouException;
import dev.astra.gateway.client.AstraRespostaInvalidaException;

import io.github.resilience4j.circuitbreaker.CallNotPermittedException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.lang.Nullable;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@RestControllerAdvice
public class ApiExceptionHandler extends ResponseEntityExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);
    private static final int SEGUNDOS_RETRY_AFTER = 10;

    @ExceptionHandler(AstraFalhaTransitoriaException.class)
    ProblemDetail falhaTransitoria(AstraFalhaTransitoriaException e) {
        log.warn("Astra indisponível após as tentativas: {} (timeout={})", e.getMessage(), e.isTimeout());
        return e.isTimeout()
                ? problema(HttpStatus.GATEWAY_TIMEOUT, "O Astra demorou demais para responder.")
                : problema(HttpStatus.SERVICE_UNAVAILABLE, "O serviço de IA está indisponível no momento.");
    }

    @ExceptionHandler(CallNotPermittedException.class)
    ResponseEntity<ProblemDetail> circuitoAberto(CallNotPermittedException e) {
        log.warn("Circuito aberto: chamada ao Astra não foi tentada");
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .header(HttpHeaders.RETRY_AFTER, String.valueOf(SEGUNDOS_RETRY_AFTER))
                .body(problema(HttpStatus.SERVICE_UNAVAILABLE,
                        "O serviço de IA está instável; o circuito está aberto. Tente novamente em instantes."));
    }

    @ExceptionHandler(AstraRejeitouException.class)
    ProblemDetail astraRejeitou(AstraRejeitouException e) {
        log.warn("{}", e.getMessage());
        return problema(HttpStatus.BAD_GATEWAY, "O serviço de IA recusou a requisição.");
    }

    @ExceptionHandler(AstraRespostaInvalidaException.class)
    ProblemDetail respostaInvalida(AstraRespostaInvalidaException e) {
        log.error("{}", e.getMessage(), e);
        return problema(HttpStatus.BAD_GATEWAY, "O serviço de IA respondeu em formato inesperado.");
    }

    @ExceptionHandler(Exception.class)
    ProblemDetail inesperado(Exception e) {
        log.error("Erro inesperado: {}", e.getClass().getSimpleName(), e);
        return problema(HttpStatus.INTERNAL_SERVER_ERROR, "Erro interno no servidor.");
    }

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(MethodArgumentNotValidException ex,
            HttpHeaders headers, HttpStatusCode status, WebRequest request) {
        Map<String, String> campos = new LinkedHashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(erro -> campos.putIfAbsent(erro.getField(), erro.getDefaultMessage()));
        ProblemDetail problema = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Os dados enviados são inválidos.");
        problema.setTitle("Requisição inválida");
        problema.setProperty("campos", campos);
        return handleExceptionInternal(ex, problema, headers, status, request);
    }

    @Override
    protected ResponseEntity<Object> handleExceptionInternal(Exception ex, @Nullable Object body, HttpHeaders headers,
            HttpStatusCode statusCode, WebRequest request) {
        ResponseEntity<Object> resposta = super.handleExceptionInternal(ex, body, headers, statusCode, request);
        if (resposta != null && resposta.getBody() instanceof ProblemDetail problema) {
            problema.setProperty("idRequisicao", MDC.get(RequestIdFilter.CHAVE_MDC));
        }
        return resposta;
    }

    private static ProblemDetail problema(HttpStatus status, String detalhe) {
        ProblemDetail problema = ProblemDetail.forStatusAndDetail(status, detalhe);
        problema.setTitle(status.getReasonPhrase());
        problema.setProperty("idRequisicao", MDC.get(RequestIdFilter.CHAVE_MDC));
        return problema;
    }
}
