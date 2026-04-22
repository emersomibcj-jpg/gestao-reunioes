from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_super_secreta_reunioes"

DB_NAME = "reunioes.db"

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


def validar_data(texto, obrigatoria=True):
    if not texto.strip():
        return not obrigatoria
    try:
        datetime.strptime(texto.strip(), "%d/%m/%Y")
        return True
    except ValueError:
        return False


def validar_horario(texto):
    if not texto.strip():
        return True
    try:
        datetime.strptime(texto.strip(), "%H:%M")
        return True
    except ValueError:
        return False


def reuniao_duplicada(nome, tema, data, horario, usuario, ignorar_id=None):
    conn = get_db()
    cur = conn.cursor()

    if ignorar_id:
        cur.execute("""
            SELECT id FROM reunioes
            WHERE nome=? AND tema=? AND data_reuniao=? 
            AND IFNULL(horario,'')=IFNULL(?, '')
            AND usuario=? AND id<>?
        """, (nome, tema, data, horario, usuario, ignorar_id))
    else:
        cur.execute("""
            SELECT id FROM reunioes
            WHERE nome=? AND tema=? AND data_reuniao=? 
            AND IFNULL(horario,'')=IFNULL(?, '')
            AND usuario=?
        """, (nome, tema, data, horario, usuario))

    row = cur.fetchone()
    conn.close()
    return row is not None


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


def buscar_reunioes(busca="", campo="Todos", data_ini="", data_fim=""):
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    consulta = "SELECT * FROM reunioes WHERE 1=1"
    params = []

    if tipo != "admin":
        consulta += " AND usuario=?"
        params.append(usuario)

    if busca:
        termo = f"%{busca}%"
        consulta += """
        AND (
            nome LIKE ? OR tema LIKE ? OR data_reuniao LIKE ? 
            OR participantes LIKE ? OR status LIKE ?
        )
        """
        params.extend([termo]*5)

    consulta += " ORDER BY id DESC"

    conn = get_db()
    rows = conn.execute(consulta, params).fetchall()
    conn.close()

    return rows


@app.context_processor
def inject_user():
    return dict(
        usuario_nome=session.get("usuario_nome"),
        usuario_tipo=session.get("usuario_tipo")
    )


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

    return render_template("painel.html", reunioes=reunioes, indicadores=indicadores, status_lista=STATUS_LISTA)


@app.route("/salvar", methods=["POST"])
def salvar():
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    reuniao_id = request.form.get("reuniao_id")
    nome = request.form["nome"]
    tema = request.form["tema"]
    data = request.form["data"]
    horario = request.form["horario"]
    participantes = request.form["participantes"]
    status = request.form["status"]
    pautas = request.form["pautas"]
    observacoes = request.form["observacoes"]

    conn = get_db()
    cur = conn.cursor()

    if reuniao_id:
        if tipo == "admin":
            cur.execute("""
                UPDATE reunioes SET nome=?, tema=?, data_reuniao=?, horario=?, participantes=?, status=?, pautas=?, observacoes=?
                WHERE id=?
            """, (nome, tema, data, horario, participantes, status, pautas, observacoes, reuniao_id))
        else:
            cur.execute("""
                UPDATE reunioes SET nome=?, tema=?, data_reuniao=?, horario=?, participantes=?, status=?, pautas=?, observacoes=?
                WHERE id=? AND usuario=?
            """, (nome, tema, data, horario, participantes, status, pautas, observacoes, reuniao_id, usuario))
    else:
        cur.execute("""
            INSERT INTO reunioes (usuario, nome, tema, data_reuniao, horario, participantes, status, pautas, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (usuario, nome, tema, data, horario, participantes, status, pautas, observacoes))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))


@app.route("/excluir/<int:reuniao_id>", methods=["POST"])
def excluir(reuniao_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    conn = get_db()

    if tipo == "admin":
        conn.execute("DELETE FROM reunioes WHERE id=?", (reuniao_id,))
    else:
        conn.execute("DELETE FROM reunioes WHERE id=? AND usuario=?", (reuniao_id, usuario))

    conn.commit()
    conn.close()

    return redirect(url_for("painel"))


@app.route("/detalhes/<int:reuniao_id>")
def detalhes(reuniao_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    conn = get_db()

    if tipo == "admin":
        reuniao = conn.execute("SELECT * FROM reunioes WHERE id=?", (reuniao_id,)).fetchone()
    else:
        reuniao = conn.execute("SELECT * FROM reunioes WHERE id=? AND usuario=?", (reuniao_id, usuario)).fetchone()

    conn.close()

    if not reuniao:
        flash("Acesso negado", "erro")
        return redirect(url_for("painel"))

    return render_template("detalhes.html", reuniao=reuniao)


if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
