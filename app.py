from flask import Flask, render_template_string, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

DB_NAME = "reunioes.db"

USUARIOS = {
    "emerson": {"senha": "1234", "nome": "Emerson", "tipo": "admin"},
    "davi": {"senha": "1234", "nome": "Davi", "tipo": "usuario"}
}

STATUS_LISTA = ["Planejada", "Em andamento", "Concluída"]


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS reunioes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        nome TEXT,
        tema TEXT,
        data_reuniao TEXT,
        horario TEXT,
        participantes TEXT,
        status TEXT,
        pautas TEXT,
        observacoes TEXT
    )
    """)
    conn.commit()
    conn.close()


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["usuario"]
        senha = request.form["senha"]

        if user in USUARIOS and USUARIOS[user]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = user
            session["nome"] = USUARIOS[user]["nome"]
            session["tipo"] = USUARIOS[user]["tipo"]
            return redirect("/painel")

        flash("Login inválido")

    return render_template_string("""
    <style>
        body {
            background: #0f172a;
            color: white;
            font-family: Arial;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
        }
        form {
            background:#1e293b;
            padding:20px;
            border-radius:10px;
        }
        input {
            width:100%;
            margin:10px 0;
            padding:8px;
            border:none;
            border-radius:5px;
        }
        button {
            background:#38bdf8;
            border:none;
            padding:10px;
            width:100%;
        }
    </style>

    <form method="POST">
        <h2>Login</h2>
        <input name="usuario" placeholder="Usuário">
        <input name="senha" type="password" placeholder="Senha">
        <button>Entrar</button>

        {% for m in get_flashed_messages() %}
            <p style="color:red;">{{m}}</p>
        {% endfor %}
    </form>
    """)


# ================= PAINEL =================
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    conn = get_db()

    if session["tipo"] == "admin":
        reunioes = conn.execute("SELECT * FROM reunioes").fetchall()
    else:
        reunioes = conn.execute(
            "SELECT * FROM reunioes WHERE usuario=?",
            (session["usuario"],)
        ).fetchall()

    conn.close()

    return render_template_string("""
    <style>
        body {
            font-family: Arial;
            background: #0f172a;
            color: white;
            padding: 20px;
        }
        h2 { color: #38bdf8; }

        input, textarea, select {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border-radius: 5px;
            border: none;
        }

        button {
            background: #38bdf8;
            border: none;
            padding: 10px;
            color: black;
            border-radius: 5px;
        }

        table {
            width: 100%;
            margin-top: 20px;
            border-collapse: collapse;
        }

        th, td {
            border: 1px solid #334155;
            padding: 8px;
        }

        th { background: #1e293b; }
        tr:hover { background: #1e293b; }

        a { color: #38bdf8; }
    </style>

    <h2>Bem-vindo, {{session.nome}}</h2>
    <a href="/logout">Sair</a>

    <h3>Nova Reunião</h3>

    <form method="POST" action="/salvar">
        Nome:<input name="nome">
        Tema:<input name="tema">
        Data:<input name="data">
        Horário:<input name="horario">
        Participantes:<input name="participantes">

        Status:
        <select name="status">
            {% for s in status %}
                <option>{{s}}</option>
            {% endfor %}
        </select>

        Pautas:<textarea name="pautas"></textarea>
        Observações:<textarea name="observacoes"></textarea>

        <button>Salvar</button>
    </form>

    <h3>Reuniões</h3>

    <table>
    <tr>
        <th>ID</th>
        <th>Nome</th>
        <th>Tema</th>
        <th>Data</th>
        <th>Status</th>
        <th>Ações</th>
    </tr>

    {% for r in reunioes %}
    <tr>
        <td>{{r.id}}</td>
        <td>{{r.nome}}</td>
        <td>{{r.tema}}</td>
        <td>{{r.data_reuniao}}</td>
        <td>{{r.status}}</td>
        <td>
            <a href="/detalhes/{{r.id}}">Ver</a>
            <form method="POST" action="/excluir/{{r.id}}" style="display:inline;">
                <button>Excluir</button>
            </form>
        </td>
    </tr>
    {% endfor %}
    </table>
    """, reunioes=reunioes, status=STATUS_LISTA)


# ================= SALVAR =================
@app.route("/salvar", methods=["POST"])
def salvar():
    conn = get_db()

    conn.execute("""
    INSERT INTO reunioes (usuario, nome, tema, data_reuniao, horario, participantes, status, pautas, observacoes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["usuario"],
        request.form["nome"],
        request.form["tema"],
        request.form["data"],
        request.form["horario"],
        request.form["participantes"],
        request.form["status"],
        request.form["pautas"],
        request.form["observacoes"]
    ))

    conn.commit()
    conn.close()

    return redirect("/painel")


# ================= EXCLUIR =================
@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = get_db()

    if session["tipo"] == "admin":
        conn.execute("DELETE FROM reunioes WHERE id=?", (id,))
    else:
        conn.execute(
            "DELETE FROM reunioes WHERE id=? AND usuario=?",
            (id, session["usuario"])
        )

    conn.commit()
    conn.close()

    return redirect("/painel")


# ================= DETALHES =================
@app.route("/detalhes/<int:id>")
def detalhes(id):
    conn = get_db()

    if session["tipo"] == "admin":
        reuniao = conn.execute("SELECT * FROM reunioes WHERE id=?", (id,)).fetchone()
    else:
        reuniao = conn.execute(
            "SELECT * FROM reunioes WHERE id=? AND usuario=?",
            (id, session["usuario"])
        ).fetchone()

    conn.close()

    return render_template_string("""
    <body style="background:#0f172a;color:white;font-family:Arial;padding:20px;">
    <h2>Detalhes</h2>

    <p><b>Nome:</b> {{r.nome}}</p>
    <p><b>Tema:</b> {{r.tema}}</p>
    <p><b>Data:</b> {{r.data_reuniao}}</p>
    <p><b>Status:</b> {{r.status}}</p>
    <p><b>Participantes:</b> {{r.participantes}}</p>

    <a href="/painel" style="color:#38bdf8;">Voltar</a>
    </body>
    """, r=reuniao)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    criar_tabelas()
    app.run(host="0.0.0.0", port=10000)
