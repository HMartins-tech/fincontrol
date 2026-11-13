from functools import wraps

from flask import (Flask, render_template, request, redirect,  # pyright: ignore[reportMissingImports]
                   session, url_for)
from flask_mysqldb import MySQL  # pyright: ignore[reportMissingImports]
from MySQLdb.cursors import DictCursor  # pyright: ignore[reportMissingImports]
from werkzeug.security import generate_password_hash, check_password_hash

import config

app = Flask(__name__)

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

# Chave usada para assinar os cookies de sessão (login)
app.secret_key = config.SECRET_KEY

mysql = MySQL(app)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def consultar(sql, parametros=(), unico=False):
    """
    Executa um SELECT e retorna todos os registros como dicionários.
    Se unico=True, retorna apenas o primeiro registro.
    """
    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute(sql, parametros)

    if unico:
        registro = cursor.fetchone()
    else:
        registro = cursor.fetchall()

    cursor.close()

    return registro


def executar(sql, parametros=()):
    """
    Executa um INSERT/UPDATE/DELETE e faz commit.
    """
    cursor = mysql.connection.cursor()

    cursor.execute(sql, parametros)

    mysql.connection.commit()

    cursor.close()


def validar_valor(texto_valor):
    """
    Valida o valor vindo do formulário.
    Retorna o valor em float se for um número maior que zero,
    ou None se for inválido (texto, zero ou negativo).
    """
    try:
        valor = float(str(texto_valor).replace(',', '.'))
    except (TypeError, ValueError):
        return None

    if valor <= 0:
        return None

    return round(valor, 2)


def transacao_pertence_ao_usuario(id_transacao):
    """
    Verifica se a transação informada pertence ao usuário logado.
    Impede que um usuário edite ou exclua registros de outro.
    """
    registro = consultar(
        """
        SELECT id_transacao
        FROM transacao
        WHERE id_transacao = %s
          AND id_usuario = %s
        """,
        (id_transacao, session['id_usuario']),
        unico=True
    )

    return registro is not None


def login_obrigatorio(rota):
    """
    Decorator: bloqueia a rota se o usuário não estiver logado,
    redirecionando para a tela de login.
    """
    @wraps(rota)
    def wrapper(*args, **kwargs):

        if 'id_usuario' not in session:
            return redirect(url_for('login'))

        return rota(*args, **kwargs)

    return wrapper


# ------------------------------------------------------------------
# Login / Logout
# ------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        senha = request.form['senha']

        usuario = consultar(
            """
            SELECT *
            FROM usuario
            WHERE email = %s
            """,
            (email,),
            unico=True
        )

        # Verifica se o usuário existe e se a senha bate com o hash salvo
        if usuario and check_password_hash(usuario['senha'], senha):

            session['id_usuario'] = usuario['id_usuario']
            session['nome_usuario'] = usuario['nome']

            return redirect('/dashboard')

        return render_template('login.html', erro='E-mail ou senha inválidos.')

    return render_template('login.html')


@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# ------------------------------------------------------------------
# Página inicial
# ------------------------------------------------------------------

@app.route('/')
def home():

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()

        mensagem = "✅ Conexão com MySQL realizada com sucesso!"

    except Exception as erro:
        mensagem = f"❌ Erro: {erro}"

    return render_template('index.html', mensagem=mensagem)


# ------------------------------------------------------------------
# Usuários
# ------------------------------------------------------------------

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():

    if request.method == 'POST':

        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        # Salva o HASH da senha, nunca a senha pura
        try:
            executar(
                """
                INSERT INTO usuario (nome, email, senha)
                VALUES (%s, %s, %s)
                """,
                (nome, email, generate_password_hash(senha))
            )

        except Exception:
            return render_template(
                'cadastro.html',
                erro='Este e-mail já está cadastrado.'
            )

        return redirect('/cadastro')

    return render_template('cadastro.html')


@app.route('/usuarios')
@login_obrigatorio
def usuarios():

    usuarios = consultar(
        """
        SELECT id_usuario, nome, email
        FROM usuario
        """
    )

    return render_template(
        'usuarios.html',
        usuarios=usuarios
    )


@app.route('/excluir_usuario/<int:id>')
@login_obrigatorio
def excluir_usuario(id):

    # O usuário logado não pode excluir a própria conta: isso encerraria
    # a sessão no meio do uso e deixaria o sistema em estado inconsistente
    if id == session['id_usuario']:
        return redirect('/usuarios')

    executar(
        """
        DELETE FROM usuario
        WHERE id_usuario = %s
        """,
        (id,)
    )

    return redirect('/usuarios')


@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_usuario(id):

    if request.method == 'POST':

        nome = request.form['nome']
        email = request.form['email']

        executar(
            """
            UPDATE usuario
            SET nome = %s,
                email = %s
            WHERE id_usuario = %s
            """,
            (nome, email, id)
        )

        return redirect('/usuarios')

    usuario = consultar(
        """
        SELECT id_usuario, nome, email
        FROM usuario
        WHERE id_usuario = %s
        """,
        (id,),
        unico=True
    )

    return render_template(
        'editar_usuario.html',
        usuario=usuario
    )


# ------------------------------------------------------------------
# Receitas
# ------------------------------------------------------------------

@app.route('/receitas', methods=['GET', 'POST'])
@login_obrigatorio
def receitas():

    if request.method == 'POST':

        descricao = request.form['descricao']
        valor = validar_valor(request.form['valor'])
        data = request.form['data']
        categoria = request.form['categoria']

        # Valor precisa ser numérico e maior que zero:
        # valor zero não movimenta o saldo e negativo inverte o tipo da transação
        if valor is None:
            categorias = consultar(
                """
                SELECT id_categoria, nome_categoria
                FROM categoria
                WHERE tipo = 'Receita'
                """
            )

            return render_template(
                'receitas.html',
                categorias=categorias,
                erro='Informe um valor numérico maior que zero.'
            )

        executar(
            """
            INSERT INTO transacao
            (
                descricao,
                valor,
                data_transacao,
                tipo,
                id_usuario,
                id_categoria
            )
            VALUES
            (%s,%s,%s,'Receita',%s,%s)
            """,
            (
                descricao,
                valor,
                data,
                session['id_usuario'],
                categoria
            )
        )

        return redirect('/receitas')

    categorias = consultar(
        """
        SELECT id_categoria, nome_categoria
        FROM categoria
        WHERE tipo = 'Receita'
        """
    )

    return render_template(
        'receitas.html',
        categorias=categorias
    )


@app.route('/listar_receitas')
@login_obrigatorio
def listar_receitas():

    receitas = consultar(
        """
        SELECT
            t.id_transacao,
            t.descricao,
            t.valor,
            t.data_transacao,
            c.nome_categoria
        FROM transacao t
        INNER JOIN categoria c
            ON t.id_categoria = c.id_categoria
        WHERE t.tipo = 'Receita'
          AND t.id_usuario = %s
        """,
        (session['id_usuario'],)
    )

    return render_template(
        'listar_receitas.html',
        receitas=receitas
    )


@app.route('/editar_receita/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_receita(id):

    # O usuário só pode editar transações que pertencem a ele
    if not transacao_pertence_ao_usuario(id):
        return redirect('/listar_receitas')

    categorias = consultar(
        """
        SELECT id_categoria, nome_categoria
        FROM categoria
        WHERE tipo = 'Receita'
        """
    )

    if request.method == 'POST':

        descricao = request.form['descricao']
        valor = validar_valor(request.form['valor'])
        data = request.form['data']
        categoria = request.form['categoria']

        if valor is None:
            return render_template(
                'editar_receita.html',
                receita={'id_transacao': id, 'descricao': descricao,
                         'valor': request.form['valor'], 'data_transacao': data,
                         'id_categoria': int(categoria)},
                categorias=categorias,
                erro='Informe um valor numérico maior que zero.'
            )

        executar(
            """
            UPDATE transacao
            SET descricao = %s,
                valor = %s,
                data_transacao = %s,
                id_categoria = %s
            WHERE id_transacao = %s
              AND id_usuario = %s
            """,
            (
                descricao,
                valor,
                data,
                categoria,
                id,
                session['id_usuario']
            )
        )

        return redirect('/listar_receitas')

    receita = consultar(
        """
        SELECT id_transacao, descricao, valor, data_transacao, id_categoria
        FROM transacao
        WHERE id_transacao = %s
        """,
        (id,),
        unico=True
    )

    return render_template(
        'editar_receita.html',
        receita=receita,
        categorias=categorias
    )


@app.route('/excluir_receita/<int:id>')
@login_obrigatorio
def excluir_receita(id):

    # Só exclui se a transação pertencer ao usuário logado
    executar(
        """
        DELETE FROM transacao
        WHERE id_transacao = %s
          AND id_usuario = %s
        """,
        (id, session['id_usuario'])
    )

    return redirect('/listar_receitas')


# ------------------------------------------------------------------
# Despesas
# ------------------------------------------------------------------

@app.route('/despesas', methods=['GET', 'POST'])
@login_obrigatorio
def despesas():

    if request.method == 'POST':

        descricao = request.form['descricao']
        valor = validar_valor(request.form['valor'])
        data = request.form['data']
        categoria = request.form['categoria']

        # Valor precisa ser numérico e maior que zero:
        # valor zero não movimenta o saldo e negativo inverte o tipo da transação
        if valor is None:
            categorias = consultar(
                """
                SELECT id_categoria, nome_categoria
                FROM categoria
                WHERE tipo = 'Despesa'
                """
            )

            return render_template(
                'despesas.html',
                categorias=categorias,
                erro='Informe um valor numérico maior que zero.'
            )

        executar(
            """
            INSERT INTO transacao
            (
                descricao,
                valor,
                data_transacao,
                tipo,
                id_usuario,
                id_categoria
            )
            VALUES
            (%s,%s,%s,'Despesa',%s,%s)
            """,
            (
                descricao,
                valor,
                data,
                session['id_usuario'],
                categoria
            )
        )

        return redirect('/despesas')

    categorias = consultar(
        """
        SELECT id_categoria, nome_categoria
        FROM categoria
        WHERE tipo = 'Despesa'
        """
    )

    return render_template(
        'despesas.html',
        categorias=categorias
    )


@app.route('/listar_despesas')
@login_obrigatorio
def listar_despesas():

    despesas = consultar(
        """
        SELECT
            t.id_transacao,
            t.descricao,
            t.valor,
            t.data_transacao,
            c.nome_categoria
        FROM transacao t
        INNER JOIN categoria c
            ON t.id_categoria = c.id_categoria
        WHERE t.tipo = 'Despesa'
          AND t.id_usuario = %s
        """,
        (session['id_usuario'],)
    )

    return render_template(
        'listar_despesas.html',
        despesas=despesas
    )


@app.route('/editar_despesa/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_despesa(id):

    # O usuário só pode editar transações que pertencem a ele
    if not transacao_pertence_ao_usuario(id):
        return redirect('/listar_despesas')

    categorias = consultar(
        """
        SELECT id_categoria, nome_categoria
        FROM categoria
        WHERE tipo = 'Despesa'
        """
    )

    if request.method == 'POST':

        descricao = request.form['descricao']
        valor = validar_valor(request.form['valor'])
        data = request.form['data']
        categoria = request.form['categoria']

        if valor is None:
            return render_template(
                'editar_despesa.html',
                despesa={'id_transacao': id, 'descricao': descricao,
                         'valor': request.form['valor'], 'data_transacao': data,
                         'id_categoria': int(categoria)},
                categorias=categorias,
                erro='Informe um valor numérico maior que zero.'
            )

        executar(
            """
            UPDATE transacao
            SET descricao = %s,
                valor = %s,
                data_transacao = %s,
                id_categoria = %s
            WHERE id_transacao = %s
              AND id_usuario = %s
            """,
            (
                descricao,
                valor,
                data,
                categoria,
                id,
                session['id_usuario']
            )
        )

        return redirect('/listar_despesas')

    despesa = consultar(
        """
        SELECT id_transacao, descricao, valor, data_transacao, id_categoria
        FROM transacao
        WHERE id_transacao = %s
        """,
        (id,),
        unico=True
    )

    return render_template(
        'editar_despesa.html',
        despesa=despesa,
        categorias=categorias
    )


@app.route('/excluir_despesa/<int:id>')
@login_obrigatorio
def excluir_despesa(id):

    # Só exclui se a transação pertencer ao usuário logado
    executar(
        """
        DELETE FROM transacao
        WHERE id_transacao = %s
          AND id_usuario = %s
        """,
        (id, session['id_usuario'])
    )

    return redirect('/listar_despesas')


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@app.route('/dashboard')
@login_obrigatorio
def dashboard():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(valor),0)
        FROM transacao
        WHERE tipo='Receita'
          AND id_usuario=%s
    """, (session['id_usuario'],))

    total_receitas = float(cursor.fetchone()[0])

    cursor.execute("""
        SELECT COALESCE(SUM(valor),0)
        FROM transacao
        WHERE tipo='Despesa'
          AND id_usuario=%s
    """, (session['id_usuario'],))

    total_despesas = float(cursor.fetchone()[0])

    saldo = total_receitas - total_despesas

    cursor.close()

    return render_template(
        'dashboard.html',
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo=saldo
    )


if __name__ == '__main__':
    app.run(debug=True)
