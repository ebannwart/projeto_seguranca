import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Liste os usuários
usuarios = cursor.execute("SELECT id, nome, email, tipo, aprovado FROM usuarios").fetchall()
print("\nUsuários existentes:")
for u in usuarios:
    print(f"ID: {u[0]} | Nome: {u[1]} | Email: {u[2]} | Tipo: {u[3]} | Aprovado: {u[4]}")

# Aprove o primeiro admin (ou qualquer ID que desejar)
id_para_aprovar = int(input("\nDigite o ID do usuário que deseja aprovar manualmente: "))
cursor.execute("UPDATE usuarios SET aprovado = 1 WHERE id = ?", (id_para_aprovar,))

conn.commit()
conn.close()
print("✅ Usuário aprovado com sucesso!")