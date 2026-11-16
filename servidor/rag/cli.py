"""Uso (dentro de servidor/):  python -m rag indexar | buscar "pergunta" | perguntar "pergunta" | avaliar | servir"""
import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from rag.configuracao import (DOCS_DIR, INDEX_DIR, MODELO_EMBEDDING, PERGUNTAS_AVALIACAO,
                              SCORE_MINIMO, TOP_K)
from rag.consulta import buscar_contexto, perguntar
from rag.embeddings import FastEmbedEmbedder
from rag.indice import IndiceVetorial, indexar_pasta

def configurar_saida_utf8() -> None:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")

def _carregar() -> IndiceVetorial:
    try:
        return IndiceVetorial.carregar(INDEX_DIR, modelo_esperado=MODELO_EMBEDDING)
    except FileNotFoundError:
        sys.exit("Índice não encontrado. Rode primeiro: python -m rag indexar")

def _avaliar(args, embedder) -> None:
    from config import GROQ_MODEL
    from rag.avaliacao import avaliar, carregar_perguntas, resumir
    from rag.llm import llm_groq
    from rag.prompts import prompts_padrao

    prompts = prompts_padrao()
    resultados = avaliar(carregar_perguntas(args.perguntas), _carregar(), embedder, llm_groq,
                         args.k, args.score_minimo, prompts, pausa=args.pausa)
    for r in resultados:
        print(f"{'OK ' if r.aprovado else 'FALHA'}  {r.id}  {r.pergunta}")
        for motivo in r.motivos_de_falha:
            print(f"        - {motivo}")
    resumo = resumir(resultados)
    print("\n" + json.dumps(resumo, ensure_ascii=False, indent=1))
    if args.saida:
        registro = {
            "data": datetime.now().isoformat(timespec="seconds"),
            "versao_prompt": prompts.versao, "modelo_llm": GROQ_MODEL,
            "modelo_embedding": MODELO_EMBEDDING, "k": args.k, "score_minimo": args.score_minimo,
            "resumo": resumo, "resultados": [asdict(r) for r in resultados],
        }
        Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(args.saida).write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
        print("Resultado completo em", args.saida)

def main(argv: list[str] | None = None) -> None:
    configurar_saida_utf8()
    parser = argparse.ArgumentParser(prog="python -m rag")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("indexar", help="indexa os .md da pasta de documentos")
    for nome, ajuda in (("buscar", "mostra os trechos mais parecidos, sem LLM"),
                        ("perguntar", "busca o contexto e responde com o LLM")):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("pergunta")
        p.add_argument("-k", type=int, default=TOP_K)
        p.add_argument("--score-minimo", type=float, default=SCORE_MINIMO)
    av = sub.add_parser("avaliar", help="roda as perguntas de avaliação contra o LLM real")
    av.add_argument("--perguntas", type=Path, default=PERGUNTAS_AVALIACAO)
    av.add_argument("--saida", help="arquivo JSON para gravar o resultado completo")
    av.add_argument("--pausa", type=float, default=1.0, help="segundos entre chamadas ao LLM")
    av.add_argument("-k", type=int, default=TOP_K)
    av.add_argument("--score-minimo", type=float, default=SCORE_MINIMO)
    sub.add_parser("servir", help="sobe a API (/ask e /health) em modo de desenvolvimento")
    args = parser.parse_args(argv)

    if args.comando == "servir":
        from rag.configuracao import API_HOST, API_PORT
        from rag.wsgi import app
        app.run(host=API_HOST, port=API_PORT)
        return

    embedder = FastEmbedEmbedder()
    if args.comando == "indexar":
        indice = indexar_pasta(DOCS_DIR, embedder)
        indice.salvar(INDEX_DIR)
        print(f"{len(indice.trechos)} trechos de {DOCS_DIR} indexados em {INDEX_DIR} (modelo {indice.modelo})")
    elif args.comando == "buscar":
        for trecho, score in buscar_contexto(_carregar(), embedder, args.pergunta, args.k, args.score_minimo):
            print(f"{score:.3f}  {trecho.fonte} > {trecho.secao}\n       {trecho.texto[:110]!r}")
    elif args.comando == "avaliar":
        _avaliar(args, embedder)
    else:
        from rag.llm import llm_groq
        resposta = perguntar(args.pergunta, _carregar(), embedder, llm_groq, args.k, args.score_minimo)
        print(resposta.texto)
        print("\nFontes:", ", ".join(resposta.fontes) or "nenhuma")
        print("Versão dos prompts:", resposta.versao_prompt)

if __name__ == "__main__":
    main()
