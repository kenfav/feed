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
    print(f"Links encontrados: {len(links)}")

    count = 0
    urls_vistas = set()

    for link_tag in links:
        href = link_tag['href'].replace('./', 'https://news.google.com/')
        
        if href in urls_vistas: continue
        urls_vistas.add(href)

        # --- CORREÇÃO AQUI: Prioridade TOTAL ao aria-label ---
        title = link_tag.get('aria-label')
        
        # Se não tiver aria-label, tenta o texto (fallback)
        if not title:
            title = link_tag.get_text(strip=True)
            
        # Se ainda assim estiver vazio, pula (não gera item sem título)
        if not title:
            continue

        # Limpeza opcional: O aria-label vem com "Titulo - Fonte - Hora"
        # Se você quiser limpar, pode descomentar abaixo:
        # parts = title.rsplit(' - ', 2) # Tenta separar as 2 ultimas partes
        # if len(parts) > 1: title = parts[0] 

        # --- Imagem (Lógica Figure Anterior) ---
        img_src = ""
        figure = link_tag.find_previous('figure')
        if figure:
            img = figure.find('img')
            if img:
                if img.has_attr('srcset'):
                    parts = img['srcset'].split(' ')
                    if len(parts) >= 2: img_src = parts[-2]
                    else: img_src = img.get('src')
                else:
                    img_src = img.get('src')

                if img_src and img_src.startswith('/'):
                    img_src = 'https://news.google.com' + img_src

        # --- Data ---
        pub_date = datetime.datetime.now(datetime.timezone.utc)
        # Procura data perto do link
        time_tag = None
        if link_tag.parent:
            time_tag = link_tag.parent.find('time')
        if not time_tag:
            time_tag = link_tag.find_next('time')
            
        if time_tag and time_tag.has_attr('datetime'):
            try: pub_date = time_tag['datetime']
            except: pass

        # --- Adiciona ao Feed ---
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
    print(f"Sucesso! {count} itens com títulos (via aria-label).")

if __name__ == "__main__":
    gerar_feed_google()
