from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Tentative de chargement du .env, ignore les erreurs d'encodage
try:
    load_dotenv()
except UnicodeDecodeError:
    print("Attention: Problème d'encodage du fichier .env, utilisation des variables d'environnement système")

COLLECTION_NAME = "chunks"

# Configuration OpenAI sécurisée
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError(
        " OPENAI_API_KEY non trouvée!\n"
        "   â†’ Vérifier que backend/.env contient: OPENAI_API_KEY=votre-cle\n"
        "   â†’ Pour Railway: configurer la variable dans le Dashboard"
    )

openai_client = OpenAI(api_key=openai_api_key)

# Configuration Qdrant adaptable (local vs cloud)
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if qdrant_url:
    # Mode Cloud (Railway, production)
    print(f"ðŸŒ Connexion à  Qdrant Cloud: {qdrant_url}")
    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
else:
    # Mode Local (développement)
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    print(f"ðŸ  Connexion à  Qdrant Local: {qdrant_host}:{qdrant_port}")
    qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)

app = FastAPI()

# Configuration CORS permissive pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Important : False avec allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchCriteria(BaseModel):
    """Critères de recherche extraits de la query"""
    max_budget: int | None = None
    min_budget: int | None = None
    city: str | None = None
    furnished: bool | None = None
    min_surface: float | None = None
    max_surface: float | None = None
    rooms: int | None = None
    max_results: int | None = None  # Nombre d'appartements demandés

class IntentAnalysis(BaseModel):
    """Analyse de l'intention utilisateur par GPT"""
    is_apartment_search: bool
    criteria: SearchCriteria
    reasoning: str  # Pour debug

class QueryRequest(BaseModel):
    query: str
    type: str | None = None
    summarize: bool = False
    conversation_history: list[dict] | None = None  # Format: [{"role": "user", "content": "..."}, ...]

def analyze_user_intent(query: str, conversation_history: list[dict] | None = None) -> IntentAnalysis:
    """
    Agent GPT qui analyse l'intention utilisateur et extrait les critères structurés
    EN TENANT COMPTE DE L'HISTORIQUE DE CONVERSATION
    """
    system_prompt = """Tu es un agent d'analyse de requàªtes pour une plateforme de logement étudiant.

Ta mission : analyser TOUTE LA CONVERSATION (pas juste la dernière question) et déterminer :
1. Est-ce une recherche d'appartement EXPLICITE ? (true/false)
2. Si oui, extraire TOUS les critères mentionnés DANS TOUTE LA CONVERSATION

RàˆGLES STRICTES :
- is_apartment_search=true UNIQUEMENT si l'utilisateur cherche un logement/appartement/studio/chambre/toit
- is_apartment_search=false pour les questions sur services, forfaits, marque, activités, équipements
- Extraire TOUS les critères : ville, budget, pièces, surface, meublé, nombre de résultats
- ANALYSER L'HISTORIQUE : si l'utilisateur a mentionné "Archamps" avant, city="Archamps"
- ANALYSER L'HISTORIQUE : si l'utilisateur a dit "600â‚¬" ou "t1 et 600â‚¬", max_budget=600
- ANALYSER L'HISTORIQUE : si l'utilisateur dit juste "800" ou "1000", c'est un budget â†’ max_budget=800
- ANALYSER L'HISTORIQUE : si l'utilisateur dit "T1" ou "Studio" ou "T2", extraire rooms (Studio=1, T1=1, T2=2, etc.)
- MAPPER LES ZONES : "Paris" â†’ chercher dans Massy-Palaiseau, Villejuif, Noisy-le-Grand
- MAPPER LES ZONES : "Genève" â†’ chercher dans Archamps
- Si l'utilisateur dit "Paris", city="Paris" (le système gérera les villes multiples)
- Si l'utilisateur dit "Tous" pour les typologies, rooms=null (afficher toutes)

EXEMPLES :
 "c'est quoi les forfaits red de chez sfr ?" â†’ is_apartment_search: false
 "quels sont les services chez ECLA ?" â†’ is_apartment_search: false
✅… "j'ai besoin de trouver un toit à  moins de 500 euros à  paris" â†’ is_apartment_search: true, max_budget: 500, city: "Paris"
✅… Historique: "Archamps", puis "t1 et 600â‚¬" â†’ is_apartment_search: true, rooms: 1, max_budget: 600, city: "Archamps"

Réponds UNIQUEMENT en JSON valide (pas de markdown) :
{
  "is_apartment_search": true/false,
  "criteria": {
    "max_budget": null ou nombre,
    "min_budget": null ou nombre,
    "city": null ou "Paris"/"Lyon"/etc,
    "furnished": null ou true/false,
    "min_surface": null ou nombre,
    "max_surface": null ou nombre,
    "rooms": null ou nombre (1=studio),
    "max_results": null ou nombre (si l'utilisateur précise combien d'appartements il veut voir)
  },
  "reasoning": "Courte explication de ton analyse"
}"""

    try:
        # Construire les messages avec l'historique
        messages = [{"role": "system", "content": system_prompt}]

        # Ajouter l'historique si disponible
        if conversation_history:
            for msg in conversation_history[-6:]:  # Garder les 6 derniers messages
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Ajouter la question actuelle
        messages.append({"role": "user", "content": f"Question actuelle : {query}"})

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.0,  # Déterministe
            max_tokens=300
        )

        result_text = response.choices[0].message.content.strip()
        print(f"[GPT-AGENT] Analyse brute: {result_text}")

        # Parser le JSON
        result_json = json.loads(result_text)

        # Construire IntentAnalysis
        criteria = SearchCriteria(
            max_budget=result_json["criteria"].get("max_budget"),
            min_budget=result_json["criteria"].get("min_budget"),
            city=result_json["criteria"].get("city"),
            furnished=result_json["criteria"].get("furnished"),
            min_surface=result_json["criteria"].get("min_surface"),
            max_surface=result_json["criteria"].get("max_surface"),
            rooms=result_json["criteria"].get("rooms"),
            max_results=result_json["criteria"].get("max_results")
        )

        intent = IntentAnalysis(
            is_apartment_search=result_json["is_apartment_search"],
            criteria=criteria,
            reasoning=result_json.get("reasoning", "")
        )

        print(f"[GPT-AGENT] Intent: {intent.is_apartment_search}, Criteres: {criteria}")
        return intent

    except Exception as e:
        print(f"[ERROR] Erreur analyse GPT: {e}")
        # Fallback : considérer que ce n'est pas une recherche d'appartement
        return IntentAnalysis(
            is_apartment_search=False,
            criteria=SearchCriteria(),
            reasoning=f"Erreur parsing: {e}"
        )

def embed(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def generate_commercial_response(chunks, query, conversation_history=None):
    """
    Agent commercial IA qui accompagne l'utilisateur comme un vrai conseiller
    ET qui sait collaborer avec le système d'affichage d'appartements
    """
    has_apartments = any(c.get('type') == 'appartement' for c in chunks)

    # Construire le contexte conversationnel
    conversation_context = ""
    if conversation_history and len(conversation_history) > 0:
        conversation_context = "Historique de la conversation :\n"
        for msg in conversation_history[-4:]:  # Garder les 4 derniers messages
            role = "Client" if msg.get("role") == "user" else "Vous"
            conversation_context += f"{role}: {msg.get('content', '')}\n"
        conversation_context += "\n"

    # Détecter si l'utilisateur a déjà  accepté l'aide
    user_accepted_help = False
    if conversation_history:
        recent_messages = [msg.get('content', '').lower() for msg in conversation_history[-3:]]
        acceptance_keywords = ['oui', 'yes', 'd\'accord', 'ok', 'parfait', 'montre', 'montrez', 'voir', 'montre-moi', 'montrez-moi']
        user_accepted_help = any(keyword in msg for msg in recent_messages for keyword in acceptance_keywords)
        print(f"[AGENT-COMMERCIAL] User accepted help: {user_accepted_help}")

    # Détecter si l'utilisateur demande explicitement à  voir des appartements
    user_wants_apartments = False
    if conversation_history:
        recent_messages = [msg.get('content', '').lower() for msg in conversation_history[-2:]]
        apartment_keywords = ['montre', 'montrez', 'voir', 'appartements', 'logements', 'disponibles', 'proche', 'budget']
        user_wants_apartments = any(keyword in msg for msg in recent_messages for keyword in apartment_keywords)
        print(f"[AGENT-COMMERCIAL] User wants apartments: {user_wants_apartments}")

    if has_apartments:
        nb_apartments = len([c for c in chunks if c.get('type') == 'appartement'])
        cities = list(set([c.get('city', '') for c in chunks if c.get('type') == 'appartement']))
        cities_str = ", ".join(cities) if cities else ""

        # Extraire les prix min/max
        prices = [c.get('rent_cc_eur', 0) for c in chunks if c.get('type') == 'appartement']
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        system_prompt = """Tu es Sarah, conseillère en logement chez ECLA, spécialisée dans l'accompagnement des étudiants et jeunes actifs.

TON ROLE :
- Accompagner le client comme un vrai commercial (chaleureux, proactif, orienté solution)
- Proposer UNIQUEMENT nos TYPOLOGIES de logements (JAMAIS la concurrence)
- Guider vers la réservation en montrant directement les typologies

CONCEPT IMPORTANT - TYPOLOGIES :
Une TYPOLOGIE = un modèle de logement représentatif dans une résidence (ex: Studio 18mÂ², T1 25mÂ², T2 40mÂ², etc.)
- Chaque résidence propose généralement 6 typologies : Studio, T1, T2, T3, T4, Colocation
- Le prix de base est affiché sur chaque card de typologie
- Le client construira SA réservation en choisissant des options (étage, TV, parking, etc.)
- Tu montres TOUTES les typologies disponibles d'une résidence

IMPORTANT - FLUX SIMPLIFIE :
- Après avoir identifié la ville/résidence, tu montres DIRECTEMENT toutes les typologies
- Le budget est affiché sur les cards, pas besoin de le demander
- Tu encourages le client à  explorer les différentes options
- Le client peut changer de résidence à  tout moment

RàˆGLES STRICTES :
 JAMAIS mentionner : CROUS, LeBonCoin, Appartager, Colonies, SeLoger
 JAMAIS dire "je ne peux pas vous aider"
 JAMAIS dire "X appartements" â†’ Dis "les typologies disponibles"
✅… TOUJOURS proposer des alternatives
✅… TOUJOURS poser une question de relance
✅… àŠtre concis (2-3 phrases max)
✅… Préparer le client avant de montrer les typologies

EXEMPLES :
 "Malheureusement, je n'ai rien à  Paris."
✅… "Je n'ai pas de résidence à  Paris dans ce budget, par contre à  Lille les typologies commencent à  710â‚¬. Lille est très bien desservie. Souhaitez-vous voir les typologies ?"

 "Voici 12 appartements."
✅… "Je vous montre les typologies disponibles à  Lille ! Du Studio au T4, à  partir de 710â‚¬/mois. Quelle typologie vous intéresse ?"
"""

        # Logique intelligente selon le contexte
        if user_wants_apartments and user_accepted_help:
            # MODE AFFICHAGE : L'utilisateur veut voir les appartements ET a accepté l'aide
            print(f"[AGENT-COMMERCIAL] Mode: AFFICHAGE (user wants apartments + accepted help)")
            prompt = f"""{conversation_context}Question actuelle : {query}

RESULTATS TROUVES :
- {nb_apartments} appartements disponibles
- Villes : {cities_str}
- Prix : de {min_price:.0f}€‚¬ à {max_price:.0f}€

CONSIGNES (MODE AFFICHAGE) :
1. Annonce que tu vas montrer les appartements (1 phrase)
2. Prépare le client : "Voici les appartements qui correspondent le mieux à  votre recherche"
3. TERMINE par une question pour la suite :
   "Quel appartement vous intéresse le plus ?"
   "Avez-vous des questions sur l'un de ces logements ?"
   "Souhaitez-vous que je vous aide à  réserver ?"

Réponds :"""
        elif user_accepted_help:
            # MODE ACTION COMMERCIALE : L'utilisateur a accepté l'aide mais veut d'abord affiner
            print(f"[AGENT-COMMERCIAL] Mode: AFFINAGE (user accepted help but wants to refine)")
            prompt = f"""{conversation_context}Question actuelle : {query}

RESULTATS TROUVES :
- {nb_apartments} appartements disponibles
- Villes : {cities_str}
- Prix : de {min_price:.0f}â‚¬ à  {max_price:.0f}â‚¬

CONSIGNES (MODE AFFINAGE) :
1. Présente les résultats de manière engageante (2-3 phrases)
2. Souligne le meilleur rapport qualité/prix
3. TERMINE par une question PRECISE pour affiner AVANT de montrer les appartements :
   "Quelle ville préférez-vous parmi {cities_str} ?"
   "Souhaitez-vous voir uniquement les studios ou aussi les T2 ?"
   "Voulez-vous que je filtre par prix maximum ?"
   "Préférez-vous les appartements meublés ou non meublés ?"
   "Souhaitez-vous que je vous montre les appartements maintenant ?"

Réponds :"""
        else:
            # MODE PROPOSITION D'AIDE : L'utilisateur n'a pas encore accepté
            print(f"[AGENT-COMMERCIAL] Mode: PROPOSITION (user hasn't accepted help yet)")
            prompt = f"""{conversation_context}Question actuelle : {query}

RESULTATS TROUVES :
- {nb_apartments} appartements disponibles
- Villes : {cities_str}
- Prix : de {min_price:.0f}â‚¬ à  {max_price:.0f}â‚¬

CONSIGNES (MODE PROPOSITION) :
1. Présente les résultats de manière engageante (2-3 phrases)
2. Souligne le meilleur rapport qualité/prix
3. TERMINE par une proposition d'aide :
   "Puis-je vous aider à  trouver un logement qui correspond à  vos critères et à  votre budget ?"

Réponds :"""

        max_tokens = 150

    else:
        # Pour les infos générales
        system_prompt = """Tu es Sarah, conseillère en logement chez ECLA.

TON Rà”LE :
- Répondre aux questions sur nos services, résidences, offres
- àŠtre concis et informatif
- Orienter vers la recherche d'appartements si pertinent

COLLABORATION :
Tu travailles avec un système d'affichage d'appartements. Tu peux déclencher l'affichage quand c'est pertinent.

RàˆGLES :
 JAMAIS mentionner la concurrence
✅… Utiliser UNIQUEMENT les informations fournies
✅… TOUJOURS proposer d'aider à  trouver un logement à  la fin"""

        if user_accepted_help:
            # MODE ACTION : L'utilisateur veut de l'aide, on propose des critères
            prompt = f"""{conversation_context}Question : {query}

Informations disponibles :
{chr(10).join([f"- {c['content'][:200]}" for c in chunks])}

Réponds de manière claire et structurée (2-3 paragraphes max).
TERMINE par une question pour affiner sa recherche : "Quelle ville vous intéresse ? Quel est votre budget maximum ?" """
        else:
            # MODE PROPOSITION : Proposition d'aide classique
            prompt = f"""{conversation_context}Question : {query}

Informations disponibles :
{chr(10).join([f"- {c['content'][:200]}" for c in chunks])}

Réponds de manière claire et structurée (2-3 paragraphes max).
TERMINE par une proposition d'aide : "Puis-je vous aider à  trouver un logement ?" """

        max_tokens = 400

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,  # Plus créatif pour l'agent commercial
        max_tokens=max_tokens
    )

    return response.choices[0].message.content.strip()

def summarize_chunks(chunks, query):
    # Détecter si ce sont des appartements ou des infos générales
    has_apartments = any(c.get('type') == 'appartement' for c in chunks)

    if has_apartments:
        # Pour les appartements : réponse très courte (les cards montrent tout)
        nb_apartments = len([c for c in chunks if c.get('type') == 'appartement'])

        # Extraire les villes disponibles
        cities = list(set([c.get('city', '') for c in chunks if c.get('type') == 'appartement']))
        cities_str = ", ".join(cities) if cities else ""

        prompt = f"""
Question utilisateur : {query}
Nombre d'appartements trouvés : {nb_apartments}
Villes disponibles : {cities_str}

RàˆGLE ABSOLUE : JAMAIS mentionner de concurrents (CROUS, LeBonCoin, Appartager, Colonies, etc.) !
On propose UNIQUEMENT nos propres appartements !

Ecris UNE phrase simple et directe. JAMAIS de "Bonjour" ou formule de politesse.

EXEMPLES :
- "Voici {nb_apartments} appartements disponibles à  {cities_str}."
- "{nb_apartments} logements correspondent à  votre recherche."

Si l'utilisateur cherchait une ville spécifique mais qu'on propose d'autres villes :
- "Voici {nb_apartments} appartements disponibles dans ces villes : {cities_str}."

Réponds en 1 phrase MAXIMUM :
"""
        max_tokens = 50
    else:
        # Pour les infos générales : réponse complète et détaillée
        # MAIS toujours orienter vers NOS services, pas la concurrence
        prompt = f"""
Tu es un assistant spécialisé dans le logement étudiant et coliving.

Question : {query}

Informations disponibles :
{chr(10).join([f"- {c['content'][:200]}" for c in chunks])}

RàˆGLE ABSOLUE : Réponds en utilisant UNIQUEMENT les informations fournies.
JAMAIS mentionner de concurrents (CROUS, LeBonCoin, Appartager, Colonies, etc.)

Réponds de manière claire, complète et structurée. Tu peux utiliser 2-3 paragraphes si nécessaire.
"""
        max_tokens = 400

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Tu es un conseiller en logement expert. Tu promeus UNIQUEMENT nos propres services, JAMAIS la concurrence."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content.strip()

@app.get("/")
def root():
    return {"status": "ok", "message": "API is running"}

@app.post("/search")
def search(req: QueryRequest):
    try:
        print(f"[SEARCH] Recherche recue: {req.query}")

        # ETAPE 0: Agent GPT analyse l'intention et extrait les critères EN TENANT COMPTE DE L'HISTORIQUE
        intent = analyze_user_intent(req.query, req.conversation_history)
        print(f"[GPT-INTENT] {intent.reasoning}")
        print(f"[GPT-INTENT] Recherche appartement: {intent.is_apartment_search}")
        print(f"[GPT-CRITERIA] budget_max={intent.criteria.max_budget}, ville={intent.criteria.city}, pieces={intent.criteria.rooms}, meuble={intent.criteria.furnished}")

        # Si ce n'est PAS une recherche d'appartement, forcer type=None
        if not intent.is_apartment_search:
            req.type = None
        else:
            # Si recherche d'appartement MAIS aucun critère â†’ forcer type="appartement" pour trouver des résultats
            if not intent.criteria.city and not intent.criteria.max_budget and not intent.criteria.rooms:
                req.type = "appartement"
                print("[INFO] Recherche d'appartement sans critères â†’ Forcer type='appartement' pour Qdrant")

        try:
            vector = embed(req.query)
        except Exception as e:
            print(f"[ERROR] Erreur embedding: {str(e)}")
            raise

        # ETAPE 1: Construire les filtres Qdrant avec les critères GPT
        filter_conditions = []

        if req.type:
            filter_conditions.append(FieldCondition(key="type", match=MatchValue(value=req.type)))

        # Filtre ville (extrait par GPT)
        # Gérer le mapping des ZONES â†’ villes multiples
        ZONE_MAPPING = {
            "Paris": ["Massy-Palaiseau", "Villejuif", "Noisy-le-Grand"],
            "Genève": ["Archamps"],
            "Lille": ["Lille"],
            "Bordeaux": ["Bordeaux"]
        }

        if intent.criteria.city:
            # Si c'est une ZONE, chercher dans toutes les villes de la zone
            if intent.criteria.city in ZONE_MAPPING:
                # On ne filtre PAS ici, le backend retournera toutes les villes et on filtrera après
                print(f"[INFO] Zone '{intent.criteria.city}' détectée â†’ recherche dans {ZONE_MAPPING[intent.criteria.city]}")
                # Ne pas ajouter de filtre, on récupère tout et on filtre après
            else:
                # Ville spécifique
                filter_conditions.append(FieldCondition(key="city", match=MatchValue(value=intent.criteria.city)))

        # Filtre meublé (extrait par GPT)
        if intent.criteria.furnished is not None:
            filter_conditions.append(FieldCondition(key="furnished", match=MatchValue(value=intent.criteria.furnished)))

        # Filtre nombre de pièces (extrait par GPT)
        if intent.criteria.rooms:
            filter_conditions.append(FieldCondition(key="rooms", match=MatchValue(value=intent.criteria.rooms)))

        filters = Filter(must=filter_conditions) if filter_conditions else None

        try:
            results = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=20,  # Augmenter pour avoir plus de résultats avant filtrage budget
                with_payload=True,
                query_filter=filters
            )
            print(f"[RESULTS] Trouve {len(results)} resultats")
        except Exception as e:
            print(f"[ERROR] Erreur Qdrant: {str(e)}")
            raise

        # Extraire les chunks avec toutes les métadonnées
        chunks = []
        apartments = []

        for r in results:
            payload = r.payload

            # Si c'est un appartement ET que c'est une recherche d'appartement
            if payload.get("type") == "appartement":
                # Si l'utilisateur ne cherche PAS d'appartement, skip
                if not intent.is_apartment_search:
                    continue

                rent = payload.get("rent_cc_eur", 0)

                # NOTE: On ne filtre PAS par budget ici pour permettre l'affichage de TOUTES les typologies d'une résidence
                # Le filtrage par budget sera appliqué APRàˆS le groupement par ville (ligne 655-657)
                # Cela permet de montrer toutes les typologies disponibles, et de masquer uniquement celles hors budget

                # Créer la card seulement si le budget est OK
                apartment_card = {
                    "id": payload.get("apartment_id", ""),
                    "typologie_id": payload.get("typologie_id", ""),
                    "city": payload.get("city", ""),
                    "rooms": payload.get("rooms", 1),
                    "surface_m2": payload.get("surface_m2", 0),
                    "furnished": payload.get("furnished", False),
                    "rent_cc_eur": rent,
                    "availability_date": payload.get("availability_date", ""),
                    "energy_label": payload.get("energy_label", ""),
                    "postal_code": payload.get("postal_code", ""),
                    "floor": payload.get("floor", 0),
                    "orientation": payload.get("orientation", "Nord"),
                    "bed_size": payload.get("bed_size", 140),
                    "has_ac": payload.get("has_ac", False),
                    "application_fee": payload.get("application_fee", 100),
                    "deposit_months": payload.get("deposit_months", 1),
                    "is_typologie": payload.get("is_typologie", False),
                    "content": payload["content"],
                    "score": r.score
                }
                apartments.append(apartment_card)

                # Créer aussi le chunk pour cet appartement
                chunk_data = {
                    "content": payload["content"],
                    "url": payload.get("url", ""),
                    "type": payload.get("type", ""),
                    "score": r.score
                }
                chunks.append(chunk_data)
            else:
                # Pour les non-appartements, ajouter le chunk normalement
                chunk_data = {
                    "content": payload["content"],
                    "url": payload.get("url", ""),
                    "type": payload.get("type", ""),
                "score": r.score
            }
                chunks.append(chunk_data)

        if req.summarize:
            print("[AI] Generation du resume IA...")

            # STRATEGIE COMMERCIALE : Si recherche appartement mais 0 résultat â†’ élargir automatiquement
            if intent.is_apartment_search and len(apartments) == 0:
                print("[FALLBACK] Aucun appartement trouvé, élargissement automatique...")

                # Elargir : retirer les filtres de ville ET augmenter le budget de 30%
                fallback_filters = []
                if req.type:
                    fallback_filters.append(FieldCondition(key="type", match=MatchValue(value=req.type)))

                # Garder seulement les critères non-budget
                if intent.criteria.furnished is not None:
                    fallback_filters.append(FieldCondition(key="furnished", match=MatchValue(value=intent.criteria.furnished)))
                if intent.criteria.rooms:
                    fallback_filters.append(FieldCondition(key="rooms", match=MatchValue(value=intent.criteria.rooms)))

                fallback_filter = Filter(must=fallback_filters) if fallback_filters else None

                # Nouvelle recherche élargie
                fallback_results = qdrant.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=vector,
                    limit=20,
                    with_payload=True,
                    query_filter=fallback_filter
                )
                print(f"[FALLBACK] {len(fallback_results)} résultats trouvés après élargissement")

                # Reconstruire apartments et chunks
                apartments = []
                chunks = []

                # Elargir le budget de 30% si spécifié
                expanded_budget = None
                if intent.criteria.max_budget:
                    expanded_budget = int(intent.criteria.max_budget * 1.3)
                    print(f"[FALLBACK] Budget élargi de {intent.criteria.max_budget}â‚¬ à  {expanded_budget}â‚¬")

                for r in fallback_results:
                    payload = r.payload
                    if payload.get("type") == "appartement":
                        rent = payload.get("rent_cc_eur", 0)

                        # Filtre budget élargi (ou pas de filtre si pas de budget)
                        if expanded_budget and rent > expanded_budget:
                            continue

                        apartment_card = {
                            "id": payload.get("apartment_id", ""),
                            "typologie_id": payload.get("typologie_id", ""),
                            "city": payload.get("city", ""),
                            "rooms": payload.get("rooms", 1),
                            "surface_m2": payload.get("surface_m2", 0),
                            "surface_min": payload.get("surface_min", 0),
                            "surface_max": payload.get("surface_max", 0),
                            "furnished": payload.get("furnished", False),
                            "rent_cc_eur": rent,
                            "availability_date": payload.get("availability_date", ""),
                            "energy_label": payload.get("energy_label", ""),
                            "postal_code": payload.get("postal_code", ""),
                            "floor": payload.get("floor", 0),
                            "orientation": payload.get("orientation", "Nord"),
                            "bed_size": payload.get("bed_size", 140),
                            "has_ac": payload.get("has_ac", False),
                            "application_fee": payload.get("application_fee", 100),
                            "deposit_months": payload.get("deposit_months", 1),
                            "is_typologie": payload.get("is_typologie", False),
                            "content": payload["content"],
                            "score": r.score
                        }
                        apartments.append(apartment_card)

                        chunk_data = {
                            "content": payload["content"],
                            "url": payload.get("url", ""),
                            "type": payload.get("type", ""),
                            "score": r.score
                        }
                        chunks.append(chunk_data)

            # Si on a des appartements, analyser les résidences disponibles
            if apartments:
                # Définir les ZONES géographiques
                ZONE_MAPPING = {
                    "Paris": ["Massy-Palaiseau", "Villejuif", "Noisy-le-Grand"],
                    "Genève": ["Archamps"],
                    "Lille": ["Lille"],
                    "Bordeaux": ["Bordeaux"]
                }

                # Si l'utilisateur a choisi une ZONE, filtrer les appartements par villes de la zone
                if intent.criteria.city and intent.criteria.city in ZONE_MAPPING:
                    zone_cities = ZONE_MAPPING[intent.criteria.city]
                    apartments = [apt for apt in apartments if apt['city'] in zone_cities]
                    print(f"[INFO] Filtrage par zone '{intent.criteria.city}': {len(apartments)} typologies dans {zone_cities}")

                # Extraire les villes uniques (après filtrage par zone si applicable)
                cities = list(set([apt['city'] for apt in apartments]))

                # Déterminer si l'utilisateur a choisi "flexible"
                is_flexible = req.query.lower() in ["je suis flexible", "flexible"] or "flexible" in req.query.lower()

                # Si plusieurs villes ET l'utilisateur n'a pas spécifié de ville/zone, proposer de choisir
                if len(cities) > 1 and not intent.criteria.city:
                    intro = generate_commercial_response(chunks, req.query, req.conversation_history)

                    # Si l'utilisateur a dit "flexible", proposer les ZONES
                    if is_flexible:
                        quick_replies = [
                            {"id": "paris", "label": "Paris", "value": "Paris"},
                            {"id": "geneve", "label": "Genève", "value": "Genève"},
                            {"id": "lille", "label": "Lille", "value": "Lille"},
                            {"id": "bordeaux", "label": "Bordeaux", "value": "Bordeaux"}
                        ]
                        print(f"[SUCCESS] Agent commercial - Proposition des ZONES géographiques")
                    else:
                        # Sinon, proposer les villes individuelles + flexible
                        quick_replies = [
                            {"id": city.lower().replace("-", "_"), "label": city, "value": city}
                            for city in sorted(cities)]
                        # Ajouter l'option "Flexible"
                        quick_replies.append({"id": "flexible", "label": "Je suis flexible", "value": "flexible"})
                        print(f"[SUCCESS] Agent commercial - {len(cities)} résidences disponibles avec quick replies")

                    return {
                        "answer": intro,
                        "quick_replies": quick_replies,
                        "apartments": [],
                        "has_apartments": False
                    }
                else:
                    # Une seule ville ou ville spécifiée
                    # NOUVEAU FLUX SIMPLIFIE : Afficher directement TOUTES les typologies
                    # Le budget est visible sur les cards, l'utilisateur choisit ensuite

                    intro = generate_commercial_response(chunks, req.query, req.conversation_history)

                    # Afficher toutes les typologies de la résidence (sans filtre de budget ni de rooms)
                    apartments_to_return = apartments

                    print(f"[SUCCESS] Agent commercial - Affichage direct de {len(apartments_to_return)} typologies")
                    return {
                        "answer": intro,
                        "apartments": apartments_to_return,
                        "residences_available": [],
                        "has_apartments": True
                    }

                    # ANCIEN CODE - On garde pour référence mais n'est plus exécuté
                    if False and intent.criteria.max_budget is None:
                        intro = generate_commercial_response(chunks, req.query, req.conversation_history)

                        # Proposer des tranches de budget
                        quick_replies = [
                            {"id": "budget_600", "label": "Moins de 600â‚¬", "value": "600"},
                            {"id": "budget_800", "label": "600-800â‚¬", "value": "800"},
                            {"id": "budget_1000", "label": "800-1000â‚¬", "value": "1000"},
                            {"id": "budget_1500", "label": "1000-1500â‚¬", "value": "1500"},
                            {"id": "budget_plus", "label": "Plus de 1500â‚¬", "value": "9999"},
                            {"id": "budget_flexible", "label": "Flexible", "value": "flexible"}
                        ]

                        print(f"[SUCCESS] Agent commercial - Demande du budget avant d'afficher les typologies")
                        return {
                            "answer": intro,
                            "quick_replies": quick_replies,
                            "apartments": [],
                            "has_apartments": False
                        }
                    else:
                        # Budget spécifié
                        # Si l'utilisateur n'a PAS précisé de typologie, lui demander AVANT d'afficher les cards
                        if intent.criteria.rooms is None:
                            intro = generate_commercial_response(chunks, req.query, req.conversation_history)

                            # Proposer les types de typologies disponibles dans cette ville/budget
                            # Analyser les typologies disponibles dans le budget
                            apartments_in_budget = [apt for apt in apartments if apt['rent_cc_eur'] <= intent.criteria.max_budget]

                            # Extraire les types uniques (Studio, T1, T2, etc.)
                            typologie_types = set()
                            for apt in apartments_in_budget:
                                rooms = apt['rooms']
                                if rooms == 0:
                                    typologie_types.add(("Colocation", 0, "ðŸ "))
                                elif rooms == 1:
                                    surface = apt.get('surface_m2', 0)
                                    if surface < 23:
                                        typologie_types.add(("Studio", 1, "ðŸ "))
                                    else:
                                        typologie_types.add(("T1", 1, "ðŸ "))
                                else:
                                    typologie_types.add((f"T{rooms}", rooms, "ðŸ "))

                            # Créer les quick replies pour les typologies
                            typologie_list = sorted(typologie_types, key=lambda x: x[1])
                            quick_replies = [
                                {"id": f"typo_{typ[0].lower()}", "label": typ[0], "value": typ[0]}
                                for typ in typologie_list
                            ]
                            # Ajouter "Tous" pour voir toutes les typologies
                            quick_replies.append({"id": "typo_all", "label": "Tous", "value": "all"})

                            print(f"[SUCCESS] Agent commercial - Proposition de {len(quick_replies)-1} types de typologies")
                            return {
                                "answer": intro,
                                "quick_replies": quick_replies,
                                "apartments": [],
                                "has_apartments": False
                            }
                        else:
                            # Typologie spécifiée ou "Tous"
                            # Vérifier si l'utilisateur a dit "Tous" ou "all"
                            is_all = "tous" in req.query.lower() or "all" in req.query.lower()

                            # Filtrer par budget
                            apartments_to_return = [apt for apt in apartments if apt['rent_cc_eur'] <= intent.criteria.max_budget]

                            # Filtrer par typologie si spécifié (sauf si "Tous")
                            if not is_all and intent.criteria.rooms is not None:
                                if intent.criteria.rooms == 1:
                                    # Pour rooms=1, il faut distinguer Studio et T1 par la surface
                                    # On laisse passer les deux, le frontend affichera correctement
                                    pass
                                else:
                                    apartments_to_return = [apt for apt in apartments_to_return if apt['rooms'] == intent.criteria.rooms]

                            excluded = len(apartments) - len(apartments_to_return)
                            filter_desc = "toutes typologies" if is_all else f"typologie rooms={intent.criteria.rooms}"
                            print(f"[INFO] Filtrage par budget {intent.criteria.max_budget}â‚¬ et {filter_desc}: {len(apartments_to_return)}/{len(apartments)} typologies affichées")

                            intro = generate_commercial_response(chunks, req.query, req.conversation_history)
                            print(f"[SUCCESS] Agent commercial - {len(apartments_to_return)} typologies affichées")
                            return {
                    "answer": intro,
                                "apartments": apartments_to_return,
                                "residences_available": [],
                    "has_apartments": True
                }
            else:
                # Agent commercial pour infos générales
                answer = generate_commercial_response(chunks, req.query, req.conversation_history)
                print("[SUCCESS] Agent commercial - infos générales")
                return {
                    "answer": answer,
                    "residences_available": [],
                    "has_apartments": False
                }

        return chunks
    except Exception as e:
        print(f"[ERROR] ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
