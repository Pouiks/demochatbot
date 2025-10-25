"""
Générateur de typologies ECLA
Génère des typologies représentatives pour chaque résidence (Studio, T1, T2, T3, T4, Colocation)
"""
import json
import os
from datetime import datetime, timedelta
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Villes ECLA avec caractéristiques
CITIES = [
    {
        "city": "Massy-Palaiseau",
        "postal_code": "91300",
        "avg_price_m2": 30,
        "description": "Proche Polytechnique et CentraleSupélec, quartier technologique",
        "transport": "RER B"
    },
    {
        "city": "Villejuif",
        "postal_code": "94800",
        "avg_price_m2": 32,
        "description": "Campus santé IGR, accès rapide Paris",
        "transport": "Métro ligne 7"
    },
    {
        "city": "Noisy-le-Grand",
        "postal_code": "93160",
        "avg_price_m2": 28,
        "description": "Mont d'Est, quartier dynamique",
        "transport": "RER A"
    },
    {
        "city": "Archamps",
        "postal_code": "74160",
        "avg_price_m2": 35,
        "description": "Proche Genève, frontaliers suisses, technopôle",
        "transport": "Navette Genève"
    },
    {
        "city": "Lille",
        "postal_code": "59000",
        "avg_price_m2": 27,
        "description": "Centre ville, universités, quartier étudiant",
        "transport": "Métro, Tramway"
    },
    {
        "city": "Bordeaux",
        "postal_code": "33000",
        "avg_price_m2": 29,
        "description": "Campus Talence, quartier historique",
        "transport": "Tramway"
    }
]

# Typologies d'appartements avec surfaces fixes par type
TYPOLOGIE_TYPES = [
    {
        "type": "Studio",
        "rooms": 1,
        "surface_range": (16, 23),  # Range pour variation
        "base_services": ["wifi fibre", "espace coworking", "laverie"],
        "is_colocation": False
    },
    {
        "type": "T1",
        "rooms": 1,
        "surface_range": (20, 30),
        "base_services": ["wifi fibre", "espace coworking", "laverie", "kitchenette équipée"],
        "is_colocation": False
    },
    {
        "type": "T2",
        "rooms": 2,
        "surface_range": (35, 45),
        "base_services": ["wifi fibre", "salle de sport", "espace coworking", "laverie"],
        "is_colocation": False
    },
    {
        "type": "T3",
        "rooms": 3,
        "surface_range": (50, 65),
        "base_services": ["wifi fibre", "salle de sport", "espace coworking", "laverie", "parking"],
        "is_colocation": False
    },
    {
        "type": "T4",
        "rooms": 4,
        "surface_range": (65, 85),
        "base_services": ["wifi fibre", "salle de sport", "espace coworking", "laverie", "parking", "terrasse"],
        "is_colocation": False
    },
    {
        "type": "Colocation",
        "rooms": 0,  # 0 pour colocation
        "surface_range": (25, 50),
        "base_services": ["wifi fibre", "salle de sport", "espace coworking", "laverie", "cuisine partagée"],
        "is_colocation": True
    }
]

# Services optionnels aléatoires
OPTIONAL_SERVICES = [
    "balcon", "parking", "cave", "terrasse", "vue dégagée", 
    "cuisine équipée", "dressing", "salle de bain avec baignoire"
]

# Orientations possibles
ORIENTATIONS = ["Nord", "Sud", "Est", "Ouest"]

def get_bed_size(city, typologie_type):
    """Déterminer la taille du lit selon les règles"""
    is_studio = typologie_type['type'] == "Studio"
    is_villejuif = city == "Villejuif"
    
    if is_studio and is_villejuif:
        return 90  # Lit 90 pour studios Villejuif
    elif is_studio:
        return 120  # Lit 120 pour autres studios
    else:
        return 140  # Lit 140 pour T2+

def has_air_conditioning(city, typologie_type):
    """Déterminer si la typologie a la climatisation"""
    # Climatisation uniquement pour T2, T3, T4, Colocation à Noisy-le-Grand, Archamps, Bordeaux
    eligible_cities = ["Noisy-le-Grand", "Archamps", "Bordeaux"]
    eligible_types = ["T2", "T3", "T4", "Colocation"]
    
    return city in eligible_cities and typologie_type['type'] in eligible_types

def generate_availability_date():
    """Générer une date de disponibilité réaliste"""
    today = datetime.now()
    # 40% dispo immédiate, 30% dans 1 mois, 20% dans 2-3 mois, 10% dans 4-6 mois
    days_ahead = random.choices(
        [0, 30, 60, 90, 120, 180],
        weights=[40, 30, 15, 10, 3, 2]
    )[0]
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

def calculate_price(surface, price_per_m2, typologie_type):
    """Calculer le loyer de manière réaliste et cohérente (100% meublé)"""
    # Prix de base : surface × prix au m²
    base_price = surface * price_per_m2
    
    # Ajustements selon le type (grands logements = léger dégressif au m²)
    if typologie_type['rooms'] >= 3:
        base_price *= 0.92  # -8% pour T3
    elif typologie_type['rooms'] >= 4:
        base_price *= 0.88  # -12% pour T4
    
    # Tous meublés : +10% en moyenne
    base_price *= random.uniform(1.08, 1.12)
    
    # Variation aléatoire ±5%
    base_price *= random.uniform(0.95, 1.05)
    
    # Charges forfaitaires réalistes
    rooms_for_charges = max(typologie_type['rooms'], 1)  # Min 1 pour colocation
    charges = 50 + (rooms_for_charges - 1) * 15  # 50€ base + 15€/pièce suppl
    
    # Prix total
    total_price = base_price + charges
    
    # Arrondir à la dizaine
    total_price = int(total_price / 10) * 10
    
    return total_price

def generate_typologie_description(city_info, typologie_type, surface, price, availability, services, bed_size, has_ac, floor, orientation):
    """Générer une description pour une typologie"""
    rooms_display = typologie_type['rooms'] if typologie_type['rooms'] > 0 else "Colocation"
    type_name = typologie_type['type']
    
    # Construire description avec tous les détails
    ac_text = " Climatisation incluse." if has_ac else ""
    bed_text = f"Lit {bed_size}cm."
    
    templates = [
        f"Typologie {type_name} à {city_info['city']} ({city_info['postal_code']}) : {surface}m² meublé, étage {floor}, orientation {orientation}. {bed_text}{ac_text} Services : {', '.join(services[:4])}. Loyer : {price}€/mois CC. Résidence ECLA {city_info['city']}. {city_info['description']}.",
        
        f"{type_name} {surface}m² meublé - ECLA {city_info['city']}. Étage {floor}, exposition {orientation}. {bed_text}{ac_text} Équipements : {', '.join(services[:3])}. {price}€/mois CC. Accès {city_info['transport']}.",
        
        f"Résidence ECLA {city_info['city']} : Typologie {type_name} de {surface}m² meublée. Étage {floor} ({orientation}). {bed_text}{ac_text} Services : {', '.join(services[:4])}. {price}€/mois CC."
    ]
    
    return random.choice(templates)

def generate_typologies():
    """Générer les typologies pour chaque résidence"""
    all_typologies = []
    typologie_id_counter = 1
    
    print(f"🏠 Génération de typologies ECLA pour {len(CITIES)} résidences\n")
    
    for city_info in CITIES:
        city_slug = city_info['city'].lower().replace(" ", "-").replace("é", "e")
        print(f"📍 {city_info['city']} : Génération de {len(TYPOLOGIE_TYPES)} typologies...")
        
        for typologie_type in TYPOLOGIE_TYPES:
            # Surface moyenne pour cette typologie
            surface = random.randint(*typologie_type['surface_range'])
            
            # Calculer prix (100% meublé)
            price = calculate_price(surface, city_info['avg_price_m2'], typologie_type)
            
            # Date de disponibilité
            availability = generate_availability_date()
            
            # Services (base + quelques optionnels)
            services = typologie_type['base_services'].copy()
            num_optional = random.randint(0, 2)
            if num_optional > 0:
                services.extend(random.sample(OPTIONAL_SERVICES, min(num_optional, len(OPTIONAL_SERVICES))))
            
            # Classe énergie (majorité B, quelques A et C)
            energy_label = random.choices(['A', 'B', 'C', 'D'], weights=[15, 60, 20, 5])[0]
            
            # Nouveaux champs pour typologies
            floor = random.randint(0, 10)
            orientation = random.choice(ORIENTATIONS)
            bed_size = get_bed_size(city_info['city'], typologie_type)
            has_ac = has_air_conditioning(city_info['city'], typologie_type)
            
            # ID unique pour la typologie
            type_slug = typologie_type['type'].lower().replace(" ", "-")
            typologie_id = f"{city_slug}-{type_slug}"
            
            # Description
            description = generate_typologie_description(
                city_info, typologie_type, surface, price, availability, 
                services, bed_size, has_ac, floor, orientation
            )
            
            # Construire la typologie
            typologie = {
                "id": f"ecla-typo-{typologie_id_counter:04d}",
                "text": description,
                "metadata": {
                    "typologie_id": typologie_id,
                    "city": city_info['city'],
                    "postal_code": city_info['postal_code'],
                    "rooms": typologie_type['rooms'],
                    "surface_m2": float(surface),
                    "surface_min": float(typologie_type['surface_range'][0]),  # Range minimum
                    "surface_max": float(typologie_type['surface_range'][1]),  # Range maximum
                    "furnished": True,  # 100% meublé
                    "rent_cc_eur": float(price),
                    "availability_date": availability,
                    "energy_label": energy_label,
                    "residence_name": f"ECLA {city_info['city']}",
                    "is_typologie": True,
                    "floor": floor,
                    "orientation": orientation,
                    "bed_size": bed_size,
                    "has_ac": has_ac,
                    "application_fee": 100,  # Frais de dossier fixes
                    "deposit_months": 1,  # Garantie fixe
                    "synthesized": True
                }
            }
            
            all_typologies.append(typologie)
            typologie_id_counter += 1
        
        print(f"   ✅ {len(TYPOLOGIE_TYPES)} typologies générées pour {city_info['city']}")
    
    return all_typologies

def save_typologies(typologies, filename="typologies_ecla.jsonl"):
    """Sauvegarder les typologies en JSONL"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for typo in typologies:
            f.write(json.dumps(typo, ensure_ascii=False) + '\n')
    
    print(f"\n✅ {len(typologies)} typologies sauvegardées dans {filename}")
    
    # Statistiques
    print("\n📊 Statistiques :")
    by_city = {}
    by_type = {}
    with_ac = 0
    prices = [typo['metadata']['rent_cc_eur'] for typo in typologies]
    bed_sizes = {}
    
    for typo in typologies:
        city = typo['metadata']['city']
        rooms = typo['metadata']['rooms']
        by_city[city] = by_city.get(city, 0) + 1
        
        # Type name
        if rooms == 0:
            type_name = "Colocation"
        elif rooms == 1:
            type_name = "Studio/T1"
        else:
            type_name = f"T{rooms}"
        by_type[type_name] = by_type.get(type_name, 0) + 1
        
        # Climatisation
        if typo['metadata']['has_ac']:
            with_ac += 1
        
        # Taille de lit
        bed = typo['metadata']['bed_size']
        bed_sizes[bed] = bed_sizes.get(bed, 0) + 1
    
    print("\n  Par ville :")
    for city, count in sorted(by_city.items()):
        print(f"    - {city}: {count} typologies")
    
    print("\n  Par type :")
    for type_name, count in sorted(by_type.items()):
        print(f"    - {type_name}: {count}")
    
    print(f"\n  Avec climatisation : {with_ac}/{len(typologies)}")
    
    print("\n  Tailles de lit :")
    for bed, count in sorted(bed_sizes.items()):
        print(f"    - Lit {bed}cm : {count}")
    
    print(f"\n  Prix (CC) :")
    print(f"    - Min: {min(prices):.0f}€")
    print(f"    - Max: {max(prices):.0f}€")
    print(f"    - Moyen: {sum(prices)/len(prices):.0f}€")
    
    print(f"\n  Tous meublés : 100%")
    print(f"  Frais de dossier : 100€ (fixe)")
    print(f"  Garantie : 1 mois de loyer (fixe)")

if __name__ == "__main__":
    print("=" * 60)
    print("  GÉNÉRATEUR DE TYPOLOGIES ECLA")
    print("=" * 60)
    print()
    
    typologies = generate_typologies()
    save_typologies(typologies)
    
    print("\n" + "=" * 60)
    print("✅ Génération terminée !")
    print("=" * 60)
    print("\n📝 Prochaine étape : Ingérer dans Qdrant")
    print("   python ingest_apartments.py typologies_ecla.jsonl")
    print()

