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
        "❌ OPENAI_API_KEY non trouvée!\n"
        "   → Vérifier que backend/.env contient: OPENAI_API_KEY=votre-cle\n"
        "   → Pour Railway: configurer la variable dans le Dashboard"
    )

openai_client = OpenAI(api_key=openai_api_key)

# Configuration Qdrant adaptable (local vs production)
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
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

def analyze_user_intent(query: str) -> IntentAnalysis:
    """
    Agent GPT qui analyse l'intention utilisateur et extrait les critères structurés
    """
    system_prompt = """Tu es un agent d'analyse de requêtes pour une plateforme de logement étudiant.

Ta mission : analyser la question de l'utilisateur et déterminer :
1. Est-ce une recherche d'appartement EXPLICITE ? (true/false)
2. Si oui, extraire TOUS les critères mentionnés

RÈGLES STRICTES :
- is_apartment_search=true UNIQUEMENT si l'utilisateur cherche un logement/appartement/studio/chambre/toit
- is_apartment_search=false pour les questions sur services, forfaits, marque, activités, équipements
- Extraire TOUS les critères : ville, budget, pièces, surface, meublé

EXEMPLES :
❌ "c'est quoi les forfaits red de chez sfr ?" → is_apartment_search: false
❌ "quels sont les services chez ECLA ?" → is_apartment_search: false
✅ "j'ai besoin de trouver un toit à moins de 500 euros à paris" → is_apartment_search: true, max_budget: 500, city: "Paris"
✅ "je cherche un T2 meublé à Lyon" → is_apartment_search: true, rooms: 2, city: "Lyon", furnished: true
✅ "studio pas cher disponible ?" → is_apartment_search: true

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
    "rooms": null ou nombre (1=studio)
  },
  "reasoning": "Courte explication de ton analyse"
}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question utilisateur : {query}"}
            ],
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
            rooms=result_json["criteria"].get("rooms")
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
    
    # Détecter si l'utilisateur a déjà accepté l'aide
    user_accepted_help = False
    if conversation_history:
        recent_messages = [msg.get('content', '').lower() for msg in conversation_history[-3:]]
        acceptance_keywords = ['oui', 'yes', 'd\'accord', 'ok', 'parfait', 'montre', 'montrez', 'voir', 'montre-moi', 'montrez-moi']
        user_accepted_help = any(keyword in msg for msg in recent_messages for keyword in acceptance_keywords)
        print(f"[AGENT-COMMERCIAL] User accepted help: {user_accepted_help}")
    
    # Détecter si l'utilisateur demande explicitement à voir des appartements
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

TON RÔLE :
- Accompagner le client comme un vrai commercial (chaleureux, proactif, orienté solution)
- Proposer UNIQUEMENT nos appartements (JAMAIS la concurrence)
- Poser des questions pour affiner les besoins
- Guider vers la réservation

IMPORTANT - COLLABORATION AVEC LE SYSTÈME :
Tu travailles en collaboration avec un système d'affichage d'appartements. Tu sais que :
- Tu peux déclencher l'affichage des appartements quand c'est pertinent
- Les appartements s'affichent sous forme de cartes visuelles
- Tu dois préparer le client avant de montrer les appartements
- Tu dois expliquer ce qu'il va voir

RÈGLES STRICTES :
❌ JAMAIS mentionner : CROUS, LeBonCoin, Appartager, Colonies, SeLoger
❌ JAMAIS dire "je ne peux pas vous aider"
✅ TOUJOURS proposer des alternatives
✅ TOUJOURS poser une question de relance
✅ Être concis (2-3 phrases max)
✅ Préparer le client avant de montrer les appartements

EXEMPLES :
❌ "Malheureusement, je n'ai rien à Paris."
✅ "Je n'ai pas d'appartements à Paris dans ce budget, par contre j'ai 5 studios à Lille à partir de 232€. Lille est très bien desservie et dynamique. Souhaitez-vous que je vous les montre ?"

❌ "Voici 12 appartements."
✅ "J'ai 12 appartements pour vous ! Le plus économique est à 226€ à Lille. Avez-vous une préférence de ville ?"
"""

        # Logique intelligente selon le contexte
        if user_wants_apartments and user_accepted_help:
            # MODE AFFICHAGE : L'utilisateur veut voir les appartements ET a accepté l'aide
            print(f"[AGENT-COMMERCIAL] Mode: AFFICHAGE (user wants apartments + accepted help)")
            prompt = f"""{conversation_context}Question actuelle : {query}

RÉSULTATS TROUVÉS :
- {nb_apartments} appartements disponibles
- Villes : {cities_str}
- Prix : de {min_price:.0f}€ à {max_price:.0f}€

CONSIGNES (MODE AFFICHAGE) :
1. Annonce que tu vas montrer les appartements (1 phrase)
2. Prépare le client : "Voici les appartements qui correspondent le mieux à votre recherche"
3. TERMINE par une question pour la suite :
   "Quel appartement vous intéresse le plus ?" 
   "Avez-vous des questions sur l'un de ces logements ?"
   "Souhaitez-vous que je vous aide à réserver ?"

Réponds :"""
        elif user_accepted_help:
            # MODE ACTION COMMERCIALE : L'utilisateur a accepté l'aide mais veut d'abord affiner
            print(f"[AGENT-COMMERCIAL] Mode: AFFINAGE (user accepted help but wants to refine)")
            prompt = f"""{conversation_context}Question actuelle : {query}

RÉSULTATS TROUVÉS :
- {nb_apartments} appartements disponibles
- Villes : {cities_str}
- Prix : de {min_price:.0f}€ à {max_price:.0f}€

CONSIGNES (MODE AFFINAGE) :
1. Présente les résultats de manière engageante (2-3 phrases)
2. Souligne le meilleur rapport qualité/prix
3. TERMINE par une question PRÉCISE pour affiner AVANT de montrer les appartements :
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

RÉSULTATS TROUVÉS :
- {nb_apartments} appartements disponibles
- Villes : {cities_str}
- Prix : de {min_price:.0f}€ à {max_price:.0f}€

CONSIGNES (MODE PROPOSITION) :
1. Présente les résultats de manière engageante (2-3 phrases)
2. Souligne le meilleur rapport qualité/prix
3. TERMINE par une proposition d'aide :
   "Puis-je vous aider à trouver un logement qui correspond à vos critères et à votre budget ?"

Réponds :"""

        max_tokens = 150
        
    else:
        # Pour les infos générales
        system_prompt = """Tu es Sarah, conseillère en logement chez ECLA.

TON RÔLE :
- Répondre aux questions sur nos services, résidences, offres
- Être concis et informatif
- Orienter vers la recherche d'appartements si pertinent

COLLABORATION :
Tu travailles avec un système d'affichage d'appartements. Tu peux déclencher l'affichage quand c'est pertinent.

RÈGLES :
❌ JAMAIS mentionner la concurrence
✅ Utiliser UNIQUEMENT les informations fournies
✅ TOUJOURS proposer d'aider à trouver un logement à la fin"""

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
TERMINE par une proposition d'aide : "Puis-je vous aider à trouver un logement ?" """

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

RÈGLE ABSOLUE : JAMAIS mentionner de concurrents (CROUS, LeBonCoin, Appartager, Colonies, etc.) ! 
On propose UNIQUEMENT nos propres appartements !

Écris UNE phrase simple et directe. JAMAIS de "Bonjour" ou formule de politesse.

EXEMPLES :
- "Voici {nb_apartments} appartements disponibles à {cities_str}."
- "{nb_apartments} logements correspondent à votre recherche."

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

RÈGLE ABSOLUE : Réponds en utilisant UNIQUEMENT les informations fournies.
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
        
        # ÉTAPE 0: Agent GPT analyse l'intention et extrait les critères
        intent = analyze_user_intent(req.query)
        print(f"[GPT-INTENT] {intent.reasoning}")
        print(f"[GPT-INTENT] Recherche appartement: {intent.is_apartment_search}")
        print(f"[GPT-CRITERIA] budget_max={intent.criteria.max_budget}, ville={intent.criteria.city}, pieces={intent.criteria.rooms}, meuble={intent.criteria.furnished}")
        
        # Si ce n'est PAS une recherche d'appartement, forcer type=None
        if not intent.is_apartment_search:
            req.type = None
        
        try:
            vector = embed(req.query)
        except Exception as e:
            print(f"[ERROR] Erreur embedding: {str(e)}")
            raise
            
        # ÉTAPE 1: Construire les filtres Qdrant avec les critères GPT
        filter_conditions = []

        if req.type:
            filter_conditions.append(FieldCondition(key="type", match=MatchValue(value=req.type)))
        
        # Filtre ville (extrait par GPT)
        if intent.criteria.city:
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
                
                # Filtre budget max (extrait par GPT)
                if intent.criteria.max_budget is not None and rent > intent.criteria.max_budget:
                    print(f"[FILTER] Appartement exclu (budget): {rent}€ > {intent.criteria.max_budget}€")
                    continue
                
                # Filtre budget min (extrait par GPT)
                if intent.criteria.min_budget is not None and rent < intent.criteria.min_budget:
                    print(f"[FILTER] Appartement exclu (budget min): {rent}€ < {intent.criteria.min_budget}€")
                    continue
                
                # Filtre surface min (extrait par GPT)
                if intent.criteria.min_surface is not None and payload.get("surface_m2", 0) < intent.criteria.min_surface:
                    print(f"[FILTER] Appartement exclu (surface): {payload.get('surface_m2')}m² < {intent.criteria.min_surface}m²")
                    continue
                
                # Créer la card seulement si le budget est OK
                apartment_card = {
                    "id": payload.get("apartment_id", ""),
                    "city": payload.get("city", ""),
                    "rooms": payload.get("rooms", 1),
                    "surface_m2": payload.get("surface_m2", 0),
                    "furnished": payload.get("furnished", False),
                    "rent_cc_eur": rent,
                    "availability_date": payload.get("availability_date", ""),
                    "energy_label": payload.get("energy_label", ""),
                    "postal_code": payload.get("postal_code", ""),
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
            
            # STRATÉGIE COMMERCIALE : Si recherche appartement mais 0 résultat → élargir automatiquement
            if intent.is_apartment_search and len(apartments) == 0:
                print("[FALLBACK] Aucun appartement trouvé, élargissement automatique...")
                
                # Élargir : retirer les filtres de ville ET augmenter le budget de 30%
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
                
                # Élargir le budget de 30% si spécifié
                expanded_budget = None
                if intent.criteria.max_budget:
                    expanded_budget = int(intent.criteria.max_budget * 1.3)
                    print(f"[FALLBACK] Budget élargi de {intent.criteria.max_budget}€ à {expanded_budget}€")
                
                for r in fallback_results:
                    payload = r.payload
                    if payload.get("type") == "appartement":
                        rent = payload.get("rent_cc_eur", 0)
                        
                        # Filtre budget élargi (ou pas de filtre si pas de budget)
                        if expanded_budget and rent > expanded_budget:
                            continue
                        
                        apartment_card = {
                            "id": payload.get("apartment_id", ""),
                            "city": payload.get("city", ""),
                            "rooms": payload.get("rooms", 1),
                            "surface_m2": payload.get("surface_m2", 0),
                            "furnished": payload.get("furnished", False),
                            "rent_cc_eur": rent,
                            "availability_date": payload.get("availability_date", ""),
                            "energy_label": payload.get("energy_label", ""),
                            "postal_code": payload.get("postal_code", ""),
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
            
            # Si on a des appartements, retourner un format mixte
            if apartments:
                # Agent commercial avec contexte conversationnel
                intro = generate_commercial_response(chunks, req.query, req.conversation_history)
                print(f"[SUCCESS] Agent commercial - {len(apartments)} appartements")
                return {
                    "answer": intro,
                    "apartments": apartments,
                    "has_apartments": True
                }
            else:
                # Agent commercial pour infos générales
                answer = generate_commercial_response(chunks, req.query, req.conversation_history)
                print("[SUCCESS] Agent commercial - infos générales")
                return {
                    "answer": answer,
                    "has_apartments": False
                }

        return chunks
    except Exception as e:
        print(f"[ERROR] ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
