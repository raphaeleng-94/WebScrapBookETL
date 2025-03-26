import requests
from bs4 import BeautifulSoup
import os
import time
import logging
import psycopg2
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from logging import basicConfig, getLogger

#----------------------------------------------
# Configuração do Logfire
import logfire
logfire.configure()
basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = getLogger(__name__)
logger.setLevel(logging.INFO)
logfire.instrument_requests()
logfire.instrument_sqlalchemy()

#----------------------------------------------
# Configuração do logging
basicConfig(level=logging.INFO)

# Importar a base e livros do banco.py
from banco import Base, Livro
# Carrega as variáveis de ambiente
load_dotenv()

# Lê as variáveis separadas do arquivo .env (sem SSL)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Cria o motor do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Cria o sessionmaker
SessionLocal = sessionmaker(bind=engine)

def criar_tabela():
    # Cria a base
    Base.metadata.create_all(engine)
    logger.info("Tabela criada|verificada com sucesso")

base_url = "https://books.toscrape.com/catalogue/"
url = "https://books.toscrape.com/catalogue/page-1.html"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0"
}

# Dicionário para converter a classificação em texto para número de estrelas
estrelas_dict = {
    'One': '1 estrela',
    'Two': '2 estrelas',
    'Three': '3 estrelas',
    'Four': '4 estrelas',
    'Five': '5 estrelas'
}

# Lista para armazenar os dados dos livros
livros = []

def buscar_categoria(link):
    """Acessa o link do livro e busca a categoria"""
    try:
        site = requests.get(link, headers=headers)
        soup = BeautifulSoup(site.content, "html.parser")
        categoria = soup.find('ul', {'class': 'breadcrumb'}).find_all('a')[2].text.strip()
        return categoria
    except Exception as e:
        return "Categoria desconhecida"

def buscar_livros(soup):
    """Busca os livros na página atual"""
    for livro in soup.find_all('article', {'class': 'product_pod'}):
        # Título
        titulo = livro.find('h3').find('a')['title']

        # Classificação em estrelas
        estrelas = livro.find('p', {'class': 'star-rating'})
        if estrelas:
            classificacao = estrelas['class'][1]
            classificacao = estrelas_dict.get(classificacao, "Sem avaliação")
        else:
            classificacao = "Sem avaliação"

        # Preço
        preco = livro.find('p', {'class': 'price_color'}).text.strip()

        # Estoque
        estoque = livro.find('p', {'class': 'instock availability'}).text.strip()

        # Link para o livro
        link = base_url + livro.find('h3').find('a')['href']

        # Buscar categoria
        categoria = buscar_categoria(link)

        # Adiciona os dados à lista de livros
        livros.append((titulo, classificacao, categoria, preco, estoque))

    return livros

def proximapagina(soup):
    """Busca a próxima página de livros"""
    next_page = soup.find('li', {'class':'next'})
    if next_page:
        prox = next_page.find('a', href=True)
        if prox:
            return base_url + prox['href']
    return None

def transform_dados_livros(dados):
    """Transforma os dados de livros para o formato correto"""
    resultados = []
    for dado in dados:
        titulo = dado[0]
        classificacao = dado[1]
        categoria = dado[2]
        preco = dado[3].replace('£', '').replace(',', '.')  # Remove o símbolo de libra e trata a vírgula
        estoque = dado[4]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        dados_transformados = {
            "titulo": titulo,
            "classificacao": classificacao,
            "categoria": categoria,
            "preco": float(preco),  # Converte para número
            "estoque": estoque,
            "timestamp": timestamp
        }
        resultados.append(dados_transformados)

    return resultados

def salvar_dados_postgres(dados):
    """Salva os dados no banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        cur = conn.cursor()

        for dado in dados:
            titulo = dado['titulo']
            classificacao = dado['classificacao']
            categoria = dado['categoria']
            preco = dado['preco']
            estoque = dado['estoque']
            timestamp = dado['timestamp']
            
            # Verificando o comprimento das strings
            if len(titulo) > 250:
                logger.warning(f"Título excedendo limite de 250 caracteres: {titulo}")
            if len(classificacao) > 250:
                logger.warning(f"Classificação excedendo limite de 250 caracteres: {classificacao}")
            if len(categoria) > 250:
                logger.warning(f"Categoria excedendo limite de 250 caracteres: {categoria}")
            
            query = """
                INSERT INTO estoque_livros (titulo, classificacao, categoria, preco, estoque, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (titulo, categoria) DO NOTHING;
            """
            cur.execute(query, (titulo, classificacao, categoria, preco, estoque, timestamp))
        
        conn.commit()  # Faz o commit após todos os inserts
        logger.info(f"{len(dados)} registros salvos com sucesso!")

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Erro ao salvar dados no banco: {e}")

if __name__ == "__main__":
    criar_tabela()
    logger.info("Iniciando o pipeline com atualização a cada 15 segundos...(CTRL+C para interromper)")
    
    while url:
        try:
            site = requests.get(url, headers=headers)
            soup = BeautifulSoup(site.content, "html.parser")
            
            # Extração dos dados    
            dados = buscar_livros(soup)
            if dados:
                dados_transformados = transform_dados_livros(dados)
                salvar_dados_postgres(dados_transformados)
        
            # Atualiza a URL para a próxima página
            url = proximapagina(soup)

            time.sleep(15)

        except KeyboardInterrupt:
            logger.info("\nPipeline interrompido pelo usuário")
            break
        except Exception as e:
            logger.info(f"\nErro ao processar dados: {e}")
            time.sleep(15)
