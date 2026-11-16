package dev.astra.gateway.web;

import java.io.IOException;
import java.time.Duration;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;

import io.github.resilience4j.ratelimiter.RateLimiter;
import io.github.resilience4j.ratelimiter.RateLimiterConfig;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 2)
public class RateLimitFilter extends OncePerRequestFilter {

    private static final int MAX_IPS_RASTREADOS = 10_000;
    private static final int SEGUNDOS_DA_JANELA = 60;

    private final RateLimiterConfig configuracao;
    private final ObjectMapper mapper;
    private final Map<String, RateLimiter> porIp = Collections.synchronizedMap(
            new LinkedHashMap<>(16, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(Map.Entry<String, RateLimiter> eldest) {
                    return size() > MAX_IPS_RASTREADOS;
                }
            });

    public RateLimitFilter(@Value("${gateway.limite-por-minuto:30}") int limitePorMinuto, ObjectMapper mapper) {
        this.configuracao = RateLimiterConfig.custom()
                .limitForPeriod(limitePorMinuto)
                .limitRefreshPeriod(Duration.ofSeconds(SEGUNDOS_DA_JANELA))
                .timeoutDuration(Duration.ZERO)
                .build();
        this.mapper = mapper;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !request.getRequestURI().startsWith("/api/");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        RateLimiter limitador = porIp.computeIfAbsent(request.getRemoteAddr(),
                ip -> RateLimiter.of(ip, configuracao));
        if (limitador.acquirePermission()) {
            chain.doFilter(request, response);
            return;
        }
        ProblemDetail problema = ProblemDetail.forStatusAndDetail(HttpStatus.TOO_MANY_REQUESTS,
                "Muitas requisições. Aguarde um pouco e tente novamente.");
        problema.setTitle(HttpStatus.TOO_MANY_REQUESTS.getReasonPhrase());
        problema.setProperty("idRequisicao", MDC.get(RequestIdFilter.CHAVE_MDC));
        response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
        response.setHeader(HttpHeaders.RETRY_AFTER, String.valueOf(SEGUNDOS_DA_JANELA));
        response.setContentType(MediaType.APPLICATION_PROBLEM_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        mapper.writeValue(response.getWriter(), problema);
    }
}
