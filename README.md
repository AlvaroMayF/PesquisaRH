# PesquisaRH

Este projeto implementa um sistema de Pesquisa de Clima Organizacional para colaboradores, permitindo:

* **Login de colaboradores** (CPF + data de nascimento)
* **Formulário de pesquisa** com perguntas e opções configuráveis no banco de dados
* **Painel analítico** com gráficos de resposta (pizza)
* **Login e dashboard de administrador** para gerenciamento

---

## Tecnologias

* Linguagem: Python 3.x
* Framework web: Flask
* Banco de dados: MySQL
* Migrations: não inclusas (configuração manual)
* Bibliotecas principais:

  * `flask`
  * `mysql-connector-python`
  * `python-dotenv`
  * `pandas`
  * `matplotlib`

---

## Pré-requisitos

1. **Python 3.8+** instalado
2. **MySQL** configurado e em execução
3. Criar um ambiente virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

4. Instalar dependências

```bash
pip install flask mysql-connector-python python-dotenv pandas matplotlib
```

5. Configurar variáveis de ambiente

* Copie o arquivo `.env` em `app/.env` e ajuste se necessário:

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=senha_do_banco
DB_NAME=pesquisa_rh
FLASK_SECRET_KEY=uma_chave_secreta
```

---

## Estrutura de Pastas

```
PesquisaRH/
├── app/               # Código-fonte da aplicação Flask
│   ├── .env           # Variáveis de ambiente
│   ├── app.py         # Criação e configuração do Flask
│   ├── assets/        # Imagens (logo, favicon, background)
│   └── src/           # Código-organização em pacotes
│       ├── config/    # Configuração do DB (db.py)
│       ├── controllers/ # Controladores antigos (deprecated)
│       ├── model/     # Modelos vazios (inicialização)
│       ├── routers/   # Blueprints com rotas REST e views
│       └── views/     # Templates estáticos (HTML, CSS)
├── data/              # Dados brutos (Excel de colaboradores)
│   └── colaboradores_samar.xlsx
├── scripts/           # Scripts auxiliares (importação de dados)
│   └── load_colaboradores.py
└── .gitignore
```

---

## Configuração do Banco de Dados

Crie o banco e as tabelas necessárias executando as seguintes instruções SQL:

```sql
CREATE DATABASE IF NOT EXISTS pesquisa_rh;
USE pesquisa_rh;

CREATE TABLE colaboradores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(255) NOT NULL,
  cpf VARCHAR(14) NOT NULL UNIQUE,
  data_nascimento DATE NOT NULL,
  respondeu BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE surveys (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

CREATE TABLE form_questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  survey_id INT NOT NULL,
  section_title VARCHAR(255),
  question_text TEXT NOT NULL,
  question_type VARCHAR(50) NOT NULL,
  order_index INT DEFAULT 0,
  FOREIGN KEY (survey_id) REFERENCES surveys(id)
);

CREATE TABLE form_options (
  id INT AUTO_INCREMENT PRIMARY KEY,
  question_id INT NOT NULL,
  option_label VARCHAR(255) NOT NULL,
  option_value VARCHAR(255) NOT NULL,
  FOREIGN KEY (question_id) REFERENCES form_questions(id)
);

CREATE TABLE responses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  survey_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (survey_id) REFERENCES surveys(id)
);

CREATE TABLE response_answers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  response_id INT NOT NULL,
  question_id INT NOT NULL,
  answer TEXT,
  FOREIGN KEY (response_id) REFERENCES responses(id),
  FOREIGN KEY (question_id) REFERENCES form_questions(id)
);
```

Após criar o schema, insira a pesquisa padrão:

```sql
INSERT INTO surveys (name) VALUES ('Pesquisa de Clima Organizacional');
```

Em seguida, cadastre suas perguntas e opções em `form_questions` e `form_options`.

---

## Importando Colaboradores

Para carregar os colaboradores da planilha, execute:

```bash
python scripts/load_colaboradores.py
```

---

## Executando a Aplicação

No diretório `app/`, inicie o servidor Flask:

```bash
python app.py
```

A aplicação ficará disponível em `http://localhost:10000`.

* **/admin-login**: Login de administrador
* **/admin**: Dashboard do administrador
* **/**: Login de colaborador (página inicial)
* **/pesquisa**: Formulário de pesquisa
* **/analitico**: Visão analítica dos resultados

---

## Boas Práticas e Contribuição

* Use um ambiente virtual
* Não comite arquivos sensíveis (ex: `.env`)
* Abra issues para bugs ou novas funcionalidades
* Faça pull requests com descrições claras

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
