import socket
import sys
import threading
import time
import random

HOST = '127.0.0.1'
PORT = 8080

EXPECTED_STATUS = {
    '/index.html': 'HTTP/1.1 200 OK',
    '/': 'HTTP/1.1 200 OK',
    '/sobre.html': 'HTTP/1.1 200 OK',
    '/nao_existe.html': 'HTTP/1.1 404 Not Found',
    '/arquivo_aleatorio.txt': 'HTTP/1.1 404 Not Found',
}

EXPECTED_BODY_SNIPPET = {
    '/index.html': 'Bem-vindo',
    '/': 'Bem-vindo',
    '/sobre.html': 'Sobre o Projeto',
    '/nao_existe.html': '404',
    '/arquivo_aleatorio.txt': '404',
}

results_lock = threading.Lock()
results = {'passed': 0, 'failed': 0}


def validate_response(client_id, path, response_bytes):
    """Valida status HTTP, cabecalhos e fechamento da conexao apos a resposta."""
    errors = []

    if not response_bytes:
        return ['Nenhuma resposta recebida do servidor']

    response = response_bytes.decode('utf-8', errors='replace')
    lines = response.split('\r\n')
    status_line = lines[0] if lines else ''

    expected_status = EXPECTED_STATUS.get(path)
    if expected_status and not status_line.startswith(expected_status):
        errors.append(f"Status esperado '{expected_status}', recebido '{status_line}'")

    header_text, separator, body = response.partition('\r\n\r\n')
    if separator != '\r\n\r\n':
        errors.append('Separador de cabecalhos HTTP invalido')

    if 'Content-Type: text/html; charset=utf-8' not in header_text:
        errors.append('Cabecalho Content-Type ausente ou incorreto')

    if 'Connection: close' not in header_text:
        errors.append('Cabecalho Connection: close ausente')

    content_length_line = next(
        (line for line in header_text.split('\r\n') if line.startswith('Content-Length:')),
        None,
    )
    if not content_length_line:
        errors.append('Cabecalho Content-Length ausente')
    else:
        declared_length = int(content_length_line.split(':', 1)[1].strip())
        actual_length = len(body.encode('utf-8'))
        if declared_length != actual_length:
            errors.append(
                f'Content-Length incorreto: declarado {declared_length}, real {actual_length}'
            )

    expected_snippet = EXPECTED_BODY_SNIPPET.get(path)
    if expected_snippet and expected_snippet not in body:
        errors.append(f"Corpo da resposta nao contem '{expected_snippet}'")

    return errors


def request_page(client_id, path):
    """Simula um cliente HTTP e valida a resposta apos a requisicao."""
    print(f"[CLIENTE {client_id}] Iniciando requisicao para '{path}'...")

    client = None
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)
        client.connect((HOST, PORT))
        print(f"[CLIENTE {client_id}] Conexao TCP estabelecida com {HOST}:{PORT}")

        request = f"GET {path} HTTP/1.1\r\nHost: {HOST}\r\n\r\n"
        client.sendall(request.encode('utf-8'))

        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk

        status_line = response.decode('utf-8', errors='replace').splitlines()
        status_line = status_line[0] if status_line else 'Sem resposta'
        print(f"[CLIENTE {client_id}] Resposta recebida: {status_line}")

        errors = validate_response(client_id, path, response)

        with results_lock:
            if errors:
                results['failed'] += 1
                print(f"[CLIENTE {client_id}] FALHA na validacao:")
                for error in errors:
                    print(f"  - {error}")
            else:
                results['passed'] += 1
                print(f"[CLIENTE {client_id}] Validacao concluida com sucesso.")

    except OSError as e:
        with results_lock:
            results['failed'] += 1
        print(f"[CLIENTE {client_id}] Erro de conexao: {e}")
    finally:
        if client:
            client.close()
            print(f"[CLIENTE {client_id}] Conexao encerrada.")


if __name__ == "__main__":
    print("=" * 50)
    print("INICIANDO TESTE DE MULTIPLOS CLIENTES SIMULTANEOS")
    print("=" * 50)

    pages_to_request = [
        '/index.html', '/sobre.html', '/nao_existe.html', '/',
        '/arquivo_aleatorio.txt',
    ]

    threads = []

    for i in range(1, 11):
        time.sleep(random.uniform(0.1, 0.3))

        page = random.choice(pages_to_request)
        thread = threading.Thread(target=request_page, args=(i, page))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("=" * 50)
    print(f"TESTE CONCLUIDO: {results['passed']} validacoes OK, {results['failed']} falhas.")
    print("=" * 50)

    if results['failed'] > 0:
        sys.exit(1)
