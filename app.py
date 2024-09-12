from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    conteudo = db.Column(db.String(100), nullable = False)
    feito = db.Column(db.Integer, default = 0)
    criado = db.Column(db.DateTime, default = datetime.utcnow)

    def __repr__(self) -> str:
        return f"Tarefa {self.id}"

with app.app_context():
    db.create_all()
    
@app.route("/", methods = ["POST","GET"])
def index():
    if request.method == "POST":
        conteudo_tarefa = request.form.get('conteudo')
        nova_tarefa = Tarefa(conteudo=conteudo_tarefa)
        try:
            db.session.add(nova_tarefa)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}"
    else:
        tarefas = Tarefa.query.order_by(Tarefa.criado).all()
        return render_template("professor.html", tarefas = tarefas)

@app.route("/delete/<int:id>")
def delete(id:int):
    deletar = Tarefa.query.get_or_404(id)
    try:
        db.session.delete(deletar)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        return f"ERROR: {e}"

@app.route("/edit/<int:id>", methods= ["GET","POST"])
def edit(id:int):
    task = Tarefa.query.get_or_404(id)
    if request.method == "POST":
        task.conteudo = request.form['conteudo']
        try:
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return f"ERROR: {e}"
    else:
        return render_template("edit.html", task = task)




if __name__ == "__main__":

    app.run(debug=True)