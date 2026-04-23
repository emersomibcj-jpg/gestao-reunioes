from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

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


# 🚨 ESSA LINHA RESOLVE SEU ERRO NO RENDER
@app.before_request
def inicializar_db():
    criar_tabelas()


def contar_status():
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    conn = get_db()
    cur = conn.cursor()

    if tipo == "admin":
        total = cur.execute("SELECT COUNT(*) FROM reunioes").fetchone()[0]
        andamento = cur.execute("SELECT COUNT(*) FROM reunioes WHERE lower(status)='em andamento'").fetchone()[0]
        pausa = cur.execute("SELECT COUNT(*) FROM reunioes WHERE lower(status)='em pausa'").fetchone()[0]
        concluida = cur.execute("SELECT COUNT(*) FROM reunioes WHERE lower(status) IN ('concluída','concluida')").fetchone()[0]
    else:
        total = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=?", (usuario,)).fetchone()[0]
        andamento = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=? AND lower(status)='em andamento'", (usuario,)).fetchone()[0]
        pausa = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=? AND lower(status)='em pausa'", (usuario,)).fetchone()[0]
        concluida = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=? AND lower(status) IN ('concluída','concluida')", (usuario,)).fetchone()[0]

    conn.close()

    return {"total": total, "andamento": andamento, "pausa": pausa, "concluida": concluida}


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


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["usuario"].lower()
        senha = request.form["senha"]

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

    return render_template("painel.html",
                           reunioes=reunioes,
                           indicadores=indicadores,
                           status_lista=STATUS_LISTA)


@app.route("/salvar", methods=["POST"])
def salvar():
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")

    nome = request.form["nome"]
    tema = request.form["tema"]
    data = request.form["data"]
    horario = request.form["horario"]
    participantes = request.form["participantes"]
    status = request.form["status"]
    pautas = request.form["pautas"]
    observacoes = request.form["observacoes"]

    conn = get_db()
    conn.execute("""
        INSERT INTO reunioes (usuario, nome, tema, data_reuniao, horario, participantes, status, pautas, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (usuario, nome, tema, data, horario, participantes, status, pautas, observacoes))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))


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
