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
    
    # Configuração do Feed
    fg = FeedGenerator()
    fg.title('Google News - World Stories')
    fg.link(href=url, rel='alternate')
    fg.description('Top stories from Google News (US Edition)')
    fg.language('en')

    # --- LÓGICA DE EXTRAÇÃO (Link -> Figure Anterior) ---
    # Encontra todos os links de leitura
    links = soup.find_all('a', href=lambda x: x and x.startswith('./read/'))
    print(f"Links encontrados: {len(links)}")

    count = 0
    urls_vistas = set()

    for link_tag in links:
        # 1. Limpa URL
        href = link_tag['href'].replace('./', 'https://news.google.com/')
        
        if href in urls_vistas:
            continue
        urls_vistas.add(href)

        # 2. Título (Texto do Link ou Aria-Label)
        title = link_tag.get_text(strip=True)
        if not title:
            title = link_tag.get('aria-label', 'No Title')

        # 3. Imagem (Busca a <figure> anterior mais próxima)
        img_src = ""
        figure = link_tag.find_previous('figure')
        
        # Verifica se a figure é "vizinha" próxima (para não pegar imagem de outra noticia)
        # Geralmente no Google News estão no mesmo container pai ou avô
        if figure:
            img = figure.find('img')
            if img:
                # Tenta pegar a melhor qualidade no srcset
                if img.has_attr('srcset'):
                    # Formato: /url 1x, /url 2x
                    parts = img['srcset'].split(' ')
                    if len(parts) >= 2:
                        raw_src = parts[-2]
                    else:
                        raw_src = img.get('src')
                else:
                    raw_src = img.get('src')

                # Corrige caminho relativo da imagem
                if raw_src:
                    if raw_src.startswith('/'):
                        img_src = 'https://news.google.com' + raw_src
                    elif raw_src.startswith('http'):
                        img_src = raw_src

        # 4. Data
        pub_date = datetime.datetime.now(datetime.timezone.utc)
        # Tenta achar <time> perto do link
        container = link_tag.parent
        time_tag = container.find('time') if container else None
        
        # Se não achou no pai direto, tenta no próximo irmão (estrutura comum do Google)
        if not time_tag:
            time_tag = link_tag.find_next('time')

        if time_tag and time_tag.has_attr('datetime'):
            try:
                pub_date = time_tag['datetime']
            except: pass

        # 5. Adiciona ao Feed
        fe = fg.add_entry()
        fe.title(title)
        fe.link(href=href)
        fe.id(href)
        fe.published(pub_date)

        # HTML
        content = ""
        if img_src:
            content += f'<img src="{img_src}" style="width:100%; max-width:600px; border-radius: 8px;" /><br>'
        
        content += f'<p>{title}</p>'
        
        fe.content(content, type='CDATA')
        count += 1

    fg.rss_file('google_world.xml', pretty=True)
    print(f"Sucesso! {count} notícias geradas em 'google_world.xml'")

if __name__ == "__main__":
    gerar_feed_google()
