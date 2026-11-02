from flask import Flask, render_template, redirect, request, url_for, flash
import sqlite3
from flask_login import login_manager
from flask_bcrypt import Bcrypt
from functools import wraps
import base64
from flask import session
import os


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-troque-isto")

bcrypt = Bcrypt(app)

def conexao():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'logs' not in session:
            flash("Você precisa fazer login primeiro.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def usuario_inicial(username, password):    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    conn = conexao()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO logs (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        print(f"Usuário '{username}' criado com sucesso.")
    except sqlite3.IntegrityError:
        print(f"Usuário '{username}' já existe.")
    conn.close()



@app.route("/login", methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        nome = request.form.get('username')
        senha = request.form.get('password')

        if nome and senha:

            conn = conexao()

            usuario = conn.execute(
                'SELECT username, password_hash FROM logs WHERE username = ?',
                (nome,)
            ).fetchone()

            conn.close()

            if usuario:

                hashed_password = usuario['password_hash']

                if bcrypt.check_password_hash(hashed_password, senha):

                    session['logs'] = usuario['username']

                    return redirect(url_for('index'))

                else:
                    flash("Senha incorreta")

            else:
                flash("Usuário não encontrado")

    return render_template('admin/log_user.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logs', None)  # Remove a sessão do usuário
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for('login'))

@app.route('/excluir_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def excluirUsuario(id):
    with conexao() as conn:
        usuario = conn.execute('SELECT id, username FROM logs WHERE id = ?', (id,)).fetchone()

    if usuario is None:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('user'))

    if request.method == 'POST':
        with conexao() as conn:
            conn.execute('DELETE FROM logs WHERE id = ?', (id,))
            conn.commit()
        flash('Usuário excluído com sucesso.', 'success')
        return redirect(url_for('user'))

    return render_template('admin/excluir_usuario.html', log=usuario)

@app.route("/criar_user", methods=["GET", "POST"])
@login_required
def CriarLog():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Informe o nome de usuário e a senha.", "danger")
            return render_template("admin/criar_user.html")
        with conexao() as conn:

            usuario_existe = conn.execute(
                "SELECT 1 FROM logs WHERE username = ?", (username,)
            ).fetchone()

            if usuario_existe:
                flash("Já existe um usuário com esse nome.", "danger")
                return render_template("admin/criar_user.html")


            password_hash = bcrypt.generate_password_hash(password).decode("utf-8")


            conn.execute(
                "INSERT INTO logs (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()

        flash("Usuário criado com sucesso!", "success")
        return redirect(url_for("user"))

    return render_template("admin/criar_user.html")

@app.route("/user")
@login_required
def user():
    conn = conexao()

    logs = conn.execute(
        "SELECT id, username FROM logs ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("admin/user.html", logs=logs)

@app.route("/admin")
@login_required
def index():
    
    return render_template("admin/index.html")



@app.route("/listar_categorias")
@login_required
def listarCategoria():
    conn = conexao()
    categoria = conn.execute("select * from categoria")
    return render_template("admin/listar_categoria.html", categorias=categoria)


@app.route("/listar_produtos")
@login_required
def listarProdutos():
    conn = conexao()
    produto = conn.execute(
        """SELECT produto.*, categoria.nome AS nome_categoria
                              FROM produto
                              LEFT JOIN categoria ON produto.id_categoria = categoria.id"""
    ).fetchall()
    conn.close()
    return render_template("admin/listar_produtos.html", produto=produto)


@app.route("/cadastrar_categorias", methods=["GET", "POST"])
@login_required
def cadastrarCategoria():

    if request.method == "POST":
        nome_categoria = request.form.get("nome_categoria")
        descricao = request.form.get("descricao")
        ativo = request.form.get("ativo")
        imagem = request.files.get("imagem")
        imagem_base64 = base64.b64encode(imagem.read()).decode("utf-8")
        if nome_categoria:
            conn = conexao()
            conn.execute(
                """INSERT INTO categoria (nome, descricao, 
             ativo, imagem )
              VALUES (?, ?, ?, ?)""",
                (nome_categoria, descricao, ativo, imagem_base64),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("listarCategoria"))

    return render_template("admin/cadastrar_categoria.html")


@app.route("/cadastrar_produto", methods=["GET", "POST"])
@login_required
def cadastrarProduto():
    conn = conexao()
    if request.method == "POST":
        nome_produto = request.form.get("nome_produto")
        preco = request.form.get("preco")
        id_categoria = request.form.get("categoria")
        ativo = request.form.get("ativo")
        imagem = request.files.get("imagem")
        imagem_base64 = (
            base64.b64encode(imagem.read()).decode("utf-8") if imagem else ""
        )
        if nome_produto:
            conn.execute(
                "INSERT INTO produto (nome, preco, ativo, imagem, id_categoria) VALUES (?,?,?,?,?)",
                (nome_produto, preco, ativo, imagem_base64, id_categoria),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("listarProdutos"))
    categorias = conn.execute("SELECT * FROM categoria").fetchall()

    produto = conn.execute("SELECT * FROM produto").fetchall()

    conn.close()

    return render_template(
        "admin/cadastrar_produtos.html", produto=produto, categorias=categorias
    )
    
@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
def editarUsuario(id):
    with conexao() as conn:
        usuario = conn.execute('SELECT * FROM logs WHERE id = ?', (id,)).fetchone()

    if usuario is None:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('user'))

    if request.method == 'POST':
        nome = request.form.get('nome').strip()
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
      

        if not nome:
            flash('Informe o nome do usuário.', 'danger')
            return render_template('admin/editar_usuario.html', usuario=usuario)

        if senha != confirmar_senha:
            flash('As senhas não conferem.', 'danger')
            return render_template('admin/editar_usuario.html', usuario=usuario)

        with conexao() as conn:
            if conn.execute('SELECT 1 FROM logs WHERE username = ? AND id <> ?', (nome, id)).fetchone():
                flash('Já existe um usuário com esse nome.', 'danger')
                return render_template('admin/editar_usuario.html', usuario=usuario)

            if senha:
                conn.execute(
                "UPDATE logs SET username = ?, password_hash = ? WHERE id = ?",
                    (nome, bcrypt.generate_password_hash(senha).decode("utf-8"), id))
            else:
                conn.execute(
                    'UPDATE logs SET username = ? WHERE id = ?',
                    (nome, id),
                )
            conn.commit()

        flash('Usuário atualizado com sucesso.', 'success')
        return redirect(url_for('user'))

    return render_template('admin/editar_usuario.html', usuario=usuario)


@app.route("/editarcategoria/<int:id>", methods=["GET", "POST"])
@login_required
def editarCategoria(id):
    conn = conexao()
    categoria = conn.execute("select * from categoria where id=?", (id,)).fetchone()

    if request.method == "POST":
        nome_categoria = request.form.get("nome_categoria")
        descricao = request.form.get("descricao")
        ativo = request.form.get("ativo")
        imagem = request.files.get("imagem")
        imagem_base64 = base64.b64encode(imagem.read()).decode("utf-8")
        if nome_categoria:
            conn = conexao()
            if imagem:
                conn.execute(
                    """UPDATE categoria SET nome=?, descricao=?,
                              ativo=?,
                              imagem=? WHERE id=?""",
                    (
                        nome_categoria,
                        descricao,
                        ativo,
                        imagem_base64,
                        id,
                    ),
                )
            else:
                conn.execute(
                    """UPDATE categoria SET nome=?, descricao=?,
                              ativo=? WHERE id=?""",
                    (
                        nome_categoria,
                        descricao,
                        ativo,
                        id,
                    ),
                )

            conn.commit()
            conn.close()
            return redirect(url_for("listarCategoria"))

    return render_template("admin/editar_categoria.html", categoria=categoria)

@app.route("/editarProduto/<int:id>", methods=["GET", "POST"])
@login_required
def editarProduto(id):
    conn = conexao()
    produto= conn.execute("select * from produto where id=?", (id,)).fetchone()

    if request.method == "POST":
        nome_produto = request.form.get("nome_produto")
        preco = float(request.form.get("preco"))
        ativo = request.form.get("ativo")
        imagem = request.files.get("imagem")
        imagem_base64 = base64.b64encode(imagem.read()).decode("utf-8")
        try:
            preco = float(request.form.get("preco", ""))
        except ValueError:
            flash("Preço inválido.", "danger")
            preco = None
        if nome_produto:
            conn = conexao()
            if imagem:
                conn.execute(
                    """UPDATE produto SET nome=?, preco=?,
                              ativo=?,
                              imagem=? WHERE id=?""",
                    (
                        nome_produto,
                        preco,
                        ativo,
                        imagem_base64,
                        id,
                    ),
                )
            else:
                conn.execute(
                    """UPDATE produto SET nome=?, preco=?,
                              ativo=?, imagem=? WHERE id=?""",
                    (
                        nome_produto,
                        preco,
                        ativo,
                        imagem_base64,
                        id,
                    ),
                )

            conn.commit()
            conn.close()
            return redirect(url_for("listarProdutos"))

    return render_template("admin/editar_produto.html", produto=produto)



@app.route("/excluir_categoria/<int:id>", methods=["GET", "POST"])
@login_required
def excluirCategoria(id):
    conn = conexao()
    categoria = conn.execute(
        """SELECT * FROM categoria
          WHERE id = ?""",
        (id,),
    ).fetchone()

    if request.method == "POST":
        conn.execute("DELETE FROM categoria WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("listarCategoria"))

    return render_template("admin/excluir_categoria.html", categoria=categoria)

@app.route("/excluir_produto/<int:id>", methods=["GET", "POST"])
@login_required
def excluirProduto(id):
    conn = conexao()
    produto = conn.execute(
        """SELECT * FROM produto
          WHERE id = ?""",
        (id,),
    ).fetchone()

    if request.method == "POST":
        conn.execute("DELETE FROM produto WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("listarProdutos"))

    return render_template("admin/excluir_Produto.html", produto=produto)

@app.route("/")
def home():
    conn = conexao()
    produto = conn.execute('''SELECT produto.*,
                           categoria.nome AS nome_categoria
                           FROM produto
                           LEFT JOIN categoria
                           ON produto.id_categoria = categoria.id
                           ORDER BY produto.preco ASC
                           LIMIT 3;''').fetchall()
    conn = conexao()
    categoria = conn.execute("select * from categoria")
    
    return render_template("site/index.html", produto = produto,categoria=categoria)

@app.route("/categorias")
def categorias():
    conn = conexao()
    categoria = conn.execute("select * from categoria")
        
    return render_template("site/categorias.html", categorias=categoria)

@app.route("/produtos")
def produtos():
    conn = conexao()
    produto = conn.execute('''SELECT produto.*,
                           categoria.nome AS nome_categoria
                           FROM produto
                           LEFT JOIN categoria
                           ON produto.id_categoria = categoria.id
                           ORDER BY produto.preco ASC
                           LIMIT 3;''').fetchall()
    conn = conexao()
    
    return render_template("site/produtos.html", produto = produto)

@app.route("/verCategoria/<int:id>",methods=["GET", "POST"])
def verCategoria(id):
    conn = conexao()
    cursor = conn.cursor()
    categoria = conn.execute(
            """SELECT * FROM categoria
              WHERE id = ?""",
            (id,),
        ).fetchone()
    produto = cursor.execute(
        "SELECT * FROM produto WHERE id_categoria = ?",
        (id,)
    ).fetchall()
    conn.close()
        
    return render_template("site/verCategoria.html", categorias=categoria,produto=produto)
    



app.run(debug=True, port=5005)
