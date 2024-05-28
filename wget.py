import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

# Number of threads
MAX_THREADS = 50

def download_file(url, save_path):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Downloaded: {url}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def save_page(url, base_dir):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    file_links = []
    directory_links = []

    for tag in soup.find_all(['a', 'img', 'link', 'script']):
        if tag.name == 'a' and 'href' in tag.attrs:
            link = tag.attrs['href']
            full_url = urljoin(url, link)
            # Check if the link is likely a directory
            if full_url.endswith('/'):
                directory_links.append(full_url)
            else:
                file_links.append(full_url)
        elif tag.name in ['img', 'script'] and 'src' in tag.attrs:
            link = tag.attrs['src']
            full_url = urljoin(url, link)
            file_links.append(full_url)
        elif tag.name == 'link' and 'href' in tag.attrs and tag.attrs.get('rel') == ['stylesheet']:
            link = tag.attrs['href']
            full_url = urljoin(url, link)
            file_links.append(full_url)

    return file_links, directory_links #returns the fileLinks and the directoryLinks belongs to 
#cases que the href endsWith / or ? so it gets added to the array with directory links

#how much time shall we do it, currenth deep increases as iteration advances
#maxdepth is given by the user, how many levels inside we want to download
def adentrando(url, base_dir, visited, current_depth, max_depth):
    if current_depth > max_depth or url in visited:
        return
    visited.add(url)#adding the url in the visited

    print(f"Adentrando: {url} en nivel {current_depth}")

    # Create a directory for the current page
    parsed_url = urlparse(url)
    print(f"parsed url:{parsed_url}")
    page_dir = os.path.join(base_dir, parsed_url.netloc, os.path.dirname(parsed_url.path.lstrip('/')))
    os.makedirs(page_dir, exist_ok=True)

    # Save page content and collect file and directory links
    file_links, directory_links = save_page(url, page_dir)

    print(f"This are file links:{file_links}, this are directory links:{directory_links}")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit file download tasks
        futures = []
        for file_url in file_links:
            parsed_file_url = urlparse(file_url)
            file_path = parsed_file_url.path.lstrip('/')
            save_path = os.path.join(base_dir, parsed_url.netloc, file_path)
            futures.append(executor.submit(download_file, file_url, save_path))

        # Wait for all file download tasks to complete
        for future in futures:
            future.result()

        # Recursively crawl linked directories if within depth limit
        for directory_url in directory_links:
            adentrando(directory_url, base_dir, visited, current_depth + 1, max_depth)

if __name__ == "__main__":
    start_url = "http://148.204.58.221/axel/aplicaciones/sockets/"  # Replace with the URL you want to start from
    base_dir = "C:/Users/maxar/Documents/deswget"  # Use forward slashes to avoid escape characters
    max_depth = 2  # Set the desired depth level

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    visited = set()
    adentrando(start_url, base_dir, visited, 0, max_depth)
