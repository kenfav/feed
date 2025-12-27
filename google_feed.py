import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

def gerar_feed_google():
    # URL do Tópico "World News" (US Edition)
    url = "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen"
    
    print(f"Acessando Google News: {url}")

    # Google News é MUITO chato com robôs. Precisamos de headers perfeitos.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://news.google.com/'
    }

    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Erro ao baixar: {e}")
        return

    soup = BeautifulSoup(r.text, 'lxml')
    
    # Configura o Feed
    fg = FeedGenerator()
    fg.title('Google News - World (US)')
    fg.link(href=url, rel='alternate')
    fg.description('Top stories from around the world via Google News')
    fg.language('en')

    # Google News organiza notícias dentro de tags <article>
    articles = soup.find_all('article')
    print(f"Encontrados {len(articles)} artigos.")

    count = 0
    for article in articles:
        fe = fg.add_entry()
        
        # 1. Título (Geralmente dentro de um <h4> ou <h3>)
        # Procuramos qualquer tag de título
        title_tag = article.find(['h4', 'h3', 'a'])
        if not title_tag: continue
        
        title = title_tag.get_text(strip=True)
        fe.title(title)

        # 2. Link
        # O link geralmente está na tag <a> com href começando com ./
        link_tag = article.find('a', href=True)
        if link_tag:
            href = link_tag['href']
            # O Google usa links relativos "./articles/...", precisamos corrigir
            if href.startswith('./'):
                href = href.replace('./', 'https://news.google.com/')
            
            fe.link(href=href)
            fe.id(href)

        # 3. Data (Tag <time>)
        time_tag = article.find('time')
        if time_tag and time_tag.has_attr('datetime'):
            fe.published(time_tag['datetime'])
        else:
            fe.published(datetime.datetime.now(datetime.timezone.utc))

        # 4. Imagem (A parte difícil)
        # A imagem geralmente está numa <figure> anterior ou dentro do artigo
        # Às vezes o article é só texto e a imagem está no article pai ou irmão
        img_src = ""
        
        # Tenta achar imagem dentro do próprio artigo
        img_tag = article.find('img')
        
        # Se não achou, tenta achar na div 'pai' (layout comum do Google)
        if not img_tag and article.parent:
            img_tag = article.parent.find('img')

        if img_tag:
            # O Google usa 'srcset' para alta qualidade e 'src' para baixa
            if img_tag.has_attr('srcset'):
                # Pega a maior imagem do srcset (o último item separado por espaço)
                srcset = img_tag['srcset'].split(' ')
                # Geralmente o formato é: url 1x, url 2x. Pegamos o penúltimo item.
                if len(srcset) >= 2:
                    img_src = srcset[-2] 
            elif img_tag.has_attr('src'):
                img_src = img_tag['src']
            
            # Corrige se a URL for relativa (raro em imagens do Google, mas possível)
            if img_src.startswith('/'):
                img_src = 'https://news.google.com' + img_src

        # 5. Fonte da Notícia (Nome do Jornal)
        # Geralmente é um div pequeno com texto (ex: CNN, BBC)
        source_div = article.find('div', {'class': lambda x: x and 'vr1PYe' in x}) # Tentativa por classe comum
        if not source_div:
            # Tenta pegar qualquer span/div pequeno que não seja o título
            pass 
            # (Omissão intencional pois é difícil acertar sem classes fixas)

        # 6. Conteúdo HTML
        content = ""
        if img_src:
            content += f'<img src="{img_src}" style="width:100%; max-width:600px; border-radius:8px;" /><br>'
        
        content += f'<p>Read full coverage on Google News</p>'
        
        fe.content(content, type='CDATA')
        
        count += 1
        # Limita a 30 notícias para não ficar gigante
        if count >= 30:
            break

    # Salva o arquivo
    fg.rss_file('google_world.xml', pretty=True)
    print("Sucesso! Arquivo 'google_world.xml' gerado.")

if __name__ == "__main__":
    gerar_feed_google()
