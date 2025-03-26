from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Float, String, Integer, DateTime, UniqueConstraint
from datetime import datetime

# Cria a classe Base do SQLAlchemy (na versão 2.x)
Base = declarative_base()

class Livro(Base):
    __tablename__ = "estoque_livros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(250), nullable=False) # até 250 caracteres
    classificacao = Column(String(250), nullable=False) # até 250 caracteres
    categoria = Column(String(250), nullable=False) # até 250 caracteres
    preco = Column(Float, nullable=False)
    estoque = Column(String(250), nullable=False) # até 250 caracteres
    timestamp = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint('titulo', 'categoria', name='uix_titulo_categoria'),
    )