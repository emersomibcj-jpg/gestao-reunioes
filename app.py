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
            tema TEXT,
            data_reuniao TEXT,
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

        flash("Login inválido", "erro")

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
        status_lista=STATUS_LISTA,
        usuarios=USUARIOS,
        busca="",
        campo="Todos",
        data_ini="",
        data_fim="",
        registro_edicao=None
    )


@app.route("/usuario/<usuario>")
def ver_usuario(usuario):
    if not session.get("logado"):
        return redirect(url_for("login"))

    if session.get("usuario_tipo") != "admin":
        return redirect(url_for("painel"))

    reunioes = buscar_reunioes(filtro_usuario=usuario)
    indicadores = contar_status()

    return render_template(
        "painel.html",
        reunioes=reunioes,
        indicadores=indicadores,
        status_lista=STATUS_LISTA,
        usuarios=USUARIOS,
        busca="",
        campo="Todos",
        data_ini="",
        data_fim="",
        registro_edicao=None
    )


@app.route("/salvar", methods=["POST"])
def salvar():
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")

    # 🔥 CORREÇÃO PRINCIPAL (sem erro 400)
    nome = request.form.get("nome")
    tema = request.form.get("tema", "")
    data = request.form.get("data", "")
    horario = request.form.get("horario", "")
    participantes = request.form.get("participantes", "")
    status = request.form.get("status", "Planejada")
    pautas = request.form.get("pautas", "")
    observacoes = request.form.get("observacoes", "")

    if not nome:
        flash("Nome da reunião é obrigatório", "erro")
        return redirect(url_for("painel"))

    conn = get_db()
    conn.execute("""
        INSERT INTO reunioes
        (usuario, nome, tema, data_reuniao, horario, participantes, status, pautas, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        usuario, nome, tema, data, horario,
        participantes, status, pautas, observacoes
    ))

    conn.commit()
    conn.close()

    flash("Reunião salva com sucesso!", "sucesso")
    return redirect(url_for("painel"))


@app.route("/excluir/<int:reuniao_id>", methods=["POST"])
def excluir(reuniao_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM reunioes WHERE id=?", (reuniao_id,))
    conn.commit()
    conn.close()

    flash("Reunião excluída!", "sucesso")
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
