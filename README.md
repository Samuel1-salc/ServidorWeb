# Servidor Web Multithread 

Este projeto consiste na implementação de um Servidor Web simples e multithread em Python utilizando a biblioteca padrão de sockets. Ele foi desenvolvido como parte de um trabalho acadêmico de redes.

## O que é o projeto?

O objetivo principal deste projeto é criar um servidor capaz de receber requisições de vários clientes, interpretar comandos HTTP básicos (como o `GET`), ler arquivos HTML do disco rígido e enviá-los de volta como resposta para quem solicitou. 

##  Funcionalidades Atendidas (Requisitos do Trabalho)

De acordo com a especificação (edital do trabalho), as seguintes etapas foram inteiramente compridas:

1. **Comunicação Básica Cliente/Servidor**: Inicialmente, a base foi construída utilizando sockets TCP no Python para garantir o recebimento e o envio de mensagens (bytes) através da rede.
2. **Protocolo de Comunicação Simples**: O servidor foi programado para entender a primeira linha de uma requisição HTTP, extraindo o comando `GET nome_arquivo` (ex: `GET /index.html`).
3. **Serviço de Arquivos Locais**: Após receber a requisição de um arquivo, o servidor localiza a respectiva página no seu diretório (`index.html`, `sobre.html`), faz a leitura em disco e devolve o conteúdo ao cliente (junto com o cabeçalho de sucesso `200 OK`). Caso não ache o arquivo, devolve uma página de erro customizada (`404 Not Found`).
4. **Múltiplos Clientes Simultâneos (Threads)**: O servidor foi adaptado utilizando a biblioteca `threading`. Cada nova conexão recebida é delegada a uma nova thread, permitindo que dezenas de clientes façam requisições ao mesmo tempo sem que o servidor trave esperando o término de um para atender o outro.
5. **Testes do Sistema**: Foi desenvolvido um script de testes (`client.py`) que simula a conexão assíncrona de 10 clientes simultâneos acessando páginas diferentes. Todos são atendidos corretamente de forma concorrente.

## Como Executar

### Pré-requisitos
Apenas o interpretador do **Python 3** instalado na sua máquina. Não é necessário instalar nenhuma biblioteca externa, pois o projeto usa nativamente `socket` e `threading`.

### 1. Rodando o Servidor
Abra um terminal na pasta onde os arquivos estão localizados e inicie o servidor:
```bash
python3 server.py
```
*Aparecerá a mensagem indicando que o servidor iniciou e está escutando na porta 8080.*

### 2. Acessando pelo Navegador Web (Cliente Real)
Como o servidor entende o protocolo padrão HTTP, você pode agir como um cliente comum acessando pelo seu navegador de internet de preferência (Chrome, Firefox, Safari):
- Abra o navegador e acesse: [http://localhost:8080/](http://localhost:8080/) ou [http://localhost:8080/index.html](http://localhost:8080/index.html)
- Acesse a página sobre: [http://localhost:8080/sobre.html](http://localhost:8080/sobre.html)
- Para testar a página de erro (arquivo não existente), acesse: [http://localhost:8080/qualquercoisa](http://localhost:8080/qualquercoisa)

### 3. Executando o Script de Teste Automatizado
Para testar a capacidade de conexões **simultâneas** do servidor, você pode usar o cliente de testes criado. 
Com o servidor ainda rodando no terminal inicial, abra um **novo terminal** na mesma pasta do projeto e execute:
```bash
python3 client.py
```
O script iniciará imediatamente múltiplas requisições (threads) apontando para arquivos diversos do servidor, imprimindo na sua tela o status do que ele recebeu, enquanto o terminal do servidor mostrará todas as threads sendo atendidas ao mesmo tempo.
