from io import BytesIO
import mimetypes
from flask import Flask, render_template, redirect, request, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import io

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'segredo'  # Defina uma chave secreta única
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'uploads'

#TABELA
turma_aluno = db.Table('turma_aluno',
    db.Column('aluno_id', db.Integer, db.ForeignKey('alunos.id')),
    db.Column('turma_id', db.Integer, db.ForeignKey('turma.id'))
)

class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    arquivo = db.Column(db.LargeBinary, nullable=True)
    arquivo_nome = db.Column(db.String(100), nullable=True)  # Armazena o nome original do arquivo
    criado = db.Column(db.DateTime, default=datetime.utcnow)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)  # Associa tarefa a uma turma específica
    turma = db.relationship('Turma', backref=db.backref('tarefas', lazy=True))

    def __repr__(self) -> str:
        return f"Tarefa {self.id}"

class Turma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    professor = db.Column(db.String(100), nullable=False)
    codigo_acesso = db.Column(db.String(20), nullable=False, unique = True)  # Novo campo

    def __repr__(self) -> str:
        return f"{self.nome}"


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    tipo_perfil = db.Column(db.String(50), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo_perfil
    }

class Aluno(Usuario):
    __tablename__ = 'alunos'
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    turmas = db.relationship('Turma', secondary=turma_aluno, backref=db.backref('alunos', lazy='dynamic'))
    
    __mapper_args__ = {
        'polymorphic_identity': 'aluno',
    }


class Professor(Usuario):
    __tablename__ = 'professores'
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'professor',
    }


with app.app_context():
    db.create_all()

#<---------Rotas Principais---------->
@app.route("/turma/<int:turma_id>", methods=["POST", "GET"])
def turma(turma_id):
    turma = Turma.query.get_or_404(turma_id)  # Carregar a turma pelo ID
    tipo_perfil = session.get('tipo_perfil')
    user_id = session.get('user_id')
    user = Usuario.query.get_or_404(user_id)
    if request.method == "POST":
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        arquivo = request.files.get('arquivo')

        
        if titulo and descricao:
            arquivo_nome = arquivo.filename if arquivo else 'sem_nome'
            arquivo = arquivo.read() if arquivo else None  # Ler o conteúdo do arquivo

            nova_tarefa = Tarefa(
                titulo=titulo,
                descricao=descricao,
                arquivo=arquivo,
                arquivo_nome=arquivo_nome,
                turma_id=turma_id
            )

            try:
                db.session.add(nova_tarefa)
                db.session.commit()
                return redirect(f"/turma/{turma_id}")
            except Exception as e:
                return f"ERROR: {e}"
        else:
            return "Título ou descrição não fornecidos", 400
    else:
        tarefas = Tarefa.query.filter_by(turma_id=turma_id).order_by(Tarefa.criado).all()
        return render_template("turma.html", tarefas=tarefas, turma=turma, tipo_perfil=tipo_perfil, user=user)



@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("cadastro.html")

@app.route("/logout")
def logout():
    session.clear()  # Limpa todos os dados da sessão
    return redirect("/home")


@app.route("/aluno/<int:id>")
def aluno(id: int):
    if 'user_id' not in session:
        return redirect("/login")
    user_id = session.get('user_id')
    user = Usuario.query.get_or_404(user_id) 
    if user.tipo_perfil != 'aluno' or user.id != id:
        return redirect("/login")
    return render_template("aluno.html", aluno=user, user=user)


@app.route("/professor/<int:id>", methods=["POST", "GET"])
def professor(id: int):
    if 'user_id' not in session:
        return redirect("/login")
    
    user_id = session.get('user_id')
    user = Usuario.query.get_or_404(user_id)

    if user.tipo_perfil != 'professor':
        return redirect("/login")
    
    if request.method == "POST":
        nome = request.form.get('nome')
        codigo_acesso = request.form.get('codigo_acesso')

        turma_existente = Turma.query.filter_by(codigo_acesso=codigo_acesso).first()

        if turma_existente:
            # Retorna uma mensagem de erro se o código já existir
            flash('O código de acesso já está em uso. Por favor, escolha outro.', 'error')
            return redirect(f"/professor/{id}")

        nova_turma = Turma(nome=nome, professor=user.nome, codigo_acesso=codigo_acesso)
        try:
            db.session.add(nova_turma)
            db.session.commit()
            return redirect(f"/professor/{id}")
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}"
    else:
        
        turmas = Turma.query.filter_by(professor=user.nome).all()
        return render_template("professor_home.html", turmas=turmas, user=user)

@app.route("/tarefa/<int:id>")
def tarefa_detalhes(id: int):
    tipo_perfil = session.get('tipo_perfil')
    tarefa = Tarefa.query.get_or_404(id)
    turma = tarefa.turma
    return render_template("tarefa.html", tarefa=tarefa, tipo_perfil=tipo_perfil, turma=turma)

@app.route("/editar_perfil/<int:id>", methods=["GET", "POST"])
def editar_perfil(id: int):
    if 'user_id' not in session:
        return redirect("/login")

    user_id = session.get('user_id')
    usuario = Usuario.query.get_or_404(id)

    # Verifica se o usuário na sessão é o mesmo que o ID fornecido
    if usuario.id != user_id:
        flash("Você não tem permissão para editar este perfil.", "error")
        return redirect("/")

    if request.method == "POST":
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')

        # Atualiza os campos do usuário
        usuario.nome = nome
        usuario.email = email
        if senha:  # Permite atualização de senha apenas se um novo valor for fornecido
            usuario.senha = senha

        try:
            db.session.commit()
            flash("Perfil atualizado com sucesso!", "success")
            return redirect(f"/{usuario.tipo_perfil}/{usuario.id}")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar perfil: {e}", "error")
            return redirect(f"/editar_perfil/{id}")
    else:
        return render_template("editar_perfil.html", usuario=usuario)

#<---------Rotas Auxiliares da Turma---------->

@app.route("/acessar_turma", methods=["POST"])
def acessar_turma():
    codigo_acesso = request.form.get('codigo_turma')
    turma = Turma.query.filter_by(codigo_acesso=codigo_acesso).first()
    user_id = session.get('user_id')
    aluno = Aluno.query.get(user_id)
    if turma:
         # Verificar se o aluno já está na turma
        if aluno not in turma.alunos:
            turma.alunos.append(aluno)
            db.session.commit()
        
        return redirect(f"/aluno/{aluno.id}")
    else:
        flash("Código de turma inválido", "turma")
        return redirect(f"/aluno/{aluno.id}")

@app.route("/delete/<int:id>")
def delete(id: int):
    tarefa = Tarefa.query.get_or_404(id)

    if session.get('tipo_perfil') != 'professor':
        flash('Acesso negado. Apenas professores podem deletar tarefas.', 'error')
        return redirect(f"/turma/{tarefa.turma_id}")

    try:
        # Excluir a tarefa do banco de dados
        db.session.delete(tarefa)
        db.session.commit()
        
        # Redirecionar para a turma correta após a exclusão
        return redirect(f"/turma/{tarefa.turma_id}")
    except Exception as e:
        return f"ERROR: {e}"


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id: int):
    tarefa = Tarefa.query.get_or_404(id)
    if session.get('tipo_perfil') != 'professor':
        flash('Acesso negado. Apenas professores podem editar tarefas.', 'error')
        return redirect(f"/turma/{tarefa.turma_id}")
    
    if request.method == "POST":
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        arquivo = request.files.get('arquivo')  # Obtenha o arquivo do formulário

        if titulo and descricao:
            tarefa.titulo = titulo
            tarefa.descricao = descricao

            if arquivo and arquivo.filename:
                # Lê o conteúdo do novo arquivo
                tarefa.arquivo = arquivo.read()
                tarefa.arquivo_nome = arquivo.filename

            try:
                db.session.commit()
                return redirect(f"/turma/{tarefa.turma_id}")
            except Exception as e:
                db.session.rollback()  # Reverte qualquer mudança em caso de erro
                return f"ERROR: {e}"
        else:
            return "Título ou descrição não fornecidos", 400

    else:
        turma = Turma.query.get_or_404(id)
        return render_template("edit.html", tarefa=tarefa, turma=turma)
    
#<---------Rotas Auxiliares da Turma_Professor---------->

# Rota para excluir uma turma
@app.route("/delete_turma/<int:id>")
def delete_turma(id: int):
    turma = Turma.query.get_or_404(id)
    if session.get('tipo_perfil') != 'professor':
        flash('Acesso negado. Apenas professores podem excluir tarefas.', 'error')
        return redirect(f"/turma/{turma.id}")

    try:
        # Remover a turma do banco de dados
        db.session.delete(turma)
        db.session.commit()
        professor_id = session.get('user_id')
        return redirect(f"/professor/{professor_id}")
    except Exception as e:
        return f"ERROR: {e}"

# Rota para editar uma turma
@app.route("/edit_turma/<int:id>", methods=["GET", "POST"])
def edit_turma(id: int):
    turma = Turma.query.get_or_404(id)
    if session.get('tipo_perfil') != 'professor':
        flash('Acesso negado. Apenas professores podem editar tarefas.', 'error')
        return redirect(f"/turma/{turma.turma_id}")
    
    # Recupera o ID do usuário da sessão
    user_id = session.get('user_id')
    
    # Recupera o usuário do banco de dados, caso necessário
    user = Usuario.query.get(user_id)

    if request.method == "POST":
        turma.nome = request.form.get('nome')
        turma.codigo_acesso = request.form.get('codigo_acesso')

        try:
            db.session.commit()
            return redirect(f"/professor/{user.id}")
        except Exception as e:
            return f"ERROR: {e}"
    else:
        return render_template("edit_turma.html", turma=turma, user=user)


#<---------Rotas Auxiliares do Login---------->
@app.route("/cadastro", methods=["POST"])
def cadastro():
    nome = request.form.get("nome")
    email = request.form.get("email")
    matricula = request.form.get("matricula")
    senha = request.form.get("senha")
    tipo_perfil = request.form.get("tipo_perfil")
    
    # Verificar se o email já existe
    if Usuario.query.filter_by(email=email).first():
        flash("Email já cadastrado. Tente um email diferente!", "cadastro")
        return redirect("/login")

    # Verificar se o nome de usuário já existe
    if Usuario.query.filter_by(nome=nome).first():
        flash("Nome de usuário já cadastrado. Escolha um nome diferente!", "cadastro")
        return redirect("/login")

    if Usuario.query.filter_by(matricula=matricula).first():
        flash("Matrícula já cadastrada. Tente uma matrícula diferente!", "cadastro")
        return redirect("/login")
    
    if tipo_perfil == "aluno":
        novo_aluno = Aluno(nome=nome, senha=senha, email=email, matricula=matricula)
        db.session.add(novo_aluno)
        
    elif tipo_perfil == "professor":
        novo_professor = Professor(nome=nome, email=email, senha=senha, matricula = matricula)
        db.session.add(novo_professor)

    try:
        db.session.commit()
        return redirect("/login")
    except Exception as e:
        flash(f"Erro ao cadastrar: {e}", "cadastro")
        return redirect("/login")

@app.route("/entrar", methods=["POST"])
def entrar():
    email = request.form.get("email")
    senha = request.form.get("senha")

    user = Usuario.query.filter_by(email=email, senha=senha).first()

    if user:
        session['user_id'] = user.id
        session['matricula'] = user.matricula
        session['tipo_perfil'] = user.tipo_perfil

        if user.tipo_perfil == 'aluno':
            return redirect(f"/aluno/{user.id}")
        elif user.tipo_perfil == 'professor':
            return redirect(f"/professor/{user.id}")
    else:
        flash("Usuário ou senha inválidos", "login")
        return redirect("/login")
#<---------Rotas Auxiliares da Tarefa---------->
@app.route('/download/<int:id>')
def download_arquivo(id):
    tarefa = Tarefa.query.get_or_404(id)
    if tarefa.arquivo:
        arquivo_bytes = BytesIO(tarefa.arquivo)
        arquivo_nome = tarefa.arquivo_nome or 'arquivo_tarefa'  # Nome original do arquivo

        # Determina o tipo MIME com base na extensão do arquivo
        mimetype, _ = mimetypes.guess_type(arquivo_nome)
        mimetype = mimetype or 'application/octet-stream'

        return send_file(
            arquivo_bytes,
            download_name=arquivo_nome,  # Nome do arquivo para download
            mimetype=mimetype,  # Tipo MIME do arquivo
            as_attachment=True
        )
    else:
        return "Arquivo não encontrado", 404


if __name__ == "__main__":

    app.run(debug=True)