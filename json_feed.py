import requests
import datetime
from feedgen.feed import FeedGenerator

def gerar_feed_video():
    url = "https://b.jw-cdn.org/apis/mediator/v1/categories/E/LatestVideos?detailed=1&mediaLimit=0&clientType=json"
    
    print(f"Baixando dados da API: {url}")
    
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Erro ao baixar JSON: {e}")
        return

    fg = FeedGenerator()
    fg.title(data['category']['name'])
    fg.description(data['category'].get('description', 'Latest videos from JW Broadcasting'))
    fg.link(href='https://www.jw.org', rel='alternate')
    fg.language('en')

    videos = data['category'].get('media', [])
    print(f"Processando {len(videos)} vídeos...")

    for video in videos:
        fe = fg.add_entry()
        
        # 1. Título
        fe.title(video['title'])
        
        # 2. Busca o link do vídeo (MP4) e Imagem
        files = video.get('files', [])
        video_url = ""
        file_size = 0
        
        # Tenta pegar 720p, senão pega o último (melhor qualidade)
        for f in files:
            if f.get('label') == '720p':
                video_url = f.get('progressiveDownloadURL')
                file_size = f.get('filesize', 0)
                break
        
        if not video_url and files:
            video_url = files[-1].get('progressiveDownloadURL')
            file_size = files[-1].get('filesize', 0)

        # 3. Imagem (Thumbnail)
        images = video.get('images', {})
        img_src = ""
        if 'wss' in images and 'lg' in images['wss']:
            img_src = images['wss']['lg']
        elif 'sqr' in images and 'md' in images['sqr']:
            img_src = images['sqr']['md']

        # 4. Configuração para Download (Enclosure)
        # Isso garante compatibilidade com Apps de Podcast
        if video_url:
            fe.link(href=video_url)
            fe.id(video_url)
            fe.enclosure(video_url, str(file_size), 'video/mp4')

        # 5. Data
        if 'firstPublished' in video:
            fe.published(video['firstPublished'])

        # 6. CONTEÚDO HTML (Aqui está a mágica do Player)
        duration = video.get('durationFormattedMinSec', '')
        description_text = video.get('description', '')

        content = ""
        
        # Adiciona o Player de Vídeo HTML5
        # 'poster' é a imagem de capa antes do play
        # 'controls' mostra os botões de play/volume
        # 'preload="metadata"' economiza dados do usuário
        if video_url:
            content += f'''
            <video controls preload="metadata" style="width:100%; max-width:100%; border-radius: 8px;" poster="{img_src}">
                <source src="{video_url}" type="video/mp4">
                Seu leitor RSS não suporta reprodução de vídeo. <a href="{video_url}">Baixar Vídeo</a>
            </video>
            <br><br>
            '''
        elif img_src:
            # Se não tiver video url (erro raro), mostra só a imagem
            content += f'<img src="{img_src}" style="width:100%; max-width:600px;" /><br>'
        
        content += f'<b>⏳ Duração:</b> {duration}<br>'
        
        if description_text:
            content += f'<p>{description_text}</p>'

        fe.content(content, type='CDATA')
        fe.description(description_text if description_text else video['title'])

    # Salva com pretty=True para ficar legível (com quebras de linha)
    fg.rss_file('feed.xml', pretty=True)
    print("Sucesso! Arquivo 'feed.xml' gerado com player de vídeo.")

if __name__ == "__main__":
    gerar_feed_video()
