from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

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

    # Add a relationship to access cycle data directly
    cycle_data = db.relationship('CycleData', backref='user', lazy=True, cascade='all, delete-orphan')


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


