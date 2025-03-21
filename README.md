# WebScrapBookETL

Este projeto implementa um pipeline de ETL (Extract, Transform, Load) utilizando web scraping em Python para coletar dados de livros de um site específico, realizar o tratamento dos dados e armazená-los em um banco de dados PostgreSQL.

## Descrição do Projeto

O pipeline consiste em três etapas principais:

1. **Extração (Extract)**: 
   - Realiza web scraping de um site específico de livros
   - Coleta informações relevantes como título, autor, preço, descrição, etc.

2. **Transformação (Transform)**:
   - Limpa e processa os dados coletados
   - Remove dados duplicados ou inválidos
   - Formata os dados para o padrão desejado

3. **Carregamento (Load)**:
   - Armazena os dados processados em um banco de dados PostgreSQL
   - Mantém um histórico das extrações realizadas

## Tecnologias Utilizadas

- Python
- BeautifulSoup4/Selenium para web scraping
- Pandas para manipulação de dados
- PostgreSQL para armazenamento
- SQLAlchemy para ORM

## Requisitos

- Python 3.x
- PostgreSQL instalado e configurado
- Bibliotecas Python listadas em `requirements.txt`

## Estrutura do Projeto

```
WebScrapBookETL/
├── src/
│   ├── scraper/
│   ├── transformer/
│   └── loader/
├── config/
├── data/
├── requirements.txt
└── README.md
```

## Como Usar

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure as credenciais do banco de dados
4. Execute o pipeline: `python main.py`

## Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para submeter pull requests.

## Licença

Este projeto está sob a licença MIT. # WebScrapBookETL
