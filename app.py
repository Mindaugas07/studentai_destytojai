from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, InputRequired
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

import os
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


basedir = os.path.abspath(os.path.dirname(__file__))
print(basedir)

app = Flask(__name__)

app.config["SECRET_KEY"] = "dfgsfdgsdfgsdfgsdf"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "data.sqlite?check_same_thread=False"
)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


association_table = db.Table(
    "association",
    db.metadata,
    db.Column("studentas_id", db.Integer, db.ForeignKey("studentas.id")),
    db.Column("paskaita_id", db.Integer, db.ForeignKey("paskaita.id")),
)


class Studentas(db.Model):
    __tablename__ = "studentas"
    id = db.Column(db.Integer, primary_key=True)
    vardas = db.Column("Vardas", db.String)
    pavarde = db.Column("Pavardė", db.String)
    paskaitos = db.relationship(
        "Paskaita", secondary=association_table, back_populates="studentai"
    )


class Paskaita(db.Model):
    __tablename__ = "paskaita"
    id = db.Column(db.Integer, primary_key=True)
    vardas = db.Column("Vardas", db.String)
    savaites_diena = db.Column("Savaites diena", db.String)
    studentai = db.relationship(
        "Studentas", secondary=association_table, back_populates="paskaitos"
    )
    destytojas_id = db.Column(db.Integer, db.ForeignKey("destytojas.id"))
    destytojas = db.relationship(
        "Destytojas", cascade="all, delete", passive_deletes=True
    )


class Destytojas(db.Model):
    __tablename__ = "destytojas"
    id = db.Column(db.Integer, primary_key=True)
    vardas = db.Column("Vardas", db.String)
    pavarde = db.Column("Pavardė", db.String)
    paskaitos = db.relationship("Paskaita")


def get_pk(obj):
    return str(obj)


def paskaita_query():
    return Paskaita.query


def destytojas_query():
    return Destytojas.query


with app.app_context():
    db.create_all()

    class StudentasForm(FlaskForm):
        vardas = StringField("Vardas", [DataRequired()])
        pavarde = StringField("Pavardė", [DataRequired()])
        paskaitos = QuerySelectMultipleField(
            query_factory=Paskaita.query.all, get_label="vardas", get_pk=get_pk
        )
        submit = SubmitField("Įvesti")

    class PaskaitaForm(FlaskForm):
        vardas = StringField("Vardas", [DataRequired()])
        savaites_diena = StringField("Savaites diena", [DataRequired()])
        studentai = QuerySelectMultipleField(
            query_factory=Studentas.query.all, get_label="vardas", get_pk=get_pk
        )
        destytojas = QuerySelectField(
            query_factory=destytojas_query,
            allow_blank=True,
            get_label="vardas",
            get_pk=lambda obj: str(obj),
        )
        print(destytojas)
        submit = SubmitField("Įvesti")

    class DestytojasForm(FlaskForm):
        vardas = StringField("Vardas", [DataRequired()])
        pavarde = StringField("Pavardė", [DataRequired()])
        submit = SubmitField("Įvesti")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/studentai")
def students():
    try:
        visi_studentai = Studentas.query.all()
    except:
        visi_studentai = []
    return render_template("studentai.html", visi_studentai=visi_studentai)


@app.route("/paskaitos")
def paskaitos():
    try:
        visos_paskaitos = Paskaita.query.all()
    except:
        visos_paskaitos = []
    return render_template("paskaitos.html", visos_paskaitos=visos_paskaitos)


@app.route("/destytojai")
def destytojai():
    try:
        visi_destytojai = Destytojas.query.all()
    except:
        visi_destytojai = []
    return render_template("destytojai.html", visi_destytojai=visi_destytojai)


@app.route("/naujas_studentas", methods=["GET", "POST"])
def new_student():
    db.create_all()
    forma = StudentasForm()
    if forma.validate_on_submit():
        naujas_studentas = Studentas(
            vardas=forma.vardas.data, pavarde=forma.pavarde.data
        )
        for paskaita in forma.paskaitos.data:
            priskirta_paskaita = Paskaita.query.get(paskaita.id)
            naujas_studentas.paskaitos.append(priskirta_paskaita)
        db.session.add(naujas_studentas)
        db.session.commit()
        return redirect(url_for("students"))
    return render_template("prideti_studenta.html", form=forma)


@app.route("/nauja_paskaita", methods=["GET", "POST"])
def new_lecture():
    db.create_all()
    forma = PaskaitaForm()
    if forma.validate_on_submit():
        nauja_paskaita = Paskaita(
            vardas=forma.vardas.data, savaites_diena=forma.savaites_diena.data
        )
        for studentas in forma.studentai.data:
            priskirtas_studentas = Studentas.query.get(studentas.id)
            nauja_paskaita.studentai.append(priskirtas_studentas)
        # for destytojas in forma.destytojai.data:
        destytojas = forma.destytojas.data
        priskirtas_destytojas = Destytojas.query.get(destytojas.id)
        print(priskirtas_destytojas)
        nauja_paskaita.destytojas = priskirtas_destytojas
        db.session.add(nauja_paskaita)
        db.session.commit()
        return redirect(url_for("paskaitos"))
    return render_template("prideti_paskaita.html", form=forma)


@app.route("/naujas_destytojas", methods=["GET", "POST"])
def new_teacher():
    db.create_all()
    forma = DestytojasForm()
    if forma.validate_on_submit():
        naujas_destytojas = Destytojas(
            vardas=forma.vardas.data, pavarde=forma.pavarde.data
        )
        db.session.add(naujas_destytojas)
        db.session.commit()
        return redirect(url_for("destytojai"))
    return render_template("prideti_destytoja.html", form=forma)


@app.route("/delete_student/<int:id>")
def delete_student(id):
    uzklausa = Studentas.query.get(id)
    db.session.delete(uzklausa)
    db.session.commit()
    return redirect(url_for("students"))


@app.route("/student_update/<int:id>", methods=["GET", "POST"])
def student_update(id):
    form = StudentasForm()
    studentas = Studentas.query.get(id)
    if form.validate_on_submit():
        studentas.vardas = form.vardas.data
        studentas.pavarde = form.pavarde.data
        db.session.commit()
        return redirect(url_for("students"))
    return render_template("update_student.html", form=form, studentas=studentas)


@app.route("/delete_teacher/<int:id>")
def delete_teacher(id):
    uzklausa = Destytojas.query.get(id)
    db.session.delete(uzklausa)
    db.session.commit()
    return redirect(url_for("destytojai"))


@app.route("/teacher_update/<int:id>", methods=["GET", "POST"])
def teacher_update(id):
    form = DestytojasForm()
    destytojas = Destytojas.query.get(id)
    if form.validate_on_submit():
        destytojas.vardas = form.vardas.data
        destytojas.pavarde = form.pavarde.data
        db.session.commit()
        return redirect(url_for("destytojai"))
    return render_template("update_teacher.html", form=form, destytojas=destytojas)


@app.route("/delete_lecture/<int:id>")
def delete_lecture(id):
    uzklausa = Paskaita.query.get(id)
    db.session.delete(uzklausa)
    db.session.commit()
    return redirect(url_for("paskaitos"))


@app.route("/lecture_update/<int:id>", methods=["GET", "POST"])
def lecture_update(id):
    form = PaskaitaForm()
    paskaita = Paskaita.query.get(id)
    if form.validate_on_submit():
        paskaita.vardas = form.vardas.data
        paskaita.savaites_diena = form.savaites_diena.data
        db.session.commit()
        return redirect(url_for("paskaitos"))
    return render_template("update_lecture.html", form=form, paskaita=paskaita)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
