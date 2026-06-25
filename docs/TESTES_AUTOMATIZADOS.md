# Testes Automatizados

O arquivo `test_server.py` implementa testes automatizados para validar o comportamento principal do servidor web.

## Como executar

Entre na pasta do projeto:

```bash
cd ServidorWeb
```

Execute:

```bash
python test_server.py
```

Ou, em ambientes onde o comando principal e `python3`:

```bash
python3 test_server.py
```

## Como os testes funcionam

Os testes usam apenas bibliotecas padrao do Python:

- `unittest`, para organizar e executar os casos de teste;
- `socket`, para enviar requisicoes reais ao servidor;
- `subprocess`, para iniciar o servidor automaticamente durante os testes;
- `ThreadPoolExecutor`, para simular varios clientes ao mesmo tempo.

Durante a execucao, o teste:

1. inicia `server.py` em um processo separado;
2. aguarda o servidor ficar disponivel na porta `8080`;
3. envia requisicoes usando sockets TCP;
4. verifica os codigos de resposta;
5. verifica os cabecalhos HTTP principais;
6. encerra o servidor ao final.

## Casos cobertos

### 1. Pagina inicial existente

Requisicao:

```http
GET /index.html HTTP/1.1
```

Resultado esperado:

```http
HTTP/1.1 200 OK
```

### 2. Rota raiz

Requisicao:

```http
GET / HTTP/1.1
```

Resultado esperado:

```http
HTTP/1.1 200 OK
```

Nesse caso, o servidor deve carregar `index.html`.

### 3. Pagina sobre existente

Requisicao:

```http
GET /sobre.html HTTP/1.1
```

Resultado esperado:

```http
HTTP/1.1 200 OK
```

### 4. Arquivo inexistente

Requisicao:

```http
GET /nao_existe.html HTTP/1.1
```

Resultado esperado:

```http
HTTP/1.1 404 Not Found
```

### 5. Metodo invalido

Requisicao:

```http
POST /index.html HTTP/1.1
```

Resultado esperado:

```http
HTTP/1.1 400 Bad Request
```

### 6. Multiplos clientes simultaneos

O teste cria 10 requisicoes em paralelo usando `ThreadPoolExecutor`.

Resultado esperado:

- todas as 10 requisicoes recebem resposta;
- as paginas existentes retornam `200 OK`;
- os arquivos inexistentes retornam `404 Not Found`;
- o servidor continua funcionando enquanto atende varias conexoes.

### 7. Protecao contra acesso fora da pasta publica

Requisicoes testadas:

```http
GET /../server.py HTTP/1.1
GET /..%2Fserver.py HTTP/1.1
GET /%2e%2e/server.py HTTP/1.1
GET /../templates/404.html HTTP/1.1
```

Resultado esperado:

```http
HTTP/1.1 404 Not Found
```

Esses testes garantem que o cliente nao consegue acessar arquivos internos do projeto, como `server.py` ou arquivos dentro de `templates/`.

## Cabecalhos HTTP validados

Apos a segunda melhoria do projeto, os testes tambem verificam se toda resposta possui:

- separacao correta entre cabecalhos e corpo usando `\r\n\r\n`;
- `Content-Type: text/html; charset=utf-8`;
- `Content-Length` com o tamanho correto do corpo da resposta;
- `Connection: close`, indicando que a conexao sera encerrada apos o envio.

## Importancia para a atividade

Esses testes comprovam os principais requisitos do trabalho:

- comunicacao cliente-servidor;
- uso de sockets TCP;
- protocolo de aplicacao baseado em `GET`;
- envio de arquivos HTML locais;
- tratamento de erros;
- protecao contra acesso indevido a arquivos fora de `public/`;
- atendimento simultaneo de varios clientes usando threads.
