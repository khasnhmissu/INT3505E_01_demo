from datetime import date
from app.extension import db

class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String)
    is_available = db.Column(db.Boolean, default=True)

    loans = db.relationship("Loan", back_populates="book")
    
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default="user")
    
    loans = db.relationship("Loan", back_populates="user")

class Loan(db.Model):
    __tablename__ = "loans"

    loan_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    checkout_date = db.Column(db.Date, nullable=False, default=date.today)
    return_date = db.Column(db.Date)

    book = db.relationship("Book", back_populates="loans")
    user = db.relationship("User", back_populates="loans")