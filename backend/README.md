# 🏐 Rachadez API

**Rachadez** é uma solução de software para o gerenciamento de **rachas esportivos** da **UFCG**, como **vôlei**, **futebol society**, **beach tênis** e **tênis**.  O sistema permite o cadastro e gerenciamento de **usuários internos e externos**, bem como o controle completo de **rachas**, horários, participantes e muito mais.

---

## 📦 Requisitos

Antes de rodar o projeto, você precisará instalar os seguintes itens:

- **[Python 3.11+](https://www.python.org/downloads/)**
- **[Poetry](https://python-poetry.org/docs/#installation)** – Gerenciador de dependências usado no projeto
- **[Docker](https://docs.docker.com/get-docker/)** e **[Docker Compose](https://docs.docker.com/compose/)** – Para subir a base de dados
- **[Make](https://www.gnu.org/software/make/)** (opcional, mas recomendado para facilitar os comandos)

---

## Setup

## ⚙️ Setup do Projeto

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/rachadez-api.git
cd rachadez-api
```
### 2. Instale as dependências
```bash
poetry install
```
---

## 🧪 Estrutura do Projeto
```
├── api -> Api main directory.
│   ├── main.py
│   ├── models -> All entities models.
│   │   └── example.py
│   ├── services -> Service package containing the methods logic.
│   │   └── example.py
│   └── routes -> Package with API routes. The files must sent request to service execute.
│   |   └── example.py
|   └── utils -> Package with utils functions. services and routes could use this directory.   
│       └── example.py
├── core -> Core files to the project such as db connection and configuration variables.
│   ├── config.py
│   └── db.py
├── main.py
└── tests
```
---

## 🚀 Como rodar o projeto

### 1. Subir o banco de dados (PostgreSQL)

```bash
make db-up
```
> Isso utiliza o docker-compose para iniciar um container com o banco de dados configurado

### 2. Rodar o serviço de desenvolvimento

```bash
make run-dev
```
> O servidor estará disponível em: http://localhost:8000/v1

### 3. Voce pode testar com:

```bash
    curl http://localhost:8000/docs
```

### 4. Rodar os testes:
```bash
    make test
```
---

## 🤝 Como Contribuir

1. Faça um **fork** do projeto
2. Crie uma nova **branch** seguindo o padrão:

| Tipo     | Uso                                                  |
|----------|------------------------------------------------------|
| `feat/`  | Novas funcionalidades                                |
| `fix/`   | Correções de bugs                                    |
| `dev/`   | Desenvolvimento geral e integração de funcionalidades |
| `refactor/`, `test/`, etc | Outras categorias conforme necessário         |

Exemplo:
```bash
git checkout -b feat/adicionar-cadastro-usuario
```
Submeta um pull request com uma descrição detalhada do que foi alterado

Template de PR:
```
## What this PR does

Breve explicação do que foi feito, qual problema resolve ou qual funcionalidade adiciona.

## Related issues

Se houver, referencie o número da issue, ex: Closes #10
```
> ⚠️ Mantenha sua branch atualizada com a main ou dev para evitar conflitos.

---
