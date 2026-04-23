from flask import Flask, render_template_string, request, redirect, url_for, session, flash
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


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["usuario"]
        senha = request.form["senha"]

        if user in USUARIOS and USUARIOS[user]["senha"] == senha:
            session["logado"] = True
            session["usuario"] = user
            session["nome"] = USUARIOS[user]["nome"]
            return redirect("/painel")

        flash("Login inválido")

    return render_template_string("""
    <h2>Login</h2>
    <form method="POST">
        Usuário:<br><input name="usuario"><br><br>
        Senha:<br><input type="password" name="senha"><br><br>
        <button>Entrar</button>
    </form>
    {% for m in get_flashed_messages() %}
        <p style="color:red;">{{m}}</p>
    {% endfor %}
    """)


@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect("/")

    conn = get_db()
    reunioes = conn.execute("SELECT * FROM reunioes").fetchall()
    conn.close()

    return render_template_string("""
    <h2>Bem-vindo, {{session.nome}}</h2>
    <a href="/logout">Sair</a>

    <h3>Nova Reunião</h3>
    <form method="POST" action="/salvar">
        Nome:<br><input name="nome"><br>
        Tema:<br><input name="tema"><br>
        Data:<br><input name="data"><br>
        Horário:<br><input name="horario"><br>
        Participantes:<br><input name="participantes"><br>

        Status:<br>
        <select name="status">
            {% for s in status %}
                <option>{{s}}</option>
            {% endfor %}
        </select><br><br>

        Pautas:<br><textarea name="pautas"></textarea><br>
        Observações:<br><textarea name="observacoes"></textarea><br><br>

        <button>Salvar</button>
    </form>

    <hr>

    <h3>Reuniões</h3>

    <table border="1">
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


@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = get_db()
    conn.execute("DELETE FROM reunioes WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/painel")


@app.route("/detalhes/<int:id>")
def detalhes(id):
    conn = get_db()
    reuniao = conn.execute("SELECT * FROM reunioes WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template_string("""
    <h2>Detalhes</h2>
    <p><b>Nome:</b> {{r.nome}}</p>
    <p><b>Tema:</b> {{r.tema}}</p>
    <p><b>Data:</b> {{r.data_reuniao}}</p>
    <p><b>Status:</b> {{r.status}}</p>
    <p><b>Participantes:</b> {{r.participantes}}</p>

    <a href="/painel">Voltar</a>
    """, r=reuniao)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    criar_tabelas()
    app.run()
