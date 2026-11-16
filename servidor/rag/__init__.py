"""
RAG local do Astra: divide documentos Markdown em trechos, gera embeddings, indexa
no FAISS e monta o prompt com o contexto recuperado.

Fluxo direto, sem framework: cada etapa é uma função pequena e testável.
As dependências pesadas (faiss, fastembed) ficam em requirements-rag.txt, fora do
deploy da Vercel, e nada em servidor/main.py importa este pacote.
"""
