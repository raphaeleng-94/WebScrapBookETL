import requests
from bs4 import BeautifulSoup

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

def buscar_preco(soup):
    """ Busca o preço do livro """
    try:
        preco = soup.find('p', {'class': 'price_color'}).text.strip()
        return preco
    except Exception as e:
        return "Preço desconhecido"

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
    buscar_livros(soup)
    # Busca a próxima página
    url = proximapagina(soup)

print(f"Total de livros encontrados: {len(livros)}\n")
for i, (titulo, classificacao, categoria, preco, estoque) in enumerate(livros, 1):
    print(f"{i}. {titulo} - {classificacao} - {categoria} - {preco} - {estoque}")








