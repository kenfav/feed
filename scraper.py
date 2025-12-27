import cloudscraper
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import os

def scrape_site():
    url = "https://www.jw.org/en/whats-new/"
    
    # Cloudscraper cria um navegador virtual completo
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    print(f"Tentando acessar: {url} via GitHub Actions...")

    try:
        res = scraper.get(url, timeout=30)
        res.raise_for_status()
        print(f"Sucesso! Baixado {len(res.text)} bytes.")
    except Exception as e:
        print(f"Erro fatal: {e}")
        return

    soup = BeautifulSoup(res.text, 'lxml')
    
    # Configura o Feed RSS
    fg = FeedGenerator()
    fg.title('JW.org - What\'s New')
    fg.link(href=url, rel='alternate')
    fg.description('Latest updates from JW.org')
    fg.language('en')

    # Seleciona os itens
    items = soup.select('.synopsis')
    print(f"Encontrados {len(items)} itens.")

    for element in items:
        fe = fg.add_entry()
        
        # 1. Título e Link
        title_tag = element.select_one('h3 a')
        if not title_tag: continue
            
        title = title_tag.get_text(strip=True)
        link = title_tag['href']
        
        # Corrige link relativo
        if not link.startswith('http'):
            link = 'https://www.jw.org' + link
            
        fe.title(title)
        fe.link(href=link)
        fe.id(link)

        # 2. Data
        date_tag = element.select_one('.meta.pubDate')
        if date_tag:
            try:
                # JW usa formato YYYY-MM-DD, o feedgen aceita string direta às vezes
                # mas vamos deixar sem timezone específico para simplificar ou usar UTC
                fe.published(datetime.datetime.now(datetime.timezone.utc))
            except:
                pass

        # 3. Imagem
        img_src = ''
        img_tag = element.select_one('.jsRespImg')
        if img_tag:
            if img_tag.has_attr('data-img-size-md'):
                img_src = img_tag['data-img-size-md']
            elif img_tag.has_attr('data-img-size-lg'):
                img_src = img_tag['data-img-size-lg']
            elif img_tag.has_attr('data-img-size-xs'):
                img_src = img_tag['data-img-size-xs']

        # 4. Descrição
        context = element.select_one('.contextTitle')
        context_txt = context.get_text(strip=True) if context else ""
        
        desc = element.select_one('.desc')
        desc_txt = desc.get_text(strip=True) if desc else ""

        # HTML do Item
        content = ""
        if img_src:
            content += f'<img src="{img_src}" style="width:100%; max-width:600px;" /><br>'
        if context_txt:
            content += f'<small><b>{context_txt}</b></small><br>'
        content += desc_txt
        
        fe.content(content, type='CDATA')

    # Salva o arquivo XML
    fg.rss_file('feed.xml')
    print("Arquivo feed.xml gerado com sucesso.")

if __name__ == "__main__":
    scrape_site()
