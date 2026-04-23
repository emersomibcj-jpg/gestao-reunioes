from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

DB_NAME = "reunioes.db"

USUARIOS = {
    "emerson": {"senha": "1234", "nome": "Emerson", "tipo": "admin"},
    "davi": {"senha": "1234", "nome": "Davi", "tipo": "usuario"},
    "matthews": {"senha": "1234", "nome": "Matthews", "tipo": "usuario"},
}

STATUS_LISTA = ["Planejada", "Em andamento", "Concluída"]


def get_db():
    conn = sqlite3.connect(DB_NAME)
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


criar_tabela()


def buscar_reunioes(usuario_filtro=None):
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    query = "SELECT * FROM reunioes WHERE 1=1"
    params = []

    if tipo == "admin":
        if usuario_filtro:
            query += " AND usuario=?"
            params.append(usuario_filtro)
    else:
        query += " AND usuario=?"
        params.append(usuario)

    query += " ORDER BY id DESC"

    conn = get_db()
    dados = conn.execute(query, params).fetchall()
    conn.close()
    return dados


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["usuario"]
        senha = request.form["senha"]

        if user in USUARIOS and USUARIOS[user]["senha"] == senha:
            session["logado"] = True
            session["usuario_login"] = user
            session["usuario_tipo"] = USUARIOS[user]["tipo"]
            return redirect("/painel")

        flash("Login inválido")

    return """
    <h2>Login</h2>
    <form method="post">
        Usuário: <input name="usuario"><br>
        Senha: <input type="password" name="senha"><br>
        <button>Entrar</button>
    </form>
    """


@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    usuario_filtro = request.args.get("usuario")
    reunioes = buscar_reunioes(usuario_filtro)

    return render_template_string("""
    <h2>Painel</h2>

    {% if session["usuario_tipo"] == "admin" %}
    <form method="get">
        <select name="usuario" onchange="this.form.submit()">
            <option value="">Todos</option>
            {% for u in usuarios %}
            <option value="{{u}}" {% if u == usuario_filtro %}selected{% endif %}>{{u}}</option>
            {% endfor %}
        </select>
    </form>
    {% endif %}

    <h3>Nova reunião</h3>
    <form method="post" action="/salvar">
        Nome: <input name="nome"><br>
        Tema: <input name="tema"><br>
        Data: <input name="data"><br>
        Status: <input name="status"><br>
        <button>Salvar</button>
    </form>

    <h3>Reuniões</h3>
    <ul>
    {% for r in reunioes %}
        <li>{{r["nome"]}} - {{r["usuario"]}} - {{r["status"]}}</li>
    {% endfor %}
    </ul>

    <a href="/logout">Sair</a>
    """, reunioes=reunioes, usuarios=USUARIOS.keys(), usuario_filtro=usuario_filtro)


@app.route("/salvar", methods=["POST"])
def salvar():
    usuario = session.get("usuario_login")

    nome = request.form["nome"]
    tema = request.form["tema"]
    data = request.form["data"]
    status = request.form["status"]

    conn = get_db()
    conn.execute(
        "INSERT INTO reunioes (usuario, nome, tema, data, status) VALUES (?, ?, ?, ?, ?)",
        (usuario, nome, tema, data, status)
    )
    conn.commit()
    conn.close()

    return redirect("/painel")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
