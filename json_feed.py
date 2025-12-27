import requests
import datetime
from feedgen.feed import FeedGenerator

def gerar_feed_video():
    # URL da API Oficial (Muito mais estável que o site)
    url = "https://b.jw-cdn.org/apis/mediator/v1/categories/E/LatestVideos?detailed=1&mediaLimit=0&clientType=json"
    
    print(f"Baixando dados da API: {url}")
    
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Erro ao baixar JSON: {e}")
        return

    # Configuração do Feed
    fg = FeedGenerator()
    fg.title(data['category']['name']) # "Latest Videos"
    fg.description(data['category'].get('description', 'Latest videos from JW Broadcasting'))
    fg.link(href='https://www.jw.org', rel='alternate')
    fg.language('en')

    videos = data['category'].get('media', [])
    print(f"Processando {len(videos)} vídeos...")

    for video in videos:
        fe = fg.add_entry()
        
        # 1. Título
        fe.title(video['title'])
        
        # 2. Link do Vídeo (MP4)
        # O JSON oferece várias qualidades (240p, 360p, 480p, 720p).
        # Vamos tentar pegar 720p, se não der, pega o último da lista (geralmente a melhor qualidade)
        files = video.get('files', [])
        video_url = ""
        file_size = 0
        
        # Procura preferencialmente por 720p
        for f in files:
            if f.get('label') == '720p':
                video_url = f.get('progressiveDownloadURL')
                file_size = f.get('filesize', 0)
                break
        
        # Se não achou 720p, pega o último disponível (maior qualidade)
        if not video_url and files:
            video_url = files[-1].get('progressiveDownloadURL')
            file_size = files[-1].get('filesize', 0)

        # Adiciona o link principal e o Enclosure (para funcionar como Podcast de vídeo)
        if video_url:
            fe.link(href=video_url)
            fe.id(video_url) # ID único
            fe.enclosure(video_url, str(file_size), 'video/mp4')

        # 3. Data de Publicação
        if 'firstPublished' in video:
            fe.published(video['firstPublished'])

        # 4. Imagem (Thumbnail)
        # O JSON tem vários formatos. 'wss' (Widescreen) 'lg' (Large) é o ideal.
        images = video.get('images', {})
        img_src = ""
        
        if 'wss' in images and 'lg' in images['wss']:
            img_src = images['wss']['lg']
        elif 'sqr' in images and 'md' in images['sqr']:
            img_src = images['sqr']['md'] # Fallback para quadrado

        # 5. Descrição HTML (para aparecer bonito no leitor)
        duration = video.get('durationFormattedMinSec', '')
        
        content = ""
        if img_src:
            content += f'<img src="{img_src}" style="width:100%; max-width:600px; display:block;" /><br>'
        
        content += f'<b>Duration:</b> {duration}<br>'
        
        # Adiciona descrição se houver (o JSON as vezes traz vazio)
        if video.get('description'):
            content += f'<p>{video["description"]}</p>'
            fe.description(video["description"])
        else:
            fe.description(f"Video: {video['title']}")

        fe.content(content, type='CDATA')

    # Salva o arquivo XML
    fg.rss_file('feed_video.xml', pretty=True)
    print("Sucesso! Arquivo 'feed_video.xml' gerado.")

if __name__ == "__main__":
    gerar_feed_video()
