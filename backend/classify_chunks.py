# backend/classify_chunks.py

import json
import openai
import argparse
from tqdm import tqdm
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def classify_chunk(text):
    system_prompt = "Tu es un classifieur de contenu. Tu dois attribuer un 'type' parmi : residence, faq, reglement, contact, services, autres."
    user_prompt = f"""Voici un extrait de contenu d'un site web. Dis simplement à quelle catégorie il correspond parmi les suivantes : 
- residence (description d'une résidence, adresse, photos, chambres…)
- faq (questions fréquentes)
- reglement (règles, conditions d'admission, RGPD…)
- contact (informations de contact, accès, horaires)
- services (wifi, laverie, petit dej…)
- autres (si rien ne colle)

Contenu : '''{text}'''"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Erreur avec GPT : {e}")
        return "autres"

def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:
        for line in tqdm(infile, desc="Classification des chunks"):
            item = json.loads(line)
            text = item.get("content", "")
            chunk_type = classify_chunk(text[:1000])  # Ne dépasse pas la limite
            item["metadata"]["type"] = chunk_type
            outfile.write(json.dumps(item, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Fichier .jsonl en entrée (brut)")
    parser.add_argument("--output", required=True, help="Fichier .jsonl en sortie (classifié)")
    args = parser.parse_args()
    process_file(args.input, args.output)
