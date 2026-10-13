from flask import Flask, render_template, redirect, request, url_for, flash
import sqlite3
from flask_login import login_manager
from flask_bcrypt import Bcrypt
from functools import wraps
import base64
from flask import session

app = Flask(__name__)
app.secret_key = "uma_chave_muito_secreta_e_aleatoria"
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
usuario_inicial("admin", "senha123")



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form.get('username')
        senha = request.form.get('password')

        if nome and senha:
            conn = conexao()

            
            usuario = conn.execute(
                'SELECT username, password_hash FROM logs WHERE username=?',
                (nome,)
            ).fetchone()

            if usuario:
                hashed_password = usuario['password_hash']

                # senha digitada com o hash do banco
                if bcrypt.check_password_hash(hashed_password, senha):
                    session['logs'] = usuario['username']  
                    return redirect(url_for('index'))
                else:
                    print("Senha incorreta")
            else:
                print("Usuário não encontrado")

    return render_template('admin/login.html')

@app.route("/")
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
                              ativo=? imagem=? WHERE id=?""",
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

@app.route("/home")
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
