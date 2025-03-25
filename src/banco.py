from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Float, String, Integer, DateTime
from datetime import datetime

# Cria a classe Base do SQLAlchemy (na versão 2.x)
Base = declarative_base()

class Livro(Base):
    __tablename__ = "estoque_livros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(50), nullable=False) # até 50 caracteres
    classificacao = Column(String(50), nullable=False) # até 50 caracteres
    categoria = Column(String(50), nullable=False) # até 50 caracteres
    preco = Column(Float, nullable=False)
    estoque = Column(String(50), nullable=False) # até 50 caracteres
    timestamp = Column(DateTime, default=datetime.now)
