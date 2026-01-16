import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import json

#seed set
SEED_URLS = [
    "https://en.wikipedia.org/wiki/Computer_science",      
    "https://en.wikipedia.org/wiki/Toronto_Blue_Jays",     
    "https://en.wikipedia.org/wiki/Pizza",                 
    "https://en.wikipedia.org/wiki/Drake_(musician)",          
    "https://en.wikipedia.org/wiki/Canada",                
    "https://en.wikipedia.org/wiki/Lion",                  
    "https://en.wikipedia.org/wiki/List_of_best-selling_fiction_authors",
    "https://en.wikipedia.org/wiki/Literature",
    "https://en.wikipedia.org/wiki/Toronto",
    "https://en.wikipedia.org/wiki/History_of_Toronto",
    "https://en.wikipedia.org/wiki/Football",
    "https://en.wikipedia.org/wiki/Ice_hockey",
    "https://en.wikipedia.org/wiki/The_arts"
]

TARGET_DOMAIN = "en.wikipedia.org"
MAX_PAGES = 1000
OUTPUT_FILE = "web_collection.all"
URL_MAP_FILE = "urls.txt"
LINK_FILE = "page_links.json"

HEADERS = {
    'User-Agent': 'StudentProjectBot/1.0 (Educational Purpose; Ryerson/TMU)'
}

def is_valid_url(url):
    parsed = urlparse(url)
    return (parsed.netloc == TARGET_DOMAIN and 
            parsed.path.startswith("/wiki/") and 
            ":" not in parsed.path and 
            not parsed.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')))

def crawl():
    queue = list(SEED_URLS)
    visited = set(SEED_URLS)
    doc_id = 1
    link_structure = {}
    print(f"Starting General Topic Crawl with {len(SEED_URLS)} seeds...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out, \
         open(URL_MAP_FILE, "w", encoding="utf-8") as f_map:

        while queue and doc_id <= MAX_PAGES:
            url = queue.pop(0)
            
            try:
                time.sleep(1.0) #1 second delay between requests
                
                response = requests.get(url, headers=HEADERS, timeout=5)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Titke extract 
                title_tag = soup.find('h1', {'id': 'firstHeading'})
                title = title_tag.get_text().strip() if title_tag else "No Title"
                
                # Body extract 
                paragraphs = soup.find_all('p')
                body_text = " ".join([p.get_text().strip() for p in paragraphs])
                body_text = body_text.replace("\n", " ")

                # CACM
                f_out.write(f".I {doc_id}\n")
                f_out.write(f".T\n{title}\n")
                f_out.write(f".W\n{body_text}\n")
                f_out.write(f".X\n{url}\n")
                
                # Save URL Mapping
                f_map.write(f"{doc_id} {url}\n")
                
                print(f"[{doc_id}/{MAX_PAGES}] Crawled: {title}")

                # Extract links
                outgoing_urls = []
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href'])
                    full_url = full_url.split('#')[0]

                    if is_valid_url(full_url):
                        outgoing_urls.append(full_url)
                        if full_url not in visited:
                            visited.add(full_url)
                            queue.append(full_url)
                
                link_structure[doc_id] = outgoing_urls
                doc_id += 1

            except Exception as e:
                print(f"Error crawling {url}: {e}")

    # Save links for pageRank
    with open(LINK_FILE, "w", encoding="utf-8") as f:
        json.dump(link_structure, f)
    print("\nCrawl Complete!")

if __name__ == "__main__":
    crawl()