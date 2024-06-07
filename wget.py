import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Number of threads
MAX_THREADS = 10

def download_file(url, save_path):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(8192):
                file.write(chunk)
        print(f"\nDownloaded: {url}\n")
    except Exception as e:
        print(f"\nFailed to download {url}: {e}\n")

def save_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    file_links = set()
    directory_links = set()

    for tag in soup.find_all(['a', 'img', 'link', 'script']):
        if tag.name == 'a' and 'href' in tag.attrs:
            link = tag.attrs['href']
            full_url = urljoin(url, link)
            # Check if the link is likely a directory
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

def rename_conflicting_files(file_links, directory_links):
    dir_names = {os.path.basename(urlparse(dir_url).path.rstrip('/')).lower() for dir_url in directory_links}
    renamed_files_map = {}

    for file_url in file_links:
        file_path = urlparse(file_url).path
        file_name = os.path.basename(file_path)
        dir_path = os.path.dirname(file_path)
        
        if file_name.lower() in dir_names:
            # Rename file if there's a conflicting directory name
            new_file_name = file_name + "_file"
            renamed_files_map[file_url] = (dir_path, new_file_name)
        else:
            renamed_files_map[file_url] = (dir_path, file_name)
    
    return renamed_files_map

def adentrando(url, base_dir, visited, current_depth, max_depth):
    if current_depth > max_depth or url in visited:
        return
    visited.add(url)  # adding the URL to the visited set
    print(f"\n*****VISITED URLS***\n{visited}\n")

    print(f"\nAdentrando: {url} en nivel {current_depth}\n")

    # Create a directory for the current page
    parsed_url = urlparse(url)
    print(f"parsed url: {parsed_url}")
    page_dir = os.path.join(base_dir, parsed_url.netloc, os.path.dirname(parsed_url.path.lstrip('/').replace('/', os.sep).replace('\\', os.sep)))
    os.makedirs(page_dir, exist_ok=True)
    print(f"this is the page dir: {page_dir}")

    # Save page content and collect file and directory links
    file_links, directory_links = save_page(url)

    print(f"\nThese are file links: {file_links}, \n******\nThese are directory links: {directory_links}\n")

    # Rename conflicting file links
    renamed_files_map = rename_conflicting_files(file_links, directory_links)

    # Use ThreadPoolExecutor to download files concurrently
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_url = {
            executor.submit(download_file, file_url, os.path.join(base_dir, parsed_url.netloc, file_dir.lstrip('/').replace('/', os.sep), file_name)): file_url
            for file_url, (file_dir, file_name) in renamed_files_map.items()
            if '?' not in file_url and file_url not in visited
        }
        for future in as_completed(future_to_url):
            file_url = future_to_url[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error downloading {file_url}: {e}")

    # Recursively crawl linked directories if within depth limit
    if current_depth < max_depth:
        for directory_url in directory_links:
            adentrando(directory_url, base_dir, visited, current_depth + 1, max_depth)

if __name__ == "__main__":
    start_url = "http://148.204.58.221/axel/aplicaciones/"  # Replace with the URL you want to start from
    base_dir = "C:/Users/maxar/Documents/downloadsfrom".replace('/', os.sep)  # Use forward slashes to avoid escape characters
    max_depth = 2  # Set the desired depth level

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    visited = set()
    adentrando(start_url, base_dir, visited, 1, max_depth)
