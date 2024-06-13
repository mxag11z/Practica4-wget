import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# numero de trabajadores concurrentes, o numero de hilos
MAX_THREADS = 10

def download_file(url, save_path):
    try:
       #En caso de que no exista el directorio lo crea

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        #con requests podemos hacer el get y obtener lo que hay en el url
        response = requests.get(url, stream=True)
        response.raise_for_status()
        #escribir en el documento
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(8192):
                file.write(chunk)
        print(f"\nDownloaded: {url}\n")
    except Exception as e:
        print(f"\nFailed to download {url}: {e}\n")

#iteracion sobre el html y obtener las links a los directorios y archivos
#usamos beautifulsoup para trabajar mejor con los html
def save_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    file_links = set()
    directory_links = set()

#encontramos todas las etiquetas mennciondas, dependiendo agregarlo al file_links o directory_links
    for tag in soup.find_all(['a', 'img', 'link', 'script']):
        if tag.name == 'a' and 'href' in tag.attrs:
            link = tag.attrs['href']
            full_url = urljoin(url, link)
            # si es directorio
            if full_url.endswith('/'):
                directory_links.add(full_url)
            else:
                file_links.add(full_url)
        elif tag.name in ['img', 'script'] and 'src' in tag.attrs:
            link = tag.attrs['src']
            full_url = urljoin(url, link)
            file_links.add(full_url)
        elif tag.name == 'link' and 'href' in tag.attrs and tag.attrs.get('rel') == ['stylesheet']:
            link = tag.attrs['href']
            full_url = urljoin(url, link)
            file_links.add(full_url)

    return list(file_links), list(directory_links)

#creamos el index.html por capa
def create_index_html(page_dir, file_links, directory_links, base_dir):
    index_content = "<html><head><title>Index of {}</title></head><body>".format(page_dir)
    index_content += "<h1>Index of {}</h1>".format(page_dir)
    index_content += "<ul>"

    #obtenemos el directorio relativo para el dir
    for dir_link in directory_links:
        parsed_dir_link = urlparse(dir_link)
        local_dir_link = os.path.relpath(
            os.path.join(base_dir, parsed_dir_link.netloc, parsed_dir_link.path.lstrip('/').replace('/', os.sep)),
            start=page_dir
        )
        if local_dir_link != '.':  
            index_content += '<li><a href="{}/index.html">{}/</a></li>'.format(local_dir_link, os.path.basename(dir_link.rstrip('/')))
    #obtenemos el link relativo al archivo y apunte al local, evitamos los ?
    for file_link in file_links:
        if '?' not in file_link:
            parsed_file_link = urlparse(file_link)
            local_file_link = os.path.relpath(
                os.path.join(base_dir, parsed_file_link.netloc, parsed_file_link.path.lstrip('/').replace('/', os.sep)),
                start=page_dir
            )
            index_content += '<li><a href="{}">{}</a></li>'.format(local_file_link, os.path.basename(file_link))
    
    index_content += "</ul></body></html>"

    index_file_path = os.path.join(page_dir, "index.html")
    with open(index_file_path, 'w', encoding='utf-8') as index_file:
        index_file.write(index_content)
    print(f"Se creo el indice en: {index_file_path}")

def rename_conflicting_files(file_links, directory_links):
    dir_names = {os.path.basename(urlparse(dir_url).path.rstrip('/')).lower() for dir_url in directory_links}
    renamed_files_map = {}

    for file_url in file_links:
        file_path = urlparse(file_url).path
        file_name = os.path.basename(file_path)
        dir_path = os.path.dirname(file_path)
        
        if file_name.lower() in dir_names:
            new_file_name = file_name + "_file"
            renamed_files_map[file_url] = (dir_path, new_file_name)
        else:
            renamed_files_map[file_url] = (dir_path, file_name)
    
    return renamed_files_map

def adentrando(url, base_dir, visited, current_depth, max_depth):
    #la condicion base
    if current_depth >= max_depth or url in visited:
        return
    visited.add(url)  # se anade a los visitados
    print(f"\n*****VISITED URLS***\n{visited}\n")

    print(f"\nAdentrando: {url} en nivel {current_depth}\n")

    #para el link de directorio se crea el folder
    parsed_url = urlparse(url)
    print(f"parsed url: {parsed_url}")
    page_dir = os.path.join(base_dir, parsed_url.netloc, os.path.dirname(parsed_url.path.lstrip('/').replace('/', os.sep).replace('\\', os.sep)))
    os.makedirs(page_dir, exist_ok=True)
    print(f"this is the page dir: {page_dir}")

    # obtenemos por separado los links de directorio y de archivos
    file_links, directory_links = save_page(url)

    print(f"\nThese are file links: {file_links}, \n******\nThese are directory links: {directory_links}\n")

    # Renombrar en caso de que existan archivos y directorios con el mismo nombre
    renamed_files_map = rename_conflicting_files(file_links, directory_links)

    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # se crea un objeto futuro para cada item de renamed_files_map y se procesa con submit
        #que crea un objeto futuro al llamar a la funcion doenload_file
        futures = [
            executor.submit(download_file, file_url, os.path.join(base_dir, parsed_url.netloc, file_dir.lstrip('/').replace('/', os.sep), file_name))
            for file_url, (file_dir, file_name) in renamed_files_map.items()
            if '?' not in file_url and file_url not in visited
        ]
        #iteramos por cada objeto futuro que se ha completado y obtenemos su resultado
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error downloading file: {e}")

    # crear los index por capa
    create_index_html(page_dir, file_links, directory_links, base_dir)

    # recursividad en caso de los directorios
    if current_depth < max_depth:
        for directory_url in directory_links:
            adentrando(directory_url, base_dir, visited, current_depth + 1, max_depth)

if __name__ == "__main__":
    start_url = "http://148.204.58.221/axel/aplicaciones/"  #reemplazar con el link
    base_dir = "C:/Users/maxar/Documents/downloadsfrom".replace('/', os.sep)  #donde se va a guardar
    max_depth = 4  # Maxima capa

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    visited = set()
    adentrando(start_url, base_dir, visited, 0, max_depth)
