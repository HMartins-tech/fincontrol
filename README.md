# 💰 FinControl

Sistema de **Controle Financeiro Pessoal** desenvolvido como projeto acadêmico
(PIT II) em **Python/Flask** com **MySQL**.

O sistema permite que cada usuário cadastre suas **receitas** e **despesas**,
organize-as por **categoria** e acompanhe o **saldo** em tempo real por meio de
um dashboard — vendo apenas os seus próprios dados.

---

## 🚀 Funcionalidades

- **Cadastro de usuário** com senha protegida por hash (scrypt)
- **Login e logout** com sessão assinada
- **Proteção de rotas** — nenhuma rota de dados é acessível sem autenticação
- **CRUD completo** de receitas e despesas (criar, listar, editar, excluir)
- **Categorização** por tipo (receita / despesa)
- **Dashboard** com totais de receita, despesa e saldo
- **Isolamento de dados** — cada usuário vê apenas as suas transações
- **Validação de valores** — recusa número inválido, zero ou negativo
- **Confirmação** antes de excluir registros

---

## 🛠️ Tecnologias

| Camada          | Tecnologia                 |
| --------------- | -------------------------- |
| Linguagem       | Python 3.10+               |
| Framework Web   | Flask                      |
| Driver MySQL    | flask-mysqldb              |
| Banco de Dados  | MySQL 8                    |
| Template Engine | Jinja2                     |
| Front-end       | HTML5, CSS3, Bootstrap 5.3 |

---

## 📋 Pré-requisitos

- Python 3.10 ou superior
- MySQL 8 ou superior
- pip

> **Windows:** o `flask-mysqldb` depende do `mysqlclient`, que precisa de
> compilador C. Guarde o erro caso apareça — a solução mais simples é usar
> os _wheels_ prontos (`pip install mysqlclient`) ou instalar o
> _Microsoft C++ Build Tools_.

---

## ⚙️ Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/HMartins-tech/fincontrol.git
cd fincontrol
```

### 2. Crie e ative o ambiente virtual

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install flask flask-mysqldb
```

### 4. Configure o banco de dados

Crie o banco executando o script SQL:

```bash
mysql -u root -p < banco_de_dados.sql
```

Ou abra o MySQL Workbench e execute o conteúdo do arquivo `banco_de_dados.sql`.

### 5. Configure as credenciais

Copie o arquivo de exemplo e preencha com os seus dados:

```bash
cp config.exemplo.py config.py
```

Edite `config.py`:

```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'sua_senha'
MYSQL_DB = 'fincontrol'
SECRET_KEY = 'uma-chave-secreta-aleatoria'
```

> ⚠️ O `config.py` está no `.gitignore` porque contém credenciais.

### 6. Execute a aplicação

```bash
python app.py
```

Acesse em: **http://127.0.0.1:5000**

---

## 📁 Estrutura do projeto

```
fincontrol/
│
├── app.py                  # Rotas e lógica da aplicação
├── config.exemplo.py       # Modelo de configuração
├── banco_de_dados.sql      # Script de criação do banco
├── .gitignore
├── README.md
│
├── static/
│   └── css/
│       └── style.css       # Estilos personalizados
│
└── templates/              # Páginas HTML (Jinja2)
    ├── base.html           # Layout base (herança)
    ├── navbar.html         # Menu de navegação
    ├── index.html
    ├── login.html
    ├── cadastro.html
    ├── dashboard.html
    ├── usuarios.html
    ├── editar_usuario.html
    ├── receitas.html
    ├── listar_receitas.html
    ├── editar_receita.html
    ├── despesas.html
    ├── listar_despesas.html
    └── editar_despesa.html
```

---

## 🗄️ Modelo de dados

Três tabelas compõem o banco `fincontrol`:

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   usuario    │ 1     N │  transacao   │ N     1 │  categoria   │
│──────────────│─────────│──────────────│─────────│──────────────│
│ id_usuario PK│         │id_transacao  │         │id_categoria  │
│ nome         │         │descricao     │         │nome_categoria│
│ email UNIQUE │         │valor DECIMAL │         │tipo ENUM     │
│ senha (hash) │         │data_transacao│         └──────────────┘
└──────────────┘         │tipo ENUM     │
                         │id_usuario FK │
                         │id_categoria  │
                         └──────────────┘
```

---

## 🔐 Segurança

| Ameaça                      | Mitigação                                               |
| --------------------------- | ------------------------------------------------------- |
| SQL Injection               | Queries parametrizadas (`%s` + tupla) em 100% do código |
| Senhas em texto puro        | Hash `scrypt` via Werkzeug, com salt automático         |
| Acesso não autorizado       | Sessão + decorator `@login_obrigatorio`                 |
| Forjar ID de usuário        | `id_usuario` sempre lido da sessão, nunca do formulário |
| E-mail duplicado            | Restrição `UNIQUE` no banco + tratamento de exceção     |
| Acesso a dados de terceiros | `WHERE id_usuario = %s` em toda query de escrita        |
| XSS                         | Autoescape do Jinja2 em `{{ }}`                         |

---

## 📡 Rotas

| Método   | Rota                    | Descrição                        | Protegida |
| -------- | ----------------------- | -------------------------------- | --------- |
| GET      | `/`                     | Página inicial + status do banco | ❌        |
| GET/POST | `/login`                | Autenticação                     | ❌        |
| GET      | `/logout`               | Encerra a sessão                 | ❌        |
| GET/POST | `/cadastro`             | Cadastro de usuário              | ❌        |
| GET      | `/dashboard`            | Totais e saldo                   | ✅        |
| GET      | `/usuarios`             | Lista de usuários                | ✅        |
| GET/POST | `/editar_usuario/<id>`  | Edição de usuário                | ✅        |
| GET      | `/excluir_usuario/<id>` | Exclusão de usuário              | ✅        |
| GET/POST | `/receitas`             | Cadastro de receita              | ✅        |
| GET      | `/listar_receitas`      | Lista de receitas                | ✅        |
| GET/POST | `/editar_receita/<id>`  | Edição de receita                | ✅        |
| GET      | `/excluir_receita/<id>` | Exclusão de receita              | ✅        |
| GET/POST | `/despesas`             | Cadastro de despesa              | ✅        |
| GET      | `/listar_despesas`      | Lista de despesas                | ✅        |
| GET/POST | `/editar_despesa/<id>`  | Edição de despesa                | ✅        |
| GET      | `/excluir_despesa/<id>` | Exclusão de despesa              | ✅        |

---

## 👤 Autor

**Luiz Henrique Martins Santos**
RGM: 46304568

Projeto Integrador Transdisciplinar — PIT II
