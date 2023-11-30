from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    last_period_date = db.Column(db.Date, nullable=True)
    average_period_length = db.Column(db.Integer, nullable=True)
    average_cycle_length = db.Column(db.Integer, nullable=True)

    # Add a relationship to access cycle data and symptom data directly
    cycle_data = db.relationship('CycleData', backref='user', lazy=True, cascade='all, delete-orphan')
    symptom_data = db.relationship('SymptomData', backref='user', lazy=True, cascade='all, delete-orphan')


class CycleData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    is_predicted = db.Column(db.Boolean, nullable=False, server_default='0')

    # Add a constructor to validate dates
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'end_date' in kwargs and kwargs['start_date'] > kwargs['end_date']:
            raise ValueError("Start date must be before end date.")
        if 'is_predicted' not in kwargs:
            self.is_predicted = False


class SymptomData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    flow = db.Column(db.String(50))
    medicine = db.Column(db.String(100))
    intercourse_protection = db.Column(db.String(50))
    symptoms = db.Column(db.String(200))  # You can store a comma-separated list of symptoms
    mood = db.Column(db.String(100))
    notes = db.Column(db.Text)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ReportInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, user_id, file_path, password):
        self.user_id = user_id
        self.file_path = file_path
        self.password_hash = generate_password_hash(password)


