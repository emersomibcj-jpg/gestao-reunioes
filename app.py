from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta_reunioes"

DB_NAME = "reunioes_v2.db"

USUARIOS = {
    "emerson": {"senha": "1234", "nome": "Emerson", "tipo": "admin"},
    "davi": {"senha": "1234", "nome": "Davi", "tipo": "usuario"},
    "matthews": {"senha": "1234", "nome": "Matthews", "tipo": "usuario"},
    "giovanne": {"senha": "1234", "nome": "Giovanne", "tipo": "usuario"},
    "rebecca": {"senha": "1234", "nome": "Rebecca", "tipo": "usuario"},
    "liliane": {"senha": "1234", "nome": "Liliane", "tipo": "usuario"},
    "maya": {"senha": "1234", "nome": "Maya", "tipo": "usuario"}
}

STATUS_LISTA = ["Planejada", "Em andamento", "Em pausa", "Concluída", "Adiada", "Cancelada"]


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reunioes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            nome TEXT NOT NULL,
            tema TEXT NOT NULL,
            data_reuniao TEXT NOT NULL,
            horario TEXT,
            participantes TEXT,
            status TEXT,
            pautas TEXT,
            observacoes TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# 🔥 resolve erro do Render (cria tabela automaticamente)
@app.before_request
def inicializar_db():
    criar_tabelas()


def buscar_reunioes():
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    conn = get_db()

    if tipo == "admin":
        rows = conn.execute("SELECT * FROM reunioes ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM reunioes WHERE usuario=? ORDER BY id DESC", (usuario,)).fetchall()

    conn.close()
    return rows


def contar_status():
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    conn = get_db()
    cur = conn.cursor()

    if tipo == "admin":
        total = cur.execute("SELECT COUNT(*) FROM reunioes").fetchone()[0]
    else:
        total = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=?", (usuario,)).fetchone()[0]

    conn.close()
    return {"total": total}


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("usuario", "").lower()
        senha = request.form.get("senha", "")

        if user in USUARIOS and USUARIOS[user]["senha"] == senha:
            session["logado"] = True
            session["usuario_login"] = user
            session["usuario_nome"] = USUARIOS[user]["nome"]
            session["usuario_tipo"] = USUARIOS[user]["tipo"]
            return redirect(url_for("painel"))

        flash("Login inválido")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect(url_for("login"))

    reunioes = buscar_reunioes()
    indicadores = contar_status()

    return render_template(
        "painel.html",
        reunioes=reunioes,
        indicadores=indicadores,
        status_lista=STATUS_LISTA
    )


# 🔥 SALVAR SEM ERRO (BLINDADO)
@app.route("/salvar", methods=["POST"])
def salvar():
    try:
        if not session.get("logado"):
            return redirect(url_for("login"))

        usuario = session.get("usuario_login")

        nome = request.form.get("nome", "")
        tema = request.form.get("tema", "")
        data = request.form.get("data", "")
        horario = request.form.get("horario", "")
        participantes = request.form.get("participantes", "")
        status = request.form.get("status", "")
        pautas = request.form.get("pautas", "")
        observacoes = request.form.get("observacoes", "")

        conn = get_db()
        conn.execute("""
            INSERT INTO reunioes 
            (usuario, nome, tema, data_reuniao, horario, participantes, status, pautas, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (usuario, nome, tema, data, horario, participantes, status, pautas, observacoes))

        conn.commit()
        conn.close()

        return redirect(url_for("painel"))

    except Exception as e:
        print("ERRO AO SALVAR:", e)
        return "Erro ao salvar reunião"


# 🔥 CORRIGE ERRO DO url_for (SEU HTML ANTIGO)
@app.route("/salvar_reuniao", methods=["POST"])
def salvar_reuniao():
    return salvar()


@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    conn = get_db()

    if tipo == "admin":
        conn.execute("DELETE FROM reunioes WHERE id=?", (id,))
    else:
        conn.execute("DELETE FROM reunioes WHERE id=? AND usuario=?", (id, usuario))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))
