import socket
import threading
import os

# Configurações do servidor
HOST = '127.0.0.1'
PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def handle_client(client_socket, client_address):
    print(f"[NOVA CONEXÃO] Cliente conectado: {client_address}")
    
    try:
        # Recebe a requisição do cliente
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return
            
        print(f"[REQUISIÇÃO] {client_address}:")
        print(request.splitlines()[0] if request else "Requisição vazia")
        
        # Extrai o nome do arquivo da requisição HTTP (ex: GET /index.html HTTP/1.1)
        # O split divide por espaços: ['GET', '/index.html', 'HTTP/1.1']
        headers = request.split(' ')
        if len(headers) > 1 and headers[0] == 'GET':
            filename = headers[1]
            
            # Se for '/', carrega o index.html por padrão
            if filename == '/':
                filename = '/index.html'
                
            # Caminho completo para o arquivo local
            filepath = os.path.join(BASE_DIR, filename.lstrip('/'))
            
            # Verifica se o arquivo existe e é um arquivo mesmo
            if os.path.exists(filepath) and os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Monta a resposta de sucesso HTTP 200 OK
                response_header = 'HTTP/1.1 200 OK\nContent-Type: text/html; charset=utf-8\n\n'
                response = response_header + content
                print(f"[SUCESSO] Arquivo '{filename}' enviado para {client_address}.")
            else:
                # Arquivo não encontrado, envia erro HTTP 404 e a página 404
                not_found_path = os.path.join(BASE_DIR, '404.html')
                if os.path.exists(not_found_path):
                    with open(not_found_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    content = "<html><body><h1>404 Not Found</h1></body></html>"
                    
                response_header = 'HTTP/1.1 404 Not Found\nContent-Type: text/html; charset=utf-8\n\n'
                response = response_header + content
                print(f"[ERRO 404] Arquivo '{filename}' não encontrado para {client_address}.")
        else:
            response = 'HTTP/1.1 400 Bad Request\n\n<h1>Bad Request</h1>'
            
        # Envia a resposta de volta ao cliente
        client_socket.sendall(response.encode('utf-8'))
        
    except Exception as e:
        print(f"[ERRO] Falha ao processar requisição de {client_address}: {e}")
    finally:
        # Fecha a conexão com o cliente atual
        client_socket.close()

def start_server():
    # Cria o socket do servidor usando IPv4 (AF_INET) e TCP (SOCK_STREAM)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permite reusar a porta imediatamente após reiniciar o script
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen(5) # Ouve até 5 conexões na fila
    print(f"[SERVIDOR INICIADO] Escutando em http://{HOST}:{PORT}")
    
    try:
        while True:
            # Fica aguardando novas conexões
            client_socket, address = server.accept()
            
            # Cria uma nova thread para lidar com o cliente, 
            # permitindo que o servidor aceite o próximo cliente imediatamente
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.start()
            print(f"[THREADS ATIVAS] {threading.active_count() - 1}") # -1 pq a main conta como 1
            
    except KeyboardInterrupt:
        print("\n[SERVIDOR PARANDO] Encerrando pelo usuário.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
