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


criar_tabelas()


# 🔥 CORRIGIDO: ADMIN só vê se filtrar usuário
def buscar_reunioes(filtro_usuario=None):
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    consulta = "SELECT * FROM reunioes WHERE 1=1"
    params = []

    if tipo == "admin":
        if filtro_usuario:
            consulta += " AND usuario=?"
            params.append(filtro_usuario)
        else:
            consulta += " AND 1=0"  # 👈 não mostra nada
    else:
        consulta += " AND usuario=?"
        params.append(usuario)

    consulta += " ORDER BY id DESC"

    conn = get_db()
    rows = conn.execute(consulta, params).fetchall()
    conn.close()

    return rows


# 🔥 CORRIGIDO: contadores respeitam filtro
def contar_status(filtro_usuario=None):
    usuario = session.get("usuario_login")
    tipo = session.get("usuario_tipo")

    conn = get_db()
    cur = conn.cursor()

    if tipo == "admin":
        if filtro_usuario:
            total = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=?", (filtro_usuario,)).fetchone()[0]
            andamento = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=? AND lower(status)='em andamento'", (filtro_usuario,)).fetchone()[0]
            pausa = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=? AND lower(status)='em pausa'", (filtro_usuario,)).fetchone()[0]
            concluida = cur.execute("SELECT COUNT(*) FROM reunioes WHERE usuario=? AND lower(status) IN ('concluída','concluida')", (filtro_usuario,)).fetchone()[0]
        else:
            total = andamento = pausa = concluida = 0
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


# 🔥 AJUSTADO: aceita edição futuramente
@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect(url_for("login"))

    editar_id = request.args.get("editar_id")

    registro_edicao = None
    if editar_id:
        conn = get_db()
        registro_edicao = conn.execute("SELECT * FROM reunioes WHERE id=?", (editar_id,)).fetchone()
        conn.close()

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
        registro_edicao=registro_edicao
    )


@app.route("/usuario/<usuario>")
def ver_usuario(usuario):
    if not session.get("logado"):
        return redirect(url_for("login"))

    if session.get("usuario_tipo") != "admin":
        return redirect(url_for("painel"))

    reunioes = buscar_reunioes(filtro_usuario=usuario)
    indicadores = contar_status(filtro_usuario=usuario)

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


# 🔥 AGORA SUPORTA EDITAR E CRIAR
@app.route("/salvar", methods=["POST"])
def salvar():
    if not session.get("logado"):
        return redirect(url_for("login"))

    usuario = session.get("usuario_login")
    reuniao_id = request.form.get("reuniao_id")

    conn = get_db()

    if reuniao_id:
        # EDITAR
        conn.execute("""
            UPDATE reunioes
            SET nome=?, tema=?, data_reuniao=?, horario=?, participantes=?, status=?, pautas=?, observacoes=?
            WHERE id=?
        """, (
            request.form["nome"],
            request.form["tema"],
            request.form["data"],
            request.form["horario"],
            request.form["participantes"],
            request.form["status"],
            request.form["pautas"],
            request.form["observacoes"],
            reuniao_id
        ))
    else:
        # NOVO
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
