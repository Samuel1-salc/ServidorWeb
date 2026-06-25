import os
import socket
import threading
from urllib.parse import unquote, urlsplit

# Configurações do servidor
HOST = '127.0.0.1'
PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
ERROR_PAGE = os.path.join(BASE_DIR, 'templates', '404.html')


def build_http_response(status_line, content, content_type='text/html; charset=utf-8'):
    body = content.encode('utf-8')
    headers = (
        f"{status_line}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return headers.encode('utf-8') + body


def load_error_page():
    if os.path.exists(ERROR_PAGE):
        with open(ERROR_PAGE, 'r', encoding='utf-8') as f:
            return f.read()
    return "<html><body><h1>404 Not Found</h1></body></html>"


def build_error_response(status_line):
    return build_http_response(status_line, load_error_page())


def resolve_public_file(url_path):
    path = unquote(urlsplit(url_path).path)

    if path == '/':
        path = '/index.html'

    if os.path.isabs(path.lstrip('/')):
        return None

    # A pagina de erro nao e servida como recurso estatico.
    blocked_paths = {'/404.html', '/templates/404.html'}
    if path in blocked_paths:
        return None

    relative_path = path.lstrip('/')
    filepath = os.path.join(PUBLIC_DIR, relative_path)

    real_public = os.path.realpath(PUBLIC_DIR)
    real_file = os.path.realpath(filepath)
    try:
        if os.path.commonpath([real_public, real_file]) != real_public:
            return None
    except ValueError:
        return None

    if os.path.exists(real_file) and os.path.isfile(real_file):
        return real_file

    return None


def is_browser_probe(url_path):
    """Requisicoes automaticas de navegadores que podem ser ignoradas no log."""
    path = unquote(urlsplit(url_path).path)
    return path == '/favicon.ico' or path.startswith('/.well-known/')


def handle_client(client_socket, client_address):
    print(f"[NOVA CONEXÃO] Cliente conectado: {client_address}")

    try:
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return

        print(f"[REQUISIÇÃO] {client_address}:")
        print(request.splitlines()[0] if request else "Requisição vazia")

        headers = request.split(' ')
        if len(headers) > 1 and headers[0] == 'GET':
            filename = headers[1]
            filepath = resolve_public_file(filename)

            if filepath:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                response = build_http_response('HTTP/1.1 200 OK', content)
                print(f"[SUCESSO] Arquivo '{filename}' enviado para {client_address}.")
            else:
                response = build_error_response('HTTP/1.1 404 Not Found')
                if is_browser_probe(filename):
                    print(f"[INFO] Requisição automática do navegador: '{filename}'")
                else:
                    print(f"[ERRO 404] Arquivo '{filename}' não encontrado para {client_address}.")
        else:
            response = build_error_response('HTTP/1.1 400 Bad Request')
            print(f"[ERRO 400] Requisição inválida de {client_address}.")

        client_socket.sendall(response)

    except Exception as e:
        print(f"[ERRO] Falha ao processar requisição de {client_address}: {e}")
    finally:
        client_socket.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVIDOR INICIADO] Escutando em http://{HOST}:{PORT}")

    try:
        while True:
            client_socket, address = server.accept()

            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.start()
            print(f"[THREADS ATIVAS] {threading.active_count() - 1}")

    except KeyboardInterrupt:
        print("\n[SERVIDOR PARANDO] Encerrando pelo usuário.")
    finally:
        server.close()


if __name__ == "__main__":
    start_server()
