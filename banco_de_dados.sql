-- ============================================================
--  FinControl - Sistema de Controle Financeiro Pessoal
--  Projeto Fisico do Banco de Dados
--  Aluno: Luiz Henrique Martins Santos
--  RGM: 46304568
-- ============================================================

CREATE DATABASE IF NOT EXISTS fincontrol
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fincontrol;

-- ------------------------------------------------------------
--  Tabela: usuario
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuario (
    id_usuario  INT           NOT NULL AUTO_INCREMENT,
    nome        VARCHAR(100)  NOT NULL,
    email       VARCHAR(100)  NOT NULL,
    senha       VARCHAR(255)  NOT NULL,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uk_usuario_email (email)
) ENGINE = InnoDB;

-- ------------------------------------------------------------
--  Tabela: categoria
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categoria (
    id_categoria    INT         NOT NULL AUTO_INCREMENT,
    nome_categoria  VARCHAR(50) NOT NULL,
    tipo            ENUM('Receita','Despesa') NOT NULL,
    PRIMARY KEY (id_categoria)
) ENGINE = InnoDB;

-- ------------------------------------------------------------
--  Tabela: transacao
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transacao (
    id_transacao    INT            NOT NULL AUTO_INCREMENT,
    descricao       VARCHAR(200)   NOT NULL,
    valor           DECIMAL(10,2)  NOT NULL,
    data_transacao  DATE           NOT NULL,
    tipo            ENUM('Receita','Despesa') NOT NULL,
    id_usuario      INT            NOT NULL,
    id_categoria    INT            NOT NULL,
    PRIMARY KEY (id_transacao),
    KEY idx_transacao_usuario (id_usuario),
    KEY idx_transacao_categoria (id_categoria),
    CONSTRAINT fk_transacao_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_transacao_categoria
        FOREIGN KEY (id_categoria) REFERENCES categoria (id_categoria)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE = InnoDB;

-- ------------------------------------------------------------
--  Dados iniciais: categorias
-- ------------------------------------------------------------
INSERT INTO categoria (nome_categoria, tipo) VALUES
    ('Salario',       'Receita'),
    ('Freelance',     'Receita'),
    ('Investimentos', 'Receita'),
    ('Outros Ganhos', 'Receita'),
    ('Alimentacao',   'Despesa'),
    ('Transporte',    'Despesa'),
    ('Moradia',       'Despesa'),
    ('Saude',         'Despesa'),
    ('Educacao',      'Despesa'),
    ('Lazer',         'Despesa');
