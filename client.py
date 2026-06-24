import socket
import threading
import time
import random

HOST = '127.0.0.1'
PORT = 8080

def request_page(client_id, path):
    """Função simulando um cliente fazendo uma requisição HTTP."""
    print(f"[CLIENTE {client_id}] Iniciando requisição para '{path}'...")
    
    try:
        # Cria o socket do cliente
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        
        # Envia requisição simulando um browser básico
        request = f"GET {path} HTTP/1.1\r\nHost: {HOST}\r\n\r\n"
        client.sendall(request.encode('utf-8'))
        
        # Lê a resposta
        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk
            
        # Decodifica a resposta e extrai apenas a primeira linha (Status) e o título da página
        response_str = response.decode('utf-8')
        status_line = response_str.splitlines()[0] if response_str else "Nenhuma resposta"
        
        print(f"[CLIENTE {client_id}] Sucesso! Resposta do Servidor: {status_line}")
        
    except Exception as e:
        print(f"[CLIENTE {client_id}] Erro de conexão: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("="*50)
    print("INICIANDO TESTE DE MÚLTIPLOS CLIENTES SIMULTÂNEOS")
    print("="*50)
    
    # Lista de páginas que serão requisitadas aleatoriamente
    pages_to_request = ['/index.html', '/sobre.html', '/nao_existe.html', '/', '/arquivo_aleatorio.txt']
    
    threads = []
    
    # Cria 10 clientes (threads) simulando tráfego concorrente
    for i in range(1, 11):
        # Atraso aleatório pequeno para simular requisições naturais
        time.sleep(random.uniform(0.1, 0.3)) 
        
        page = random.choice(pages_to_request)
        t = threading.Thread(target=request_page, args=(i, page))
        threads.append(t)
        t.start()

    # Aguarda todas as threads terminarem
    for t in threads:
        t.join()
        
    print("="*50)
    print("TESTE CONCLUÍDO. TODAS AS REQUISIÇÕES FORAM PROCESSADAS.")
    print("="*50)
