import argparse
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langdetect import detect
from flask import Flask, render_template_string, request
import os
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load environment variables from .env if present
load_dotenv()

# GLOBALS
visited = set()
output_chunks = []
seen_hashes = set()

# HTML template for Flask UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chunks Viewer</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        .chunk { border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
        .meta { font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <h1>Chunks Viewer</h1>
    <form method="get">
        <input type="text" name="search" placeholder="Recherche..." value="{{ search }}" style="width:300px;">
        <select name="type">
            <option value="">Tous les types</option>
            <option value="résidence">Résidence</option>
            <option value="faq">FAQ</option>
            <option value="service">Service</option>
            <option value="offre">Offre</option>
            <option value="informations générales">Infos générales</option>
            <option value="événement">Événement</option>
            <option value="autre">Autre</option>
        </select>
        <input type="submit" value="Filtrer">
    </form>
    {% for c in chunks %}
    <div class="chunk">
        <div class="meta">🔗 <a href="{{ c['metadata']['url'] }}" target="_blank">{{ c['metadata']['url'] }}</a> | Langue: {{ c['metadata']['lang'] }}{% if c['metadata'].get('type') %} | Type: {{ c['metadata']['type'] }}{% endif %}</div>
        <div>{{ c['content'] }}</div>
    </div>
    {% endfor %}
</body>
</html>
"""

# UTILS
def classify_chunks(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        chunks = [json.loads(line) for line in f]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    batch_size = 10
    enriched_chunks = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un assistant qui classe les contenus web dans l'une des catégories suivantes : "
                    "'faq', 'résidence', 'service', 'offre', 'informations générales', 'événement', ou 'autre'. "
                    "Tu dois répondre par une liste JSON simple avec une catégorie par texte dans l'ordre donné. "
                    "Exemple de réponse attendue : [\"résidence\", \"faq\", \"autre\", ...]"
                )
            },
            {
                "role": "user",
                "content": "Classe ces extraits : " + json.dumps([c['content'][:400] for c in batch], ensure_ascii=False)
            }
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0
            )
            print("Réponse brute:", response.choices[0].message.content)
            try:
                categories = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                print(f"[ERREUR PARSE] : {e}")
                print("Réponse non JSON:", response.choices[0].message.content)
                categories = ["autre"] * len(batch)

            for c, label in zip(batch, categories):
                c['metadata']['type'] = label
                enriched_chunks.append(c)
        except Exception as e:
            print(f"Erreur pendant le batch {i}: {e}")
            for c in batch:
                c['metadata']['type'] = "erreur"
                enriched_chunks.append(c)

        time.sleep(1.5)

    with open(output_path, 'w', encoding='utf-8') as f:
        for c in enriched_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

# MODE HANDLER
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['web', 'classify'], required=True)
    parser.add_argument('--file', type=str, required=True)
    parser.add_argument('--output', type=str)
    args = parser.parse_args()

    if args.mode == 'web':
        app = Flask(__name__)

        @app.route('/')
        def view():
            search = request.args.get('search', '').lower()
            type_filter = request.args.get('type', '').lower()
            with open(args.file, 'r', encoding='utf-8') as f:
                chunks = [json.loads(line) for line in f]
            if search:
                chunks = [c for c in chunks if search in c['content'].lower()]
            if type_filter:
                chunks = [c for c in chunks if c['metadata'].get('type', '').lower() == type_filter]
            return render_template_string(HTML_TEMPLATE, chunks=chunks, search=search)

        app.run(debug=True)

    elif args.mode == 'classify':
        if not args.output:
            raise ValueError("--output est requis pour le mode classify")
        classify_chunks(args.file, args.output)

if __name__ == '__main__':
    main()
