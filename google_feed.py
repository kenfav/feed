import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

def gerar_feed_google():
    # URL do Tópico "World News" (US Edition)
    url = "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen"
    
    print(f"Acessando Google News: {url}")

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Erro ao baixar: {e}")
        return

    soup = BeautifulSoup(r.text, 'lxml')

    
    fg = FeedGenerator()
    fg.title('Google News - World')
    fg.link(href=url, rel='alternate')
    fg.description('World News')
    fg.language('en')

    # Encontra os links de notícia
    links = soup.find_all('a', href=lambda x: x and x.startswith('./read/'))
    
    count = 0
    urls_vistas = set()

    for link_tag in links:
        # 1. TENTA EXTRAIR O TÍTULO PRIMEIRO
        # Seu log mostrou que o link bom tem "aria-label" e o ruim tem "aria-hidden"
        
        # Ignora links ocultos (os quadradinhos vazios)
        if link_tag.get('aria-hidden') == 'true':
            continue

        title = link_tag.get('aria-label')
        if not title:
            title = link_tag.get_text(strip=True)
            
        # Se não tem título nenhum, ignora e NÃO marca a URL como vista ainda
        if not title:
            continue

        # 2. AGORA verifica duplicatas (só para links válidos)
        href = link_tag['href'].replace('./', 'https://news.google.com/')
        
        if href in urls_vistas:
            continue
        urls_vistas.add(href)

        # 3. Busca Imagem (Figure Anterior)
        img_src = ""
        figure = link_tag.find_previous('figure')
        if figure:
            img = figure.find('img')
            if img:
                # Prioridade: srcset -> src
                if img.has_attr('srcset'):
                    parts = img['srcset'].split(' ')
                    if len(parts) >= 2: img_src = parts[-2]
                    else: img_src = img.get('src')
                else:
                    img_src = img.get('src')

                # Limpeza da URL
                if img_src and img_src.startswith('/'):
                    img_src = 'https://news.google.com' + img_src

        # 4. Data
        pub_date = datetime.datetime.now(datetime.timezone.utc)
        # Tenta achar <time> no pai ou no próximo elemento
        time_tag = None
        if link_tag.parent:
            time_tag = link_tag.parent.find('time')
        if not time_tag:
            time_tag = link_tag.find_next('time')
            
        if time_tag and time_tag.has_attr('datetime'):
            try: pub_date = time_tag['datetime']
            except: pass

        # 5. Adiciona Item
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=href)
        fe.id(href)
        fe.published(pub_date)

        content = ""
        if img_src:
            content += f'<img src="{img_src}" style="width:100%; max-width:600px;" /><br>'
        
        content += f'<p>{title}</p>'
        
        fe.content(content, type='CDATA')
        count += 1

    fg.rss_file('google_world.xml', pretty=True)
    print(f"Sucesso! {count} itens com títulos gerados.")

if __name__ == "__main__":
    gerar_feed_google()
