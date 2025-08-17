import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Adiciona a coluna "aprovado" com valor padrão 0 (não aprovado)
cursor.execute("ALTER TABLE usuarios ADD COLUMN aprovado INTEGER DEFAULT 0")

conn.commit()
conn.close()
print("✅ Coluna 'aprovado' adicionada à tabela 'usuarios'")