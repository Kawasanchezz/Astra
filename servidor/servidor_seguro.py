import os
import subprocess
import time
import sys

def limpar_porta(porta):
    porta = int(porta)
    try:
        saida = subprocess.check_output(["netstat", "-ano"], text=True)
    except (OSError, subprocess.SubprocessError):
        return

    for linha in saida.splitlines():
        if f":{porta} " in linha and "LISTENING" in linha:
            pid = linha.split()[-1]
            if not pid.isdigit():
                continue
            print(f"[!] Limpando porta {porta} (ID do processo: {pid})...")
            try:
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.SubprocessError):
                pass
            time.sleep(0.5)

if __name__ == "__main__":
    print("==========================================")
    print("      INICIALIZADOR DO CHATBOT")
    print("==========================================")

    pasta_backend = os.path.dirname(os.path.abspath(__file__))
    arquivo_main = os.path.join(pasta_backend, "main.py")

    if not os.path.exists(arquivo_main):
        print("[X] Erro: Nao achei o arquivo main.py!")
        sys.exit(1)

    PORTA = 5000
    limpar_porta(PORTA)
    print("[+] Iniciando o sistema...")

    try:
        subprocess.run([sys.executable, "main.py"], cwd=pasta_backend)
    except KeyboardInterrupt:
        print("\n[+] Sistema desligado.")
    except Exception as e:
        print(f"\n[X] Erro: {e}")
    finally:
        print("[+] Liberando a porta...")
        limpar_porta(PORTA)

    input("\nAperte Enter para sair...")
