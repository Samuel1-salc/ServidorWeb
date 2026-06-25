import socket
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8080
BASE_DIR = Path(__file__).resolve().parent.parent


# Padroniza as mensagens exibidas durante os testes.
def log_step(message):
    print(f"\n[TESTE] {message}", flush=True)


def wait_for_server(timeout=5):
    """Aguarda ate que o servidor aceite conexoes TCP."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)

    raise RuntimeError("Servidor nao iniciou dentro do tempo esperado.")


def send_request(raw_request, description=None):
    """Envia uma requisicao HTTP simples e retorna a resposta completa."""
    if description:
        log_step(f"Enviando requisicao: {description}")

    client = socket.create_connection((HOST, PORT), timeout=3)
    try:
        client.settimeout(3)
        client.sendall(raw_request.encode("utf-8"))

        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk

        response_text = response.decode("utf-8", errors="replace")
        status_line = response_text.splitlines()[0] if response_text else "Sem resposta"

        if description:
            log_step(f"Resposta recebida para {description}: {status_line}")

        return response_text
    finally:
        client.close()


def assert_standard_http_headers(test_case, response):
    """Confere cabecalhos HTTP basicos enviados pelo servidor."""
    header_text, separator, body = response.partition("\r\n\r\n")
    test_case.assertEqual(separator, "\r\n\r\n")
    test_case.assertIn("Content-Type: text/html; charset=utf-8", header_text)
    test_case.assertIn("Connection: close", header_text)

    content_length_line = next(
        line for line in header_text.split("\r\n") if line.startswith("Content-Length:")
    )
    content_length = int(content_length_line.split(":", 1)[1].strip())
    test_case.assertEqual(content_length, len(body.encode("utf-8")))


class ServerTests(unittest.TestCase):
    # O servidor e iniciado uma unica vez antes da bateria de testes.
    @classmethod
    def setUpClass(cls):
        log_step("Iniciando server.py em um processo separado.")
        cls.server = subprocess.Popen(
            [sys.executable, str(BASE_DIR / "server.py")],
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        log_step(f"Aguardando servidor ficar disponivel em {HOST}:{PORT}.")
        wait_for_server()
        log_step("Servidor disponivel. Iniciando casos de teste.")

    # Ao final, o processo do servidor e encerrado para liberar a porta.
    @classmethod
    def tearDownClass(cls):
        log_step("Encerrando o processo do servidor usado nos testes.")
        if cls.server.poll() is None:
            cls.server.terminate()
            cls.server.wait(timeout=5)

    def test_index_exists(self):
        """Valida o carregamento direto da pagina inicial."""
        response = send_request(
            "GET /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET /index.html deve retornar 200 OK",
        )
        self.assertTrue(response.startswith("HTTP/1.1 200 OK"))
        assert_standard_http_headers(self, response)
        self.assertIn("Bem-vindo", response)
        log_step("Validacao concluida: /index.html retornou 200 OK e conteudo esperado.")

    def test_root_loads_index(self):
        """Valida se a rota raiz carrega o arquivo index.html."""
        response = send_request(
            "GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET / deve carregar index.html",
        )
        self.assertTrue(response.startswith("HTTP/1.1 200 OK"))
        assert_standard_http_headers(self, response)
        log_step("Validacao concluida: / retornou 200 OK.")

    def test_about_exists(self):
        """Valida o carregamento de uma segunda pagina existente."""
        response = send_request(
            "GET /sobre.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET /sobre.html deve retornar 200 OK",
        )
        self.assertTrue(response.startswith("HTTP/1.1 200 OK"))
        assert_standard_http_headers(self, response)
        log_step("Validacao concluida: /sobre.html retornou 200 OK.")

    def test_error_page_not_directly_accessible(self):
        """Valida que a pagina de erro nao e servida como recurso estatico."""
        response = send_request(
            "GET /404.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET /404.html deve retornar 404 Not Found",
        )
        self.assertTrue(response.startswith("HTTP/1.1 404 Not Found"))
        assert_standard_http_headers(self, response)
        self.assertIn("404", response)
        log_step("Validacao concluida: /404.html nao e acessivel diretamente.")

    def test_not_found(self):
        """Valida o tratamento de erro para arquivos inexistentes."""
        response = send_request(
            "GET /nao_existe.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET /nao_existe.html deve retornar 404 Not Found",
        )
        self.assertTrue(response.startswith("HTTP/1.1 404 Not Found"))
        assert_standard_http_headers(self, response)
        self.assertIn("404", response)
        log_step("Validacao concluida: arquivo inexistente retornou 404 Not Found.")

    def test_path_traversal_is_blocked(self):
        """Valida que o cliente nao consegue acessar arquivos fora de public/."""
        malicious_paths = [
            "/../server.py",
            "/..%2Fserver.py",
            "/%2e%2e/server.py",
            "/../templates/404.html",
        ]

        for path in malicious_paths:
            response = send_request(
                f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
                f"GET {path} deve ser bloqueado",
            )
            self.assertTrue(response.startswith("HTTP/1.1 404 Not Found"))
            assert_standard_http_headers(self, response)
            self.assertNotIn("def handle_client", response)
            self.assertNotIn("build_http_response", response)

        log_step("Validacao concluida: tentativas de path traversal foram bloqueadas.")

    def test_invalid_method(self):
        """Valida o tratamento de uma requisicao com metodo nao suportado."""
        response = send_request(
            "POST /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "POST /index.html deve retornar 400 Bad Request",
        )
        self.assertTrue(response.startswith("HTTP/1.1 400 Bad Request"))
        assert_standard_http_headers(self, response)
        self.assertIn("404", response)
        log_step("Validacao concluida: metodo invalido retornou 400 Bad Request com pagina de erro.")

    def test_multiple_clients_at_the_same_time(self):
        """Valida o atendimento de varios clientes simultaneos."""
        requests = [
            "GET /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET /sobre.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET /nao_existe.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
            "GET /arquivo_aleatorio.txt HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n",
        ] * 2

        log_step("Disparando 10 requisicoes simultaneas contra o servidor.")
        # ThreadPoolExecutor simula varios clientes acessando o servidor ao mesmo tempo.
        with ThreadPoolExecutor(max_workers=10) as executor:
            responses = list(
                executor.map(
                    send_request,
                    requests,
                    [f"cliente simultaneo {index}" for index in range(1, 11)],
                )
            )

        self.assertEqual(len(responses), 10)
        for response in responses:
            assert_standard_http_headers(self, response)

        self.assertGreaterEqual(
            sum(response.startswith("HTTP/1.1 200 OK") for response in responses),
            6,
        )
        self.assertGreaterEqual(
            sum(response.startswith("HTTP/1.1 404 Not Found") for response in responses),
            4,
        )
        log_step("Validacao concluida: 10 clientes simultaneos receberam resposta.")


if __name__ == "__main__":
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    unittest.main(testRunner=runner)
