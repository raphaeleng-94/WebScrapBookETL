import requests
from bs4 import BeautifulSoup
import os
import time
import requests
import logfire
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from logging import basicConfig, getLogger

#----------------------------------------------
# Configuração do Logfire
logfire.configure()
basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = getLogger(__name__)
logger.setLevel(logging.INFO)
logfire.instrument_requests()
logfire.instrument_sqlalchemy()

#----------------------------------------------
# Configuração do logging
basicConfig(level=logging.INFO)
logger = getLogger(__name__)

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

site = requests.get(url, headers=headers)

soup = BeautifulSoup(site.content, "html.parser")

# Dicionário para converter a classificação em texto para número de estrelas
estrelas_dict = {
    'One': '1 estrela',
    'Two': '2 estrelas',
    'Three': '3 estrelas',
    'Four': '4 estrelas',
    'Five': '5 estrelas'
}

livros = []

def buscar_categoria(link):
    """ Acessa o link do livro e busca a categoria """
    try:
        site = requests.get(link, headers=headers)
        soup = BeautifulSoup(site.content, "html.parser")
        categoria = soup.find('ul', {'class': 'breadcrumb'}).find_all('a')[2].text.strip()
        return categoria
    except Exception as e:
        return "Categoria desconhecida"

def buscar_livros(soup):
    """ Busca os livros na página atual """
    for livro in soup.find_all('article', {'class': 'product_pod'}):
        # Título
        titulo = livro.find('h3').find('a')['title']
        
        # Classificação em estrelas
        estrelas = livro.find('p', {'class': 'star-rating'})
        if estrelas:
            # Pega a segunda palavra da classe (ex: "star-rating Three" → Three)
            classificacao = estrelas['class'][1]
            classificacao = estrelas_dict.get(classificacao, "Sem avaliação")
        else:
            classificacao = "Sem avaliação"
        
        #Buscar preço
        preco = soup.find('p', {'class': 'price_color'}).text.strip()

        #Buscar estoque
        estoque = soup.find('p', {'class': 'instock availability'}).text.strip()

        #Link para o livro
        link = base_url + livro.find('h3').find('a')['href']

        #Buscar categoria
        categoria = buscar_categoria(link)  

        # Adiciona à lista
        livros.append((titulo, classificacao, categoria, preco, estoque))
    return livros
def proximapagina(soup):
    next_page = soup.find('li', {'class':'next'})
    if next_page:
        prox = next_page.find('a', href=True)
        if prox:
            return base_url + prox['href']
    return None

while url:
    site = requests.get(url, headers=headers)
    soup = BeautifulSoup(site.content, "html.parser")
    # Busca os livros na página atual
    dados = buscar_livros(soup)
    # Busca a próxima página
    url = proximapagina(soup)

def transform_dados_livros(dados):
    titulo = dados[0]
    classificacao = dados[1]
    categoria = dados[2]
    # Remove o símbolo de moeda e converte para float
    preco = float(dados[3].replace('£', ''))
    
    estoque = dados[4]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dados_transformados = {
        "titulo": titulo,
        "classificacao": classificacao,
        "categoria": categoria,
        "preco": preco,
        "estoque": estoque,
        "timestamp": timestamp
    }

    return dados_transformados

def salvar_dados_postgres(dados):
    """Salva os dados no banco de dados PostgreSQL"""
    session = SessionLocal()
    novo_registro = Livro(**dados)
    session.add(novo_registro)
    session.commit()
    session.close()
    logger.info(f"[{dados['timestamp']}] Dados salvos com sucesso no PostgreSQL!")

if __name__ == "__main__":
    criar_tabela()
    logger.info("Iniciando o pipeline com atualização a cada 15 segundos...(CTRL+C para interromper)")
    while True:
        try:
            # Extração dos dados
            dados = buscar_livros(soup)
            if dados:
                dados_transformados = transform_dados_livros(dados)
                logger.info("Dados Tratados:", dados_transformados)
                salvar_dados_postgres(dados_transformados)

            #Atualiza a URL para a próxima página
            url = proximapagina(soup)

            time.sleep(15)
        except KeyboardInterrupt:
            logger.info("\nPipeline interrompido pelo usuário")
            break
        except Exception as e:
            logger.info(f"\nErro ao processar dados: {e}")
            time.sleep(15)

"""print(f"Total de livros encontrados: {len(livros)}\n")
for i, (titulo, classificacao, categoria, preco, estoque) in enumerate(livros, 1):
    print(f"{i}. {titulo} - {classificacao} - {categoria} - {preco} - {estoque}")"""








