from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import os
import sys

def gerar_feed_offline():
    arquivo_fonte = 'jw_source.html'
    
    # Verifica se o curl fez o trabalho dele
    if not os.path.exists(arquivo_fonte):
        print(f"Erro CRÍTICO: O arquivo {arquivo_fonte} não foi encontrado!")
        sys.exit(1)

    # Verifica se o arquivo não está vazio (bloqueio gera arquivo vazio as vezes)
    if os.path.getsize(arquivo_fonte) < 1000:
        print("Erro: O arquivo baixado é muito pequeno. Provável bloqueio ou erro.")
        with open(arquivo_fonte, 'r') as f:
            print("Conteúdo:", f.read())
        sys.exit(1)

    print("Lendo arquivo HTML...")
    with open(arquivo_fonte, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'lxml')
    
    fg = FeedGenerator()
    fg.title('JW.org - What\'s New')
    fg.link(href='https://www.jw.org/en/whats-new/', rel='alternate')
    fg.description('Feed Updates')
    fg.language('en')

    items = soup.select('.synopsis')
    print(f"Sucesso: Encontrados {len(items)} itens.")

    for element in items:
        fe = fg.add_entry()
        
        # Título e Link
        title_tag = element.select_one('h3 a')
        if not title_tag: continue
            
        title = title_tag.get_text(strip=True)
        link = title_tag['href']
        if not link.startswith('http'):
            link = 'https://www.jw.org' + link
            
        fe.title(title)
        fe.link(href=link)
        fe.id(link)

        # Data
        date_tag = element.select_one('.meta.pubDate')
        if date_tag:
            try:
                fe.published(datetime.datetime.now(datetime.timezone.utc))
            except: pass

        # Imagem
        img_src = ''
        img_tag = element.select_one('.jsRespImg')
        if img_tag:
            if img_tag.has_attr('data-img-size-md'): img_src = img_tag['data-img-size-md']
            elif img_tag.has_attr('data-img-size-lg'): img_src = img_tag['data-img-size-lg']
            elif img_tag.has_attr('data-img-size-xs'): img_src = img_tag['data-img-size-xs']

        # Descrição
        desc = element.select_one('.desc')
        desc_txt = desc.get_text(strip=True) if desc else ""

        content = ""
        if img_src: content += f'<img src="{img_src}" style="width:100%; max-width:600px;" /><br>'
        content += desc_txt
        
        fe.content(content, type='CDATA')

    fg.rss_file('feed.xml')

if __name__ == "__main__":
    gerar_feed_offline()
