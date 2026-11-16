package dev.astra.gateway.web;

import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Garante um X-Request-ID em toda requisição: reaproveita o do cliente só se tiver formato seguro (evita
 * forjar linhas de log) e gera um novo caso contrário. Vai para o MDC, para a resposta e para o Astra.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdFilter extends OncePerRequestFilter {

    static final String CABECALHO = "X-Request-ID";
    static final String CHAVE_MDC = "requestId";
    private static final Pattern VALIDO = Pattern.compile("^[A-Za-z0-9._-]{1,64}$");

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String recebido = request.getHeader(CABECALHO);
        String id = recebido != null && VALIDO.matcher(recebido).matches()
                ? recebido
                : UUID.randomUUID().toString().replace("-", "").substring(0, 16);
        MDC.put(CHAVE_MDC, id);
        response.setHeader(CABECALHO, id);
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove(CHAVE_MDC);
        }
    }
}
