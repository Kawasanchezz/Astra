"""Uso (dentro de servidor/):  python -m rag indexar | buscar "pergunta" | perguntar "pergunta" """
import argparse
import sys

from rag.configuracao import DOCS_DIR, INDEX_DIR, MODELO_EMBEDDING, SCORE_MINIMO, TOP_K
from rag.consulta import buscar_contexto, perguntar
from rag.embeddings import FastEmbedEmbedder
from rag.indice import IndiceVetorial, indexar_pasta

def _carregar() -> IndiceVetorial:
    try:
        return IndiceVetorial.carregar(INDEX_DIR, modelo_esperado=MODELO_EMBEDDING)
    except FileNotFoundError:
        sys.exit("Índice não encontrado. Rode primeiro: python -m rag indexar")

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m rag")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("indexar", help="indexa os .md da pasta de documentos")
    for nome, ajuda in (("buscar", "mostra os trechos mais parecidos, sem LLM"),
                        ("perguntar", "busca o contexto e responde com o LLM")):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("pergunta")
        p.add_argument("-k", type=int, default=TOP_K)
        p.add_argument("--score-minimo", type=float, default=SCORE_MINIMO)
    args = parser.parse_args(argv)

    embedder = FastEmbedEmbedder()
    if args.comando == "indexar":
        indice = indexar_pasta(DOCS_DIR, embedder)
        indice.salvar(INDEX_DIR)
        print(f"{len(indice.trechos)} trechos de {DOCS_DIR} indexados em {INDEX_DIR} (modelo {indice.modelo})")
    elif args.comando == "buscar":
        for trecho, score in buscar_contexto(_carregar(), embedder, args.pergunta, args.k, args.score_minimo):
            print(f"{score:.3f}  {trecho.fonte} > {trecho.secao}\n       {trecho.texto[:110]!r}")
    else:
        from rag.llm import llm_groq
        resposta = perguntar(args.pergunta, _carregar(), embedder, llm_groq, args.k, args.score_minimo)
        print(resposta.texto)
        print("\nFontes:", ", ".join(resposta.fontes) or "nenhuma")

if __name__ == "__main__":
    main()
