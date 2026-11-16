package dev.astra.gateway.web.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PerguntaRequest(
        @Schema(description = "Pergunta sobre os documentos de estudo", example = "O que é idempotência em APIs?",
                maxLength = 500)
        @NotBlank(message = "A pergunta é obrigatória.")
        @Size(max = 500, message = "A pergunta deve ter no máximo 500 caracteres.") String pergunta,
        @Schema(description = "Quantos trechos recuperar (padrão do serviço: 4)", example = "4",
                minimum = "1", maximum = "10")
        @Min(value = 1, message = "k deve ser no mínimo 1.")
        @Max(value = 10, message = "k deve ser no máximo 10.") Integer k) {
}
