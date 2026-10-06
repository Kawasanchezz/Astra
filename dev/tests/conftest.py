import os
import sys

# Chave falsa ANTES de importar a config: os testes nunca chamam a Groq de verdade
# (o client e substituido por um falso em cada teste).
os.environ["GROQ_API_KEY"] = "chave-de-teste-nao-usar"
os.environ["APP_ENV"] = "development"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "servidor"))
