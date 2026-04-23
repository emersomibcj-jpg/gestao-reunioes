<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Painel</title>

<style>
body {
    font-family: Arial;
    background: #f4f6f9;
    padding: 20px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}

h2 {
    color: #2c3e50;
}

input, select, textarea {
    width: 100%;
    padding: 10px;
    margin-top: 5px;
    margin-bottom: 10px;
}

button {
    padding: 10px;
    width: 100%;
}
</style>
</head>

<body>

<!-- 🔥 MENU DE USUÁRIOS (SÓ ADMIN) -->
{% if session.get('usuario_tipo') == 'admin' %}
<div class="card">
    <b>Usuários:</b><br><br>

    <a href="/usuario/emerson">Emerson</a> |
    <a href="/usuario/davi">Davi</a> |
    <a href="/usuario/matthews">Matthews</a> |
    <a href="/usuario/giovanne">Giovanne</a> |
    <a href="/usuario/rebecca">Rebecca</a> |
    <a href="/usuario/liliane">Liliane</a> |
    <a href="/usuario/maya">Maya</a> |

    <a href="/painel">[Todos]</a>
</div>
{% endif %}


<div class="card">
    <h2>Reuniões cadastradas</h2>

    <table border="1" width="100%" cellpadding="10">
        <tr>
            <th>ID</th>
            <th>Nome</th>
            <th>Tema</th>
            <th>Data</th>
            <th>Status</th>
        </tr>

        {% for r in reunioes %}
        <tr>
            <td>{{ r.id }}</td>
            <td>{{ r.nome }}</td>
            <td>{{ r.tema }}</td>
            <td>{{ r.data_reuniao }}</td>
            <td>{{ r.status }}</td>
        </tr>
        {% endfor %}
    </table>
</div>


<div class="card">
    <h2>Cadastro de reunião</h2>

    <form method="POST" action="/salvar">

        Nome da reunião
        <input type="text" name="nome" required>

        Tema
        <input type="text" name="tema" required>

        Data
        <input type="text" name="data" placeholder="dd/mm/aaaa">

        Horário
        <input type="text" name="horario" placeholder="hh:mm">

        Participantes
        <input type="text" name="participantes">

        Status
        <select name="status">
            {% for s in status_lista %}
            <option value="{{ s }}">{{ s }}</option>
            {% endfor %}
        </select>

        Pautas
        <textarea name="pautas"></textarea>

        Observações
        <textarea name="observacoes"></textarea>

        <button type="submit">Salvar</button>
    </form>
</div>

</body>
</html>
