import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import json
import sys
import os
from langdetect import detect
from tqdm import tqdm
import time

visited = set()
output_chunks = []
seen_hashes = set()


def get_html(url):
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Crawl2Chunks/1.0)"
        })
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"[WARN] Erreur sur {url}: {e}")
    return None


def extract_links(base_url, soup):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url.split("#")[0])
    return links


def clean_soup(soup):
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "form", "button", "svg", "input", "noscript"]):
        tag.decompose()
    return soup


def extract_chunks(text, max_tokens=500):
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 30]
    chunks = []
    current = ""
    for p in paragraphs:
        if len((current + p).split()) <= max_tokens:
            current += " " + p
        else:
            chunks.append(current.strip())
            current = p
    if current:
        chunks.append(current.strip())
    return chunks


def hash_chunk(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def process_url(url, forced_lang=None):
    html = get_html(url)
    if not html:
        return set()

    soup = BeautifulSoup(html, "html.parser")
    clean = clean_soup(soup)

    # Texte lisible
    text = "\n".join([e.get_text() for e in clean.find_all(["p", "h1", "h2", "h3", "li"])])
    chunks = extract_chunks(text)

    for chunk in chunks:
        hash_id = hash_chunk(chunk)
        if hash_id in seen_hashes:
            continue
        seen_hashes.add(hash_id)

        try:
            lang = forced_lang if forced_lang else detect(chunk)
        except:
            lang = "unknown"

        output_chunks.append({
            "content": chunk,
            "metadata": {
                "url": url,
                "lang": lang,
                "hash": hash_id
            }
        })

    return extract_links(url, soup)


def crawl(start_url, lang="fr", max_pages=100):
    to_visit = [start_url]
    pbar = tqdm(total=max_pages, desc="Crawling site")
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        new_links = process_url(url, forced_lang=lang)
        to_visit.extend(new_links - visited)
        pbar.update(1)
    pbar.close()


def save_jsonl(path):
    with open(path, "w", encoding="utf-8") as f:
        for chunk in output_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage : python crawl2chunks.py <url> [--lang fr] [--output chunks.jsonl]")
        sys.exit(1)

    start_url = sys.argv[1]
    lang = "fr"
    output = "chunks.jsonl"

    if "--lang" in sys.argv:
        lang = sys.argv[sys.argv.index("--lang") + 1]

    if "--output" in sys.argv:
        output = sys.argv[sys.argv.index("--output") + 1]

    print(f"🔍 Démarrage du crawl sur : {start_url}")
    crawl(start_url, lang=lang)
    save_jsonl(output)
    print(f"✅ {len(output_chunks)} chunks extraits → {output}")


if __name__ == "__main__":
    main()
