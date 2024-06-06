""" import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

# Number of threads
MAX_THREADS = 100

def download_file(url, save_path):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"\nDownloaded: {url}\n")
    except Exception as e:
        print(f"\nFailed to download {url}: {e}\n")

def save_page(url, base_dir):
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

    return list(file_links), list(directory_links)  # Convert back to lists for compatibility with the rest of your code
 #returns the fileLinks and the directoryLinks belongs to 
#cases que the href endsWith / or ? so it gets added to the array with directory links

#how much time shall we do it, currenth deep increases as iteration advances
#maxdepth is given by the user, how many levels inside we want to download

def adentrando(url, base_dir, visited, current_depth, max_depth):
    if current_depth > max_depth or url in visited:
        return
    visited.add(url)#adding the url in the visited
    print(f"\n*****VISITED URLS***\n{visited}\n")

    print(f"\nAdentrando: {url} en nivel {current_depth}\n")

    # Create a directory for the current page
    parsed_url = urlparse(url)
    print(f"parsed url:{parsed_url}")
    page_dir = os.path.join(base_dir, parsed_url.netloc, os.path.dirname(parsed_url.path.lstrip('/').replace('/',os.sep).replace('\\',os.sep)))
    os.makedirs(page_dir, exist_ok=True)
    print(f"this is the page dir: {page_dir}")

    # Save page content and collect file and directory links
    file_links, directory_links = save_page(url, page_dir)

    print(f"\nThis are file links:{file_links}, \n******8\nthis are directory links:{directory_links}\n")
    
    for file_url in file_links:
        if not '?' in file_url or not file_url in visited:
                visited.add(file_url)
                parsed_file_url = urlparse(file_url)
            
                file_path = parsed_file_url.path.lstrip('/').replace('/',os.sep)
                print(f'\nThis is the path: {file_path}')
           
                save_path = os.path.join(base_dir,parsed_file_url.netloc, file_path)
                print(f"\nThis is the savepath: {save_path}")
                download_file(file_url,save_path)
            
        # Recursively crawl linked directories if within depth limit
    for directory_url in directory_links:
            adentrando(directory_url, base_dir, visited, current_depth + 1, max_depth)

if __name__ == "__main__":
    start_url = "http://148.204.58.221/axel/aplicaciones/"  # Replace with the URL you want to start from
    base_dir = "c:/Users/anira/Documents/downloadsfrom".replace('/',os.sep)  # Use forward slashes to avoid escape characters
    max_depth = 3  # Set the desired depth level

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    visited = set()
    adentrando(start_url, base_dir, visited, 0, max_depth) """

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

# Number of threads
MAX_THREADS = 100

def download_file(url, save_path):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
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

def ensure_directory_exists(path):
    if os.path.isfile(path):
        new_path = path + "_dir"
        os.makedirs(new_path, exist_ok=True)
        return new_path
    os.makedirs(path, exist_ok=True)
    return path

def ensure_file_path(save_path):
    dir_path = os.path.dirname(save_path)
    if os.path.isdir(dir_path):
        return save_path
    if os.path.isfile(dir_path):
        new_dir_path = dir_path + "_dir"
        os.makedirs(new_dir_path, exist_ok=True)
        return os.path.join(new_dir_path, os.path.basename(save_path))
    os.makedirs(dir_path, exist_ok=True)
    return save_path

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
    page_dir = ensure_directory_exists(page_dir)
    print(f"this is the page dir: {page_dir}")

    # Save page content and collect file and directory links
    file_links, directory_links = save_page(url)

    print(f"\nThese are file links: {file_links}, \n******\nThese are directory links: {directory_links}\n")

    for file_url in file_links:
        if not '?' in file_url and file_url not in visited:
            visited.add(file_url)
            parsed_file_url = urlparse(file_url)
            file_path = parsed_file_url.path.lstrip('/').replace('/', os.sep)
            print(f'\nThis is the path: {file_path}')
            save_path = os.path.join(base_dir, parsed_file_url.netloc, file_path)
            save_path = ensure_file_path(save_path)
            print(f"\nThis is the savepath: {save_path}")
            download_file(file_url, save_path)

    # Recursively crawl linked directories if within depth limit
    for directory_url in directory_links:
        adentrando(directory_url, base_dir, visited, current_depth + 1, max_depth)

if __name__ == "__main__":
    start_url = "http://148.204.58.221/axel/aplicaciones/"  # Replace with the URL you want to start from
    base_dir = "c:/Users/anira/Documents/downloadsfrom".replace('/', os.sep)  # Use forward slashes to avoid escape characters
    max_depth = 3  # Set the desired depth level

    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    visited = set()
    adentrando(start_url, base_dir, visited, 0, max_depth)
