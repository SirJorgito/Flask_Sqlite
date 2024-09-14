import os
from flask import Flask, render_template, redirect, request, send_from_directory, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    conteudo = db.Column(db.String(100), nullable=False)
    feito = db.Column(db.Integer, default=0)
    criado = db.Column(db.DateTime, default=datetime.utcnow)
    turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'), nullable=False)  # Associa tarefa a uma turma específica
    turma = db.relationship('Turma', backref=db.backref('tarefas', lazy=True))

    def __repr__(self) -> str:
        return f"Tarefa {self.id}"

class Turma(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    professor = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    codigo_acesso = db.Column(db.String(20), nullable=False)  # Novo campo

    def __repr__(self) -> str:
        return f"{self.nome}"


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    tipo_perfil = db.Column(db.String(50), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo_perfil
    }

class Aluno(Usuario):
    __tablename__ = 'alunos'
    id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    matricula = db.Column(db.String(100), nullable=False)
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
    if request.method == "POST":
        arquivo = request.files.get('conteudo')
        
        if arquivo:
            nome_arquivo = arquivo.filename
            
            # Verificar se o diretório 'uploads' existe, se não, criá-lo
            caminho_diretorio = 'uploads'
            if not os.path.exists(caminho_diretorio):
                os.makedirs(caminho_diretorio)
            
            nova_tarefa = Tarefa(conteudo=nome_arquivo, turma_id=turma_id)
            try:
                db.session.add(nova_tarefa)
                db.session.commit()
                
                caminho_arquivo = os.path.join(caminho_diretorio, nome_arquivo)
                arquivo.save(caminho_arquivo)  # Salvar o arquivo no diretório 'uploads'
                
                return redirect(f"/turma/{turma_id}")
            except Exception as e:
                return f"ERROR: {e}"
        else:
            return "Nenhum arquivo foi selecionado", 400
    else:
        tarefas = Tarefa.query.filter_by(turma_id=turma_id).order_by(Tarefa.criado).all()
        return render_template("turma.html", tarefas=tarefas, turma=turma)



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


@app.route("/aluno")
def aluno():
    if 'user_id' not in session:
        return redirect("/login")
    
    
    
    user_id = session.get('user_id')
    user = Usuario.query.get_or_404(user_id)
    if user.tipo_perfil != 'aluno':
        return redirect("/login")
    aluno = Aluno.query.get_or_404(user_id)  # Obtém o aluno pelo ID da sessão
    return render_template("aluno.html", aluno=aluno)


@app.route("/professor", methods=["POST", "GET"])
def professor():
    if 'user_id' not in session:
        return redirect("/login")
    professor_nome = session.get('user_id')  # Obtém o nome de usuário da sessão
    user = Usuario.query.get_or_404(professor_nome)

    if user.tipo_perfil != 'professor':
        return redirect("/login")
    
    if request.method == "POST":
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        codigo_acesso = request.form.get('codigo_acesso')

        nova_turma = Turma(nome=nome, professor=professor, descricao=descricao, codigo_acesso=codigo_acesso)
        try:
            db.session.add(nova_turma)
            db.session.commit()
            return redirect("/professor")
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}"
    else:
        
        turmas = Turma.query.all()
        return render_template("professor_home.html", turmas=turmas, professor_nome=professor_nome)

    

#<---------Rotas Auxiliares da Turma---------->

@app.route("/acessar_turma", methods=["POST"])
def acessar_turma():
    codigo_acesso = request.form.get('codigo_turma')
    turma = Turma.query.filter_by(codigo_acesso=codigo_acesso).first()

    if turma:
        return redirect(f"/turma/{turma.id}")  # Redireciona para a página da turma com o ID correto
    else:
        flash("Código de turma inválido", "turma")
        return redirect("/aluno")

@app.route("/delete/<int:id>")
def delete(id: int):
    tarefa = Tarefa.query.get_or_404(id)
    arquivo_caminho = os.path.join(UPLOAD_FOLDER, tarefa.conteudo)

    try:
        if os.path.exists(arquivo_caminho):
            os.remove(arquivo_caminho)

        db.session.delete(tarefa)
        db.session.commit()
        # Redirecionar para a turma correta
        return redirect(f"/turma/{tarefa.turma_id}")
    except Exception as e:
        return f"ERROR: {e}"


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id: int):
    task = Tarefa.query.get_or_404(id)
    if request.method == "POST":
        task.conteudo = request.form['conteudo']  # Corrigir o nome do campo se necessário
        try:
            db.session.commit()
            return redirect(f"/turma/{task.turma_id}")
        except Exception as e:
            return f"ERROR: {e}"
    else:
        return render_template("edit.html", task=task)
    
# Rota para download dos arquivos
@app.route('/uploads/<path:filename>')
def download_file(filename):
    caminho_completo = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))
    return send_from_directory(caminho_completo, filename, as_attachment=True)

#<---------Rotas Auxiliares da Turma_Professor---------->

# Rota para excluir uma turma
@app.route("/delete_turma/<int:id>")
def delete_turma(id: int):
    turma = Turma.query.get_or_404(id)

    try:
        # Remover a turma do banco de dados
        db.session.delete(turma)
        db.session.commit()
        return redirect("/professor")
    except Exception as e:
        return f"ERROR: {e}"

# Rota para editar uma turma
@app.route("/edit_turma/<int:id>", methods=["GET", "POST"])
def edit_turma(id: int):
    turma = Turma.query.get_or_404(id)
    if request.method == "POST":
        turma.nome = request.form.get('nome')
        turma.professor = request.form.get('professor')
        turma.descricao = request.form.get('descricao')

        try:
            db.session.commit()
            return redirect("/professor")
        except Exception as e:
            return f"ERROR: {e}"
    else:
        return render_template("edit_turma.html", turma=turma)


#<---------Rotas Auxiliares do Login---------->
@app.route("/cadastro", methods=["POST"])
def cadastro():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    tipo_perfil = request.form.get("tipo_perfil")
    
    # Verificar se o email já existe
    if Usuario.query.filter_by(email=email).first():
        flash("Email já cadastrado. Tente um email diferente!", "cadastro")
        return redirect("/login")

    # Verificar se o nome de usuário já existe
    if Usuario.query.filter_by(username=username).first():
        flash("Nome de usuário já cadastrado. Escolha um nome diferente!", "cadastro")
        return redirect("/login")

    if tipo_perfil == "aluno":
        matricula = request.form.get("matricula")
        # Verificar se a matrícula já existe
        if Aluno.query.filter_by(matricula=matricula).first():
            flash("Matrícula já cadastrada. Tente uma matrícula diferente!", "cadastro")
            return redirect("/login")
        novo_aluno = Aluno(username=username, password=password, email=email, matricula=matricula)
        db.session.add(novo_aluno)
        
    elif tipo_perfil == "professor":
        novo_professor = Professor(username=username, email=email, password=password)
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
    password = request.form.get("password")

    user = Usuario.query.filter_by(email=email, password=password).first()

    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['tipo_perfil'] = user.tipo_perfil

        if user.tipo_perfil == 'aluno':
            return redirect("/aluno")
        elif user.tipo_perfil == 'professor':
            return redirect("/professor")
    else:
        flash("Usuário ou senha inválidos", "login")
        return redirect("/login")
    

if __name__ == "__main__":

    app.run(debug=True)