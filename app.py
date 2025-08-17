from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = "segredo_seguro"

# Caminho do banco e das imagens
DATABASE = 'database.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Garantir que a pasta de upload exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Funções auxiliares
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS






@app.route("/")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", usuario=session["usuario"])


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db()
        user = conn.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email, senha)).fetchone()
        conn.close()
        
        if user:
            if user["aprovado"] != 1:
                flash("Aguardando aprovação do administrador.")
                return redirect(url_for("login"))
            
            session["usuario"] = user["nome"]
            session["tipo"] = user["tipo"]  # 👈 ESSA LINHA É FUNDAMENTAL
            return redirect(url_for("index"))
        
        else:
            flash("Login inválido")
    return render_template("login.html")

# Cadastro de usuário
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']
        try:
            conn = get_db()
            conn.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                         (nome, email, senha, tipo))
            conn.commit()
            conn.close()
            flash("Usuário cadastrado com sucesso!")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("E-mail já cadastrado.")
    return render_template("cadastro.html")

# Logout
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    session.pop("tipo", None)  # 👈 IMPORTANTE LIMPAR TAMBÉM
    return redirect(url_for("login"))


# Cadastro de projetos
@app.route("/cadastrar_projeto", methods=["GET", "POST"])
def cadastrar_projeto():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        titulo = request.form["titulo"]
        descricao = request.form["descricao"]
        responsavel = request.form["responsavel"]

        imagem_antes = request.files["imagem_antes"]
        imagem_depois = request.files["imagem_depois"]

        nome_arquivo_antes = ""
        nome_arquivo_depois = ""

        if imagem_antes and allowed_file(imagem_antes.filename):
            nome_arquivo_antes = secure_filename(imagem_antes.filename)
            imagem_antes.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo_antes))

        if imagem_depois and allowed_file(imagem_depois.filename):
            nome_arquivo_depois = secure_filename(imagem_depois.filename)
            imagem_depois.save(os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo_depois))

        hoje = datetime.date.today()
        mes_nome = hoje.strftime("%B").capitalize()
        ano = hoje.year

        conn = get_db()

        mes = conn.execute("SELECT * FROM meses WHERE mes=? AND ano=?", (mes_nome, ano)).fetchone()
        if not mes:
            conn.execute("INSERT INTO meses (mes, ano) VALUES (?, ?)", (mes_nome, ano))
            conn.commit()
            mes = conn.execute("SELECT * FROM meses WHERE mes=? AND ano=?", (mes_nome, ano)).fetchone()

        conn.execute("""
            INSERT INTO projetos (titulo, descricao, imagem_antes, imagem_depois, responsavel, mes_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (titulo, descricao, nome_arquivo_antes, nome_arquivo_depois, responsavel, mes["id"]))
        conn.commit()
        conn.close()
        return "✅ Projeto cadastrado com sucesso!"

    return render_template("cadastrar_projeto.html")

@app.route("/vencedor", methods=["GET"])
def vencedor():
    if "usuario" not in session:
        return redirect(url_for("login"))

    # Mapeamento de português para inglês
    meses_pt_en = {
        "Janeiro": "January", "Fevereiro": "February", "Março": "March", "Abril": "April",
        "Maio": "May", "Junho": "June", "Julho": "July", "Agosto": "August",
        "Setembro": "September", "Outubro": "October", "Novembro": "November", "Dezembro": "December"
    }

    # Obter mês e ano da query string ou usar mês/ano atual como padrão
    mes_pt = request.args.get("mes")
    ano = request.args.get("ano", type=int)

    hoje = datetime.date.today()
    if not mes_pt:
        mes_en = hoje.strftime("%B").capitalize()
        mes_pt = hoje.strftime("%B").capitalize()  # exibe corretamente na tela
    else:
        mes_en = meses_pt_en.get(mes_pt)

    if not ano:
        ano = hoje.year

    conn = get_db()

    mes = conn.execute("SELECT * FROM meses WHERE mes=? AND ano=?", (mes_en, ano)).fetchone()
    if not mes:
        conn.close()
        return render_template("vencedor.html", projetos=None, mes=mes_pt, ano=ano)

    projetos_ordenados = conn.execute("""
        SELECT projetos.*, COUNT(votos.id) AS total_votos
        FROM projetos
        LEFT JOIN votos ON projetos.id = votos.projeto_id
        WHERE projetos.mes_id = ?
        GROUP BY projetos.id
        ORDER BY total_votos DESC
    """, (mes["id"],)).fetchall()

    conn.close()
    return render_template("vencedor.html", projetos=projetos_ordenados, mes=mes_pt, ano=ano)


@app.route("/votar", methods=["GET", "POST"])
def votar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    # Identificar usuário atual
    nome_usuario = session["usuario"]
    usuario = conn.execute("SELECT * FROM usuarios WHERE nome=?", (nome_usuario,)).fetchone()
    if not usuario:
        flash("Usuário não encontrado.")
        return redirect(url_for("index"))

    hoje = datetime.date.today()
    mes_nome = hoje.strftime("%B").capitalize()
    ano = hoje.year

    # Verificar ou criar mês
    mes = conn.execute("SELECT * FROM meses WHERE mes=? AND ano=?", (mes_nome, ano)).fetchone()
    if not mes:
        conn.execute("INSERT INTO meses (mes, ano) VALUES (?, ?)", (mes_nome, ano))
        conn.commit()
        mes = conn.execute("SELECT * FROM meses WHERE mes=? AND ano=?", (mes_nome, ano)).fetchone()

    # Verificar se já votou esse mês
    voto_existente = conn.execute("""
        SELECT * FROM votos WHERE usuario_id=? AND mes_id=?
    """, (usuario["id"], mes["id"])).fetchone()

    # Se estiver votando agora (POST)
    if request.method == "POST":
        projeto_id = request.form["projeto_id"]
        if voto_existente:
            # Atualiza o voto
            conn.execute("""
                UPDATE votos SET projeto_id=? WHERE id=?
            """, (projeto_id, voto_existente["id"]))
            flash("🔁 Voto atualizado com sucesso!")
        else:
            # Novo voto
            conn.execute("""
                INSERT INTO votos (usuario_id, projeto_id, mes_id)
                VALUES (?, ?, ?)
            """, (usuario["id"], projeto_id, mes["id"]))
            flash("✅ Voto registrado com sucesso!")

        conn.commit()
        conn.close()
        return redirect(url_for("votar"))

    # Exibir projetos do mês atual
    projetos = conn.execute("""
        SELECT * FROM projetos WHERE mes_id = ?
    """, (mes["id"],)).fetchall()

    conn.close()
    return render_template("votar.html", projetos=projetos, voto_existente=voto_existente)

@app.route("/usuarios", methods=["GET", "POST"])
def gerenciar_usuarios():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute("SELECT * FROM usuarios WHERE nome=?", (session["usuario"],)).fetchone()

    if user["tipo"] != "administrador":
        conn.close()
        return "⛔ Acesso restrito ao administrador."

    if request.method == "POST":
        usuario_id = request.form["usuario_id"]
        acao = request.form["acao"]

        if acao == "aprovar":
            conn.execute("UPDATE usuarios SET aprovado = 1 WHERE id = ?", (usuario_id,))
        elif acao == "recusar":
            conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        elif acao == "excluir":
            usuario_excluir = conn.execute("SELECT nome FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
            if usuario_excluir and usuario_excluir["nome"] == session["usuario"]:
                flash("Você não pode excluir a si mesmo.")
            else:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
                flash("Usuário excluído com sucesso.")

        conn.commit()

    usuarios = conn.execute("SELECT * FROM usuarios ORDER BY aprovado ASC, nome ASC").fetchall()
    conn.close()
    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/gerenciar_projetos", methods=["GET", "POST"])
#@verifica_login
#@verifica_admin
def gerenciar_projetos():
    mes = request.args.get("mes")
    ano = request.args.get("ano", datetime.datetime.now().year)

    MESES_PT_EN = {
        "Janeiro": "January",
        "Fevereiro": "February",
        "Março": "March",
        "Abril": "April",
        "Maio": "May",
        "Junho": "June",
        "Julho": "July",
        "Agosto": "August",
        "Setembro": "September",
        "Outubro": "October",
        "Novembro": "November",
        "Dezembro": "December"
    }


    def buscar_projetos_por_mes_ano(mes, ano):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT projetos.*, meses.mes, meses.ano
            FROM projetos
            JOIN meses ON projetos.mes_id = meses.id
            WHERE meses.mes = ? AND meses.ano = ?
        ''', (mes, ano))
        return cursor.fetchall()



    


    projetos = []
    if mes:
        mes_em_portugues = request.args.get('mes')
        ano = request.args.get('ano', type=int)
        mes_em_ingles = MESES_PT_EN.get(mes_em_portugues)
        projetos = buscar_projetos_por_mes_ano(mes_em_ingles, ano)  # sua função já existente

    return render_template("gerenciar_projetos.html", projetos=projetos, mes=mes, ano=ano)


@app.route("/excluir_projeto/<int:projeto_id>", methods=["POST"])
#@verifica_login
#@verifica_admin
def excluir_projeto(projeto_id):
    
    def excluir_projeto_do_banco(projeto_id):
        import sqlite3
        conn = sqlite3.connect('database.db')  # ajuste o nome se for diferente
        cur = conn.cursor()
        cur.execute("DELETE FROM projetos WHERE id = ?", (projeto_id,))
        conn.commit()
        conn.close()
    
    excluir_projeto_do_banco(projeto_id)  # você implementa esta função
    flash("Projeto excluído com sucesso!")
    return redirect(request.referrer or url_for('gerenciar_projetos'))

# Rodar o servidor
if __name__ == "__main__":
    #app.run(debug=True)
    app.run()
    
