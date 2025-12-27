import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import os

def scrape_site():
    url = "https://www.jw.org/en/whats-new/"
    
    # Headers OBRIGATÓRIOS para não levar erro 403/400
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.jw.org/'
    }

    try:
        # O requests usa HTTP/1.1 por padrão, o que é ótimo para evitar o erro do curl
        res = requests.get(url, headers=headers, timeout=30)
        res.raise_for_status() # Para se der erro
    except Exception as e:
        print(f"Erro ao baixar o site: {e}")
        return

    soup = BeautifulSoup(res.text, 'lxml')
    
    # Configura o Feed
    fg = FeedGenerator()
    fg.title('JW.org - What\'s New')
    fg.link(href=url, rel='alternate')
    fg.description('Latest updates from JW.org')
    fg.language('en')

    # Procura os itens (mesma lógica que usamos no RSS-Bridge)
    for element in soup.select('.synopsis'):
        fe = fg.add_entry()
        
        # 1. Título e Link
        title_tag = element.select_one('h3 a')
        if not title_tag:
            continue
            
        title = title_tag.get_text(strip=True)
        link = title_tag['href']
        if not link.startswith('http'):
            link = 'https://www.jw.org' + link
            
        fe.title(title)
        fe.link(href=link)
        fe.id(link) # ID único

        # 2. Data
        date_tag = element.select_one('.meta.pubDate')
        if date_tag:
            # Tenta converter para data, se falhar usa a atual
            fe.published(datetime.datetime.now(datetime.timezone.utc))

        # 3. Imagem
        img_src = ''
        img_tag = element.select_one('.jsRespImg')
        if img_tag:
            # Tenta pegar a imagem MD, LG ou XS
            if img_tag.has_attr('data-img-size-md'):
                img_src = img_tag['data-img-size-md']
            elif img_tag.has_attr('data-img-size-lg'):
                img_src = img_tag['data-img-size-lg']
            elif img_tag.has_attr('data-img-size-xs'):
                img_src = img_tag['data-img-size-xs']
            elif img_tag.has_attr('src'):
                img_src = img_tag['src']

        # 4. Contexto e Descrição
        context_tag = element.select_one('.contextTitle')
        context = context_tag.get_text(strip=True) if context_tag else ""
        
        desc_tag = element.select_one('.desc')
        desc = desc_tag.get_text(strip=True) if desc_tag else ""

        # Monta o HTML para o leitor de RSS
        content_html = ""
        if img_src:
            content_html += f'<img src="{img_src}" style="width:100%; max-width:600px; display:block;" /><br>'
        if context:
            content_html += f'<small style="text-transform:uppercase; color:gray;">{context}</small><br>'
        content_html += desc
        
        fe.content(content_html, type='CDATA')
        fe.description(desc)

    # Salva o arquivo XML
    fg.rss_file('feed.xml')
    print("Feed gerado com sucesso!")
    #Teste para rodar

if __name__ == "__main__":
    scrape_site()
