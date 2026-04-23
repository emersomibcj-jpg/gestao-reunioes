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

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    tipo = session.get("usuario_tipo")

    # 🔥 AQUI está a mudança que você queria
    if tipo == "admin":
        reunioes = conn.execute("SELECT * FROM reunioes").fetchall()
        usuarios = conn.execute("SELECT DISTINCT usuario FROM reunioes").fetchall()
    else:
        usuario = session.get("usuario_login")
        reunioes = conn.execute("SELECT * FROM reunioes WHERE usuario=?", (usuario,)).fetchall()
        usuarios = []

    conn.close()

    return render_template("painel.html", reunioes=reunioes, usuarios=usuarios)

@app.route("/filtrar/<usuario>")
def filtrar(usuario):
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    reunioes = conn.execute("SELECT * FROM reunioes WHERE usuario=?", (usuario,)).fetchall()
    conn.close()

    return render_template("painel.html", reunioes=reunioes, usuarios=[])

@app.route("/salvar", methods=["POST"])
def salvar():
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")

    nome = request.form["nome"]
    tema = request.form["tema"]
    data = request.form["data"]

    conn = get_db()
    conn.execute("""
        INSERT INTO reunioes (usuario, nome, tema, data_reuniao)
        VALUES (?, ?, ?, ?)
    """, (usuario, nome, tema, data))
    conn.commit()
    conn.close()

    return redirect(url_for("painel"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
