from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_super_secreta_reunioes"

DB_NAME = "reunioes.db"
LOGIN_USUARIO = "emerson"
LOGIN_SENHA = "1234"
LOGIN_USUARIO = "davi"
LOGIN_SENHA = "1234"
LOGIN_USUARIO = "matthews"
LOGIN_SENHA = "1234"
LOGIN_USUARIO = "giovanne"
LOGIN_SENHA = "1234"
LOGIN_USUARIO = "rebecca"
LOGIN_SENHA = "1234"

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

def reuniao_duplicada(nome, tema, data, horario, ignorar_id=None):
    conn = get_db()
    cur = conn.cursor()
    if ignorar_id:
        cur.execute("""
            SELECT id FROM reunioes
            WHERE nome = ? AND tema = ? AND data_reuniao = ? AND IFNULL(horario,'') = IFNULL(?, '')
              AND id <> ?
        """, (nome, tema, data, horario, ignorar_id))
    else:
        cur.execute("""
            SELECT id FROM reunioes
            WHERE nome = ? AND tema = ? AND data_reuniao = ? AND IFNULL(horario,'') = IFNULL(?, '')
        """, (nome, tema, data, horario))
    row = cur.fetchone()
    conn.close()
    return row is not None

def contar_status():
    conn = get_db()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM reunioes").fetchone()[0]
    andamento = cur.execute("SELECT COUNT(*) FROM reunioes WHERE lower(status)='em andamento'").fetchone()[0]
    pausa = cur.execute("SELECT COUNT(*) FROM reunioes WHERE lower(status)='em pausa'").fetchone()[0]
    concluida = cur.execute("SELECT COUNT(*) FROM reunioes WHERE lower(status) IN ('concluída','concluida')").fetchone()[0]
    conn.close()
    return {
        "total": total,
        "andamento": andamento,
        "pausa": pausa,
        "concluida": concluida
    }

def buscar_reunioes(busca="", campo="Todos", data_ini="", data_fim=""):
    consulta = """
        SELECT id, nome, tema, data_reuniao, horario, status, participantes
        FROM reunioes
        WHERE 1=1
    """
    params = []

    if busca:
        mapa = {
            "Nome": "nome",
            "Tema": "tema",
            "Data": "data_reuniao",
            "Participantes": "participantes",
            "Status": "status"
        }
        if campo == "Todos":
            termo = f"%{busca}%"
            consulta += """
                AND (
                    nome LIKE ?
                    OR tema LIKE ?
                    OR data_reuniao LIKE ?
                    OR participantes LIKE ?
                    OR status LIKE ?
                    OR pautas LIKE ?
                    OR observacoes LIKE ?
                )
            """
            params.extend([termo] * 7)
        elif campo in mapa:
            consulta += f" AND {mapa[campo]} LIKE ?"
            params.append(f"%{busca}%")

    consulta += """
        ORDER BY substr(data_reuniao, 7, 4) DESC,
                 substr(data_reuniao, 4, 2) DESC,
                 substr(data_reuniao, 1, 2) DESC,
                 id DESC
    """

    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute(consulta, params).fetchall()
    conn.close()

    filtradas = []
    for row in rows:
        try:
            dt = datetime.strptime(row["data_reuniao"], "%d/%m/%Y")
            if data_ini:
                ini = datetime.strptime(data_ini, "%d/%m/%Y")
                if dt < ini:
                    continue
            if data_fim:
                fim = datetime.strptime(data_fim, "%d/%m/%Y")
                if dt > fim:
                    continue
        except Exception:
            pass
        filtradas.append(row)
    return filtradas

@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("logado"):
        return redirect(url_for("painel"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        if usuario == LOGIN_USUARIO and senha == LOGIN_SENHA:
            session["logado"] = True
            return redirect(url_for("painel"))
        flash("Login ou senha incorretos.", "erro")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/painel")
def painel():
    if not session.get("logado"):
        return redirect(url_for("login"))

    busca = request.args.get("busca", "").strip()
    campo = request.args.get("campo", "Todos")
    data_ini = request.args.get("data_ini", "").strip()
    data_fim = request.args.get("data_fim", "").strip()
    editar_id = request.args.get("editar_id", "").strip()

    if data_ini and not validar_data(data_ini, obrigatoria=False):
        flash("Data inicial inválida. Use dd/mm/aaaa.", "erro")
        data_ini = ""
    if data_fim and not validar_data(data_fim, obrigatoria=False):
        flash("Data final inválida. Use dd/mm/aaaa.", "erro")
        data_fim = ""

    reunioes = buscar_reunioes(busca, campo, data_ini, data_fim)
    indicadores = contar_status()

    registro_edicao = None
    if editar_id:
        conn = get_db()
        registro_edicao = conn.execute("SELECT * FROM reunioes WHERE id = ?", (editar_id,)).fetchone()
        conn.close()

    return render_template(
        "painel.html",
        reunioes=reunioes,
        indicadores=indicadores,
        campo=campo,
        busca=busca,
        data_ini=data_ini,
        data_fim=data_fim,
        registro_edicao=registro_edicao,
        status_lista=STATUS_LISTA
    )

@app.route("/salvar", methods=["POST"])
def salvar():
    if not session.get("logado"):
        return redirect(url_for("login"))

    reuniao_id = request.form.get("reuniao_id", "").strip()
    nome = request.form.get("nome", "").strip()
    tema = request.form.get("tema", "").strip()
    data = request.form.get("data", "").strip()
    horario = request.form.get("horario", "").strip()
    participantes = request.form.get("participantes", "").strip()
    status = request.form.get("status", "Planejada").strip()
    pautas = request.form.get("pautas", "").strip()
    observacoes = request.form.get("observacoes", "").strip()

    if not nome or not tema or not data:
        flash("Preencha nome da reunião, tema e data.", "erro")
        return redirect(url_for("painel", editar_id=reuniao_id if reuniao_id else ""))

    if not validar_data(data):
        flash("Data inválida. Use o formato dd/mm/aaaa.", "erro")
        return redirect(url_for("painel", editar_id=reuniao_id if reuniao_id else ""))

    if not validar_horario(horario):
        flash("Horário inválido. Use o formato hh:mm.", "erro")
        return redirect(url_for("painel", editar_id=reuniao_id if reuniao_id else ""))

    conn = get_db()
    cur = conn.cursor()

    if reuniao_id:
        if reuniao_duplicada(nome, tema, data, horario, ignorar_id=reuniao_id):
            conn.close()
            flash("Já existe outra reunião com o mesmo nome, tema, data e horário.", "erro")
            return redirect(url_for("painel", editar_id=reuniao_id))

        cur.execute("""
            UPDATE reunioes
            SET nome=?, tema=?, data_reuniao=?, horario=?, participantes=?, status=?, pautas=?, observacoes=?
            WHERE id=?
        """, (nome, tema, data, horario, participantes, status, pautas, observacoes, reuniao_id))
        flash("Reunião atualizada com sucesso.", "sucesso")
    else:
        if reuniao_duplicada(nome, tema, data, horario):
            conn.close()
            flash("Já existe uma reunião com o mesmo nome, tema, data e horário.", "erro")
            return redirect(url_for("painel"))

        cur.execute("""
            INSERT INTO reunioes (nome, tema, data_reuniao, horario, participantes, status, pautas, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, tema, data, horario, participantes, status, pautas, observacoes))
        flash("Reunião cadastrada com sucesso.", "sucesso")

    conn.commit()
    conn.close()
    return redirect(url_for("painel"))

@app.route("/excluir/<int:reuniao_id>", methods=["POST"])
def excluir(reuniao_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM reunioes WHERE id = ?", (reuniao_id,))
    conn.commit()
    conn.close()
    flash("Reunião excluída com sucesso.", "sucesso")
    return redirect(url_for("painel"))

@app.route("/detalhes/<int:reuniao_id>")
def detalhes(reuniao_id):
    if not session.get("logado"):
        return redirect(url_for("login"))

    conn = get_db()
    reuniao = conn.execute("SELECT * FROM reunioes WHERE id = ?", (reuniao_id,)).fetchone()
    conn.close()

    if not reuniao:
        flash("Reunião não encontrada.", "erro")
        return redirect(url_for("painel"))

    return render_template("detalhes.html", reuniao=reuniao)

if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
