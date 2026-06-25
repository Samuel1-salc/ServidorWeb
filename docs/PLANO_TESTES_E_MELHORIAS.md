# Plano de Testes e Melhorias

Este documento descreve como testar o servidor web simplificado e quais melhorias podem aumentar o escopo do projeto sem fugir da proposta da atividade de Redes de Computadores.

## 1. O que o projeto precisa demonstrar

Pelos requisitos da atividade, o sistema deve demonstrar:

- comunicacao cliente-servidor usando sockets;
- definicao de um protocolo de aplicacao;
- servidor capaz de ler arquivos locais;
- tratamento de erros;
- atendimento simultaneo de varios clientes por meio de threads;
- testes com clientes acessando paginas ao mesmo tempo.

## 2. Testes recomendados

### Teste 1: pagina existente

Objetivo: verificar se o servidor retorna uma pagina HTML existente.

Entrada:

```http
GET /index.html HTTP/1.1
Host: 127.0.0.1
```

Resultado esperado:

```http
HTTP/1.1 200 OK
```

E o corpo da resposta deve conter o conteudo de `index.html`.

### Teste 2: rota raiz

Objetivo: verificar se o servidor trata `/` como `index.html`.

Entrada:

```http
GET / HTTP/1.1
Host: 127.0.0.1
```

Resultado esperado:

```http
HTTP/1.1 200 OK
```

### Teste 3: arquivo inexistente

Objetivo: verificar o tratamento de erro quando o arquivo nao existe.

Entrada:

```http
GET /nao_existe.html HTTP/1.1
Host: 127.0.0.1
```

Resultado esperado:

```http
HTTP/1.1 404 Not Found
```

E o corpo da resposta deve conter a pagina `404.html`.

### Teste 4: metodo invalido

Objetivo: verificar se o servidor rejeita comandos diferentes de `GET`.

Entrada:

```http
POST /index.html HTTP/1.1
Host: 127.0.0.1
```

Resultado esperado:

```http
HTTP/1.1 400 Bad Request
```

Opcionalmente, o projeto pode evoluir para retornar `405 Method Not Allowed`, que seria ainda mais correto semanticamente.

### Teste 5: multiplos clientes simultaneos

Objetivo: comprovar que o servidor nao atende apenas um cliente por vez.

Procedimento:

1. Iniciar o servidor.
2. Executar `client.py`.
3. Observar que varios clientes fazem requisicoes para paginas diferentes.
4. Verificar no terminal do servidor que cada conexao cria uma thread propria.

Resultado esperado:

- todos os clientes recebem uma resposta;
- o servidor continua aceitando conexoes enquanto outras estao sendo processadas;
- aparecem logs de varias threads ativas no servidor.

## 3. Como implementar testes automatizados

Uma forma simples e adequada para a atividade e criar um arquivo `test_server.py` usando apenas a biblioteca padrao do Python.

A ideia e:

1. subir o servidor em um processo separado;
2. enviar requisicoes por socket;
3. verificar a primeira linha da resposta;
4. encerrar o servidor ao final dos testes.

Exemplo de estrutura:

```python
import socket
import subprocess
import time
import unittest

HOST = "127.0.0.1"
PORT = 8080


def send_request(raw_request):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        client.sendall(raw_request.encode("utf-8"))
        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk
        return response.decode("utf-8", errors="replace")
    finally:
        client.close()


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = subprocess.Popen(["python", "server.py"])
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait()

    def test_index_exists(self):
        response = send_request("GET /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        self.assertTrue(response.startswith("HTTP/1.1 200 OK"))

    def test_root_loads_index(self):
        response = send_request("GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        self.assertTrue(response.startswith("HTTP/1.1 200 OK"))

    def test_not_found(self):
        response = send_request("GET /nao_existe.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        self.assertTrue(response.startswith("HTTP/1.1 404 Not Found"))

    def test_invalid_method(self):
        response = send_request("POST /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        self.assertTrue(response.startswith("HTTP/1.1 400 Bad Request"))


if __name__ == "__main__":
    unittest.main()
```

Execucao:

```bash
python test_server.py
```

## 4. Melhorias de escopo recomendadas

### Melhoria 1: proteger acesso a arquivos fora da pasta do projeto

Problema atual:

Um cliente pode tentar pedir caminhos como:

```http
GET /../arquivo.txt HTTP/1.1
```

Melhoria:

Resolver o caminho absoluto e verificar se ele continua dentro de `BASE_DIR`.

Impacto na apresentacao:

Mostra preocupacao com seguranca em aplicacoes de rede.

### Melhoria 2: usar cabecalhos HTTP mais completos

Hoje o servidor ja envia status e `Content-Type`, mas pode ficar mais correto incluindo:

- `Content-Length`;
- `Connection: close`;
- separacao dos cabecalhos com `\r\n`.

Impacto na apresentacao:

Mostra que o grupo entende que HTTP e um protocolo de aplicacao com formato de mensagem.

### Melhoria 3: separar parsing, resposta e leitura de arquivos

O codigo pode ser organizado em funcoes como:

- `parse_request`;
- `build_response`;
- `resolve_file_path`;
- `handle_client`.

Impacto na apresentacao:

Facilita explicar o fluxo do servidor e deixa o projeto mais profissional.

### Melhoria 4: registrar logs mais completos

Adicionar logs com:

- endereco IP e porta do cliente;
- arquivo solicitado;
- codigo de status retornado;
- nome da thread.

Impacto na apresentacao:

Ajuda a demonstrar a concorrencia em tempo real.

### Melhoria 5: simular clientes com atraso

Inserir um pequeno atraso opcional no servidor ou no cliente para evidenciar que um cliente lento nao bloqueia os outros.

Impacto na apresentacao:

Fica visualmente claro por que threads sao importantes.

### Melhoria 6: suportar arquivos estaticos simples

O servidor pode detectar o tipo do arquivo:

- `.html`: `text/html`;
- `.css`: `text/css`;
- `.js`: `application/javascript`;
- `.png`: `image/png`.

Impacto na apresentacao:

Aproxima o sistema de um servidor web real.

## 5. Prioridade sugerida

Para melhorar o projeto sem complicar demais, a ordem recomendada e:

1. adicionar testes automatizados;
2. melhorar os cabecalhos HTTP;
3. proteger caminhos de arquivo;
4. melhorar logs;
5. organizar o codigo em funcoes menores;
6. opcionalmente suportar CSS, JS e imagens.

