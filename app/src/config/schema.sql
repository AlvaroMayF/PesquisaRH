-- Remove as tabelas se elas já existirem, para garantir um início limpo.
DROP TABLE IF EXISTS response_answers;
DROP TABLE IF EXISTS form_options;
DROP TABLE IF EXISTS colaborador_survey_status;
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS form_questions;
DROP TABLE IF EXISTS surveys;
DROP TABLE IF EXISTS comunicados;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS feriados;
DROP TABLE IF EXISTS colaboradores;
DROP TABLE IF EXISTS unidades;

-- Habilita o suporte a chaves estrangeiras no SQLite
PRAGMA foreign_keys = ON;


CREATE TABLE unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
);

CREATE TABLE colaboradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    respondeu INTEGER NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1,
    setor TEXT,
    cargo TEXT,
    unidade TEXT
);

CREATE TABLE feriados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    descricao TEXT NOT NULL,
    unidade TEXT NOT NULL
);

CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins (id) ON DELETE CASCADE
);

CREATE TABLE comunicados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    data_publicacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    admin_id INTEGER NOT NULL,
    imagem_url TEXT,
    categoria TEXT DEFAULT 'Aviso Interno',
    FOREIGN KEY (admin_id) REFERENCES admins (id)
);

CREATE TABLE surveys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 0,
    start_date TEXT,
    end_date TEXT
);

CREATE TABLE form_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER NOT NULL,
    order_index INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    section_title TEXT,
    question_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys (id) ON DELETE RESTRICT
);

CREATE TABLE responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER NOT NULL,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    colaborador_setor TEXT,
    colaborador_cargo TEXT,
    colaborador_unidade TEXT,
    FOREIGN KEY (survey_id) REFERENCES surveys (id) ON DELETE RESTRICT
);

CREATE TABLE colaborador_survey_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colaborador_id INTEGER NOT NULL,
    survey_id INTEGER NOT NULL,
    status TEXT DEFAULT 'completed',
    completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id) ON DELETE CASCADE,
    FOREIGN KEY (survey_id) REFERENCES surveys (id) ON DELETE CASCADE,
    UNIQUE (colaborador_id, survey_id)
);

CREATE TABLE form_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_label TEXT NOT NULL,
    option_value TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES form_questions (id) ON DELETE CASCADE
);

CREATE TABLE response_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES form_questions (id) ON DELETE CASCADE,
    FOREIGN KEY (response_id) REFERENCES responses (id) ON DELETE CASCADE
);