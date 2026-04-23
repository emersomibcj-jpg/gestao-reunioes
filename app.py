from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

DB = "reunioes.db"

USUARIOS = {
    "emerson": {"senha": "1234", "tipo": "admin"},
    "davi": {"senha": "1234", "tipo": "usuario"},
}

# ---------------- BANCO ----------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reunioes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            nome TEXT,
            tema TEXT,
            data TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

# ---------------- LOGIN (TELA AZUL) ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    erro = ""

    if request.method == "POST":
        user = request.form["usuario"]
        senha = request.form["senha"]

        if user in USUARIOS and USUARIOS[user]["senha"] == senha:
            session["user"] = user
            session["tipo"] = USUARIOS[user]["tipo"]
            return redirect(url_for("painel"))
        else:
            erro = "Login inválido"

    return render_template_string("""
    <style>
    body {
        margin:0;
        font-family: Arial;
        background: url('https://images.unsplash.com/photo-1554224155-6726b3ff858f') no-repeat center;
        background-size: cover;
    }
    .box {
        width:300px;
        margin:100px auto;
        background:#1e5aa8;
        padding:30px;
        color:white;
        border-radius:10px;
    }
    input {
        width:100%;
        padding:10px;
        margin:10px 0;
    }
    button {
        width:100%;
        padding:10px;
        background:white;
        border:none;
        font-weight:bold;
    }
    </style>

    <div class="box">
        <h2>Work Meeting</h2>
        <p>Olá, seja bem vindos!</p>

        <form method="post">
            Login
            <input name="usuario">

            Senha
            <input type="password" name="senha">

            <button>Acessar</button>
        </form>

        <p style="color:yellow;">{{erro}}</p>
    </div>
    """, erro=erro)

# ---------------- PAINEL ----------------
@app.route("/painel")
def painel():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    filtro = request.args.get("usuario")

    if session["tipo"] == "admin":
        if filtro:
            reunioes = conn.execute("SELECT * FROM reunioes WHERE usuario=?", (filtro,)).fetchall()
        else:
            reunioes = conn.execute("SELECT * FROM reunioes").fetchall()

        usuarios = conn.execute("SELECT DISTINCT usuario FROM reunioes").fetchall()
    else:
        reunioes = conn.execute("SELECT * FROM reunioes WHERE usuario=?", (session["user"],)).fetchall()
        usuarios = []

    conn.close()

    return render_template_string("""
    <h2>Painel</h2>

    <a href="{{ url_for('logout') }}">Sair</a>

    {% if session['tipo'] == 'admin' %}
    <form method="get">
        <select name="usuario">
            <option value="">Todos</option>
            {% for u in usuarios %}
                <option value="{{u.usuario}}">{{u.usuario}}</option>
            {% endfor %}
        </select>
        <button>Filtrar</button>
    </form>
    {% endif %}

    <h3>Nova reunião</h3>
    <form method="post" action="{{ url_for('salvar') }}">
        Nome: <input name="nome"><br>
        Tema: <input name="tema"><br>
        Data: <input name="data"><br>
        Status: <input name="status"><br>
        <button>Salvar</button>
    </form>

    <h3>Reuniões</h3>
    <ul>
    {% for r in reunioes %}
        <li>
            {{r.nome}} - {{r.tema}} - {{r.usuario}}
            <form method="post" action="{{ url_for('excluir', id=r.id) }}">
                <button>Excluir</button>
            </form>
        </li>
    {% endfor %}
    </ul>
    """, reunioes=reunioes, usuarios=usuarios)

# ---------------- SALVAR ----------------
@app.route("/salvar", methods=["POST"])
def salvar():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("""
        INSERT INTO reunioes (usuario, nome, tema, data, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user"],
        request.form["nome"],
        request.form["tema"],
        request.form["data"],
        request.form["status"]
    ))
    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------------- EXCLUIR ----------------
@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = get_db()

    if session["tipo"] == "admin":
        conn.execute("DELETE FROM reunioes WHERE id=?", (id,))
    else:
        conn.execute("DELETE FROM reunioes WHERE id=? AND usuario=?", (id, session["user"]))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    criar_tabela()
    app.run(debug=True)
