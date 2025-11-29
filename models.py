# models.py - SQLAlchemy models and helper DB functions
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///bank.db', echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=True)
    balance = Column(Float, default=0.0)
    transactions = relationship("Transaction", back_populates="user")

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String(20))  # deposit, withdraw, transfer_out, transfer_in
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    note = Column(String(255), nullable=True)
    user = relationship("User", back_populates="transactions")

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return Session()
