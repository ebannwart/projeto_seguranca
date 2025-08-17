import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    tipo TEXT NOT NULL  -- 'coordenador', 'gerente', etc.
)
""")

# Tabela de projetos
cursor.execute("""
CREATE TABLE IF NOT EXISTS projetos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    imagem_antes TEXT,
    imagem_depois TEXT,
    responsavel TEXT,
    mes_id INTEGER,
    FOREIGN KEY (mes_id) REFERENCES meses(id)
)
""")

# Tabela de meses
cursor.execute("""
CREATE TABLE IF NOT EXISTS meses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes TEXT NOT NULL,
    ano INTEGER NOT NULL
)
""")

# Tabela de votos
cursor.execute("""
CREATE TABLE IF NOT EXISTS votos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    projeto_id INTEGER,
    mes_id INTEGER,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (projeto_id) REFERENCES projetos(id),
    FOREIGN KEY (mes_id) REFERENCES meses(id)
)
""")

conn.commit()
conn.close()
print("✅ Banco de dados criado com sucesso!")