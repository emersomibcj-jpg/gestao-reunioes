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


criar_tabelas()


def buscar_reunioes(filtro_usuario=None):
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    consulta = "SELECT * FROM reunioes WHERE 1=1"
    params = []

    # 🔥 FILTRO POR USUÁRIO (ADMIN)
    if tipo == "admin" and filtro_usuario:
        consulta += " AND usuario=?"
        params.append(filtro_usuario)

    elif tipo != "admin":
        consulta += " AND usuario=?"
        params.append(usuario)

    consulta += " ORDER BY id DESC"

    conn = get_db()
    rows = conn.execute(consulta, params).fetchall()
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
    return render_template("painel.html", reunioes=reunioes, status_lista=STATUS_LISTA)


# 🔥🔥🔥 ESSA É A PARTE QUE FALTAVA (A CAUSA DO ERRO)
@app.route("/usuario/<usuario>")
def ver_usuario(usuario):
    if not session.get("logado"):
        return redirect(url_for("login"))

    if session.get("usuario_tipo") != "admin":
        return redirect(url_for("painel"))

    reunioes = buscar_reunioes(filtro_usuario=usuario)

    return render_template("painel.html", reunioes=reunioes, status_lista=STATUS_LISTA)


@app.route("/salvar", methods=["POST"])
def salvar():
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")

    conn = get_db()
    conn.execute("""
        INSERT INTO reunioes (usuario, nome, tema, data_reuniao, horario, participantes, status, pautas, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        usuario,
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

    return redirect(url_for("painel"))


@app.route("/excluir/<int:reuniao_id>", methods=["POST"])
def excluir(reuniao_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM reunioes WHERE id=?", (reuniao_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("painel"))


@app.route("/detalhes/<int:reuniao_id>")
def detalhes(reuniao_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    reuniao = conn.execute("SELECT * FROM reunioes WHERE id=?", (reuniao_id,)).fetchone()
    conn.close()

    return render_template("detalhes.html", reuniao=reuniao)


if __name__ == "__main__":
    app.run(debug=True)
