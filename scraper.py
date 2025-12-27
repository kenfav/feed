import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

def scrape_site():
    # URL do Hacker News (Site super leve e permissivo)
    url = "https://news.ycombinator.com/"
    
    print(f"Tentando acessar: {url}")
    
    # Headers básicos
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; ScraperTest/1.0)'
    }

    try:
        res = requests.get(url, headers=headers, timeout=30)
        res.raise_for_status()
        print("Conexão bem sucedida!")
    except Exception as e:
        print(f"Erro fatal de conexão: {e}")
        return

    soup = BeautifulSoup(res.text, 'lxml')
    
    # Configura o Feed
    fg = FeedGenerator()
    fg.title('Hacker News - TESTE')
    fg.link(href=url, rel='alternate')
    fg.description('Feed de teste para validar o GitHub Actions')
    fg.language('en')

    # No Hacker News, cada linha de notícia tem a classe 'athing'
    # Vamos pegar apenas as 10 primeiras para teste
    items = soup.select('.athing')[:10]
    
    if not items:
        print("Aviso: Conectou, mas não achou os itens (seletor CSS pode estar errado).")
        # Debug
        print(res.text[:500])
    
    count = 0
    for element in items:
        fe = fg.add_entry()
        
        # 1. Título e Link
        # A estrutura é <span class="titleline"><a href="...">Titulo</a></span>
        title_tag = element.select_one('.titleline > a')
        
        if not title_tag:
            continue
            
        title = title_tag.get_text(strip=True)
        link = title_tag['href']
        
        # Correção se for link relativo
        if not link.startswith('http'):
            link = 'https://news.ycombinator.com/' + link
            
        fe.title(title)
        fe.link(href=link)
        fe.id(link)
        fe.published(datetime.datetime.now(datetime.timezone.utc))
        
        count += 1

    # Salva o arquivo XML
    fg.rss_file('feed.xml')
    print(f"SUCESSO TOTAL: Feed gerado com {count} itens!")

if __name__ == "__main__":
    scrape_site()
