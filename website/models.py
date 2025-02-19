from flask_login import UserMixin
from sqlalchemy.sql import func
from . import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String(1000), default=None)
    phone = db.Column(db.String(1000), unique=True, default=None)
    admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    confirmed = db.Column(db.Boolean, default=False)
    user_appointments = db.Column(db.Integer, default=0)
    cancelled = db.Column(db.Integer, default=0)


class Appointments(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Time, nullable=False)
    not_cancelled = db.Column(db.Boolean, default=True)
    cancelled_by = db.Column(db.String(1000))
    cancelled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=func.now())
    user = db.relationship("User", backref="appointments")


class Details(db.Model):
    __tablename__ = "details"

    id = db.Column(db.Integer, primary_key=True)
    motive_id = db.Column(db.Integer)
    detail = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, server_default=func.now())
    user = db.relationship("User", backref="details")


class SecretCodes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, server_default=func.now())
    used = db.Column(db.Boolean, default=False)
    user = db.relationship("User", backref='secret_codes')