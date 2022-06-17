import os

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import dotenv
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from marshmallow import Schema, fields
from flask_apispec import FlaskApiSpec, marshal_with, doc

dotenv.load_dotenv()

db_user = os.environ.get('DB_USERNAME')
db_pass = os.environ.get('DB_PASSWORD')
db_hostname = os.environ.get('DB_HOSTNAME')
db_name = os.environ.get('DB_NAME')

DB_URI = 'mysql+pymysql://{db_username}:{db_password}@{db_host}/{database}'.format(db_username=db_user, db_password=db_pass, db_host=db_hostname, database=db_name)

engine = create_engine(DB_URI, echo=True)

app = Flask(__name__)
docs = FlaskApiSpec(app)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    cellphone = db.Column(db.String(13), unique=True, nullable=False)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class StudentSchema(Schema):
    id = fields.Integer()
    name = fields.Str()
    email = fields.Str()
    age = fields.Integer()
    cellphone = fields.Str()


@app.route('/', methods=['GET'])
@doc(
    tags=['common'],
    description='main page',
    responses={
        200: {"description": "Ok"},
        500: {"description": "Server error"},
    },
)
def home():
    return '<p>Hello from students API!</p>', 200


@app.route('/api-json', methods=['common'])
def api_doc_json():
    return docs.swagger_json(), 200


@app.route('/api', methods=['GET'])
def api_doc_ui():
    return docs.swagger_ui()


@app.route('/api/health-check/ok', methods=['GET'])
@doc(
    tags=['common'],
    description='check health ok',
    responses={
        200: {"description": "Ok"},
        500: {"description": "Server error"},
    },
)
def api_health_ok():
    return 'Ok', 200


@app.route('/api/health-check/bad', methods=['GET'])
@doc(
    tags=['common'],
    description='check health bad',
    responses={
        500: {"description": "Server error"},
    },
)
def api_health_bad():
    return 'Fail', 500


@app.route('/api/students', methods=['GET'])
@doc(
    tags=['students'],
    description='Get list of all students',
    responses={
        200: {"description": "Ok"},
    },
)
@marshal_with(StudentSchema(many=True))
def get_all_students():
    students = Student.get_all()
    student_list = StudentSchema(many=True)
    response = student_list.dump(students)
    return response, 200


@doc(
    tags=['students'],
    description='Get one student by id',
    responses={
        200: {"description": "Ok"},
        500: {"description": "Server error"},
    },
)
@marshal_with(StudentSchema)
@app.route('/api/students/get/<int:id>', methods=['GET'])
def get_student(id):
    student_info = Student.get_by_id(id)
    serializer = StudentSchema()
    response = serializer.dump(student_info)
    return response, 200


@app.route('/api/students/add', methods=['POST'])
@doc(
    tags=['students'],
    description='Get one student by id',
    responses={
        200: {"description": "Ok"},
        500: {"description": "Server error"},
    },
)
@marshal_with(StudentSchema)
def add_student():
    json_data = request.get_json()
    new_student = Student(
        name=json_data.get('name'),
        email=json_data.get('email'),
        age=json_data.get('age'),
        cellphone=json_data.get('cellphone')
    )
    new_student.save()
    serializer = StudentSchema()
    data = serializer.dump(new_student)
    return data, 201


@app.route('/api/students/modify/<int:id>', methods=['PATCH'])
@doc(
    tags=['students'],
    description='Modify student data',
    responses={
        200: {"description": "Ok"},
        404: {"description": "Student not found"},
        500: {"description": "Server error"},
    },
)
@marshal_with(StudentSchema)
def patch_student(id):
    student = Student.get_by_id(id)
    if not student:
        return 'Student not found', 404

    json_data = request.get_json()

    if json_data.get('name') is not None:
        student.name = json_data.get('name')
    if json_data.get('email') is not None:
        student.email = json_data.get('email')
    if json_data.get('age') is not None:
        student.age = json_data.get('age')
    if json_data.get('cellphone') is not None:
        student.cellphone = json_data.get('cellphone')

    try:
        student.save()
    except Exception:
        return 'Fail saving to db', 500

    serializer = StudentSchema()
    response = serializer.dump(student)
    return response, 200


@app.route('/api/students/change/<int:id>', methods=['PUT'])
@doc(
    tags=['students'],
    description='Change all student data',
    responses={
        200: {"description": "Ok"},
        404: {"description": "Student not found"},
        500: {"description": "Server error"},
    },
)
@marshal_with(StudentSchema)
def put_student(id):
    student = Student.get_by_id(id)
    if not student:
        return 'Student not found', 404

    json_data = request.get_json()

    student.name = json_data.get('name', '')
    student.email = json_data.get('email', '')
    student.age = json_data.get('age', 0)
    student.cellphone = json_data.get('cellphone', '')

    try:
        student.save()
    except Exception:
        return 'Fail saving to db', 500

    serializer = StudentSchema()
    response = serializer.dump(student)
    return response, 200


@app.route('/api/students/delete/<int:id>', methods=['DELETE'])
@doc(
    tags=['students'],
    description='Delete student',
    responses={
        200: {"description": "Ok"},
        404: {"description": "Student not found"},
        500: {"description": "Server error"},
    },
)
def delete_student(id):
    student = Student.get_by_id(id)
    if not student:
        return 'Student not found', 404

    try:
        student.delete()
    except Exception:
        return 'Fail deleting from db', 500

    return 'deleted', 200


docs.register(home)
docs.register(api_health_ok)
docs.register(api_health_bad)
docs.register(get_all_students)
docs.register(get_student)
docs.register(add_student)
docs.register(patch_student)
docs.register(put_student)
docs.register(delete_student)


if __name__ == '__main__':
    if not database_exists(engine.url):
        create_database(engine.url)
    db.create_all()
    app.run(port=8090, debug=True)
