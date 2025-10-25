"""
Script de test pour text_extractor.py
Pour tester : python test_extractor.py
"""

import os
import sys

def test_txt_extraction():
    """Test d'extraction de fichier TXT"""
    print("\n🧪 Test 1: Extraction TXT")
    print("-" * 50)
    
    from text_extractor import extract_text_from_txt
    
    # Créer un fichier TXT de test
    test_content = """Bienvenue chez ECLA

ECLA est une plateforme de réservation de logements étudiants.
Nous proposons des studios, T2 et T3 dans plusieurs villes françaises.

Nos services incluent:
- Aide à la réservation
- Support 24/7
- Garantie de satisfaction
"""
    
    try:
        text = extract_text_from_txt(test_content.encode('utf-8'))
        print(f"✅ Extraction réussie: {len(text)} caractères")
        print(f"Extrait: {text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_chunking():
    """Test du découpage en chunks"""
    print("\n🧪 Test 2: Découpage en chunks")
    print("-" * 50)
    
    from text_extractor import chunk_text
    
    long_text = """
    ECLA propose des logements étudiants meublés dans plusieurs villes de France.
    Nos appartements sont modernes, bien équipés et situés à proximité des transports.
    
    Nous offrons trois types de logements: les studios (T1) pour une personne, 
    les T2 pour deux personnes, et les T3 pour les colocations de trois personnes.
    
    Chaque logement dispose d'une connexion Internet haut débit, d'une cuisine équipée,
    et d'une salle de bain privative. Le chauffage et l'eau sont inclus dans le loyer.
    
    Pour réserver, il suffit de créer un compte sur notre plateforme, de choisir
    votre logement, et de valider votre réservation en ligne. Nous vous accompagnons
    tout au long du processus.
    """ * 3  # Répéter pour avoir un texte long
    
    try:
        chunks = chunk_text(long_text, max_length=300)
        print(f"✅ {len(chunks)} chunks créés")
        for i, chunk in enumerate(chunks[:3]):  # Afficher les 3 premiers
            print(f"\nChunk {i+1} ({len(chunk)} caractères):")
            print(f"{chunk[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_full_pipeline():
    """Test du pipeline complet avec un fichier TXT"""
    print("\n🧪 Test 3: Pipeline complet")
    print("-" * 50)
    
    from text_extractor import extract_and_chunk_file
    
    test_content = """
    Politique de Remboursement ECLA
    
    Conditions générales de remboursement:
    
    1. Remboursement intégral:
       - Annulation plus de 30 jours avant l'arrivée
       - Remboursement à 100% du montant payé
    
    2. Remboursement partiel:
       - Annulation entre 15 et 30 jours avant l'arrivée
       - Remboursement à 50% du montant payé
    
    3. Aucun remboursement:
       - Annulation moins de 15 jours avant l'arrivée
       - Sauf en cas de force majeure (maladie, accident)
    
    4. Force majeure:
       - Remboursement intégral sur présentation de justificatifs
       - Traitement sous 48h
    
    Contact: remboursement@ecla.com
    """ * 2
    
    try:
        chunks = extract_and_chunk_file(
            filename="test_politique.txt",
            file_content=test_content.encode('utf-8'),
            max_chunk_length=400
        )
        print(f"✅ Pipeline réussi: {len(chunks)} chunks créés")
        print(f"\nPremier chunk:")
        print(chunks[0])
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_file_validation():
    """Test de la validation des formats de fichiers"""
    print("\n🧪 Test 4: Validation des formats")
    print("-" * 50)
    
    from text_extractor import extract_text_from_file
    
    # Test avec un format non supporté
    try:
        extract_text_from_file("test.mp3", b"fake content")
        print("❌ La validation a échoué (devrait rejeter .mp3)")
        return False
    except ValueError as e:
        print(f"✅ Format rejeté correctement: {e}")
        return True
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


def test_empty_content():
    """Test avec du contenu vide"""
    print("\n🧪 Test 5: Gestion du contenu vide")
    print("-" * 50)
    
    from text_extractor import extract_and_chunk_file
    
    try:
        chunks = extract_and_chunk_file("empty.txt", b"   \n\n   ")
        print("❌ Devrait rejeter le contenu vide")
        return False
    except ValueError as e:
        print(f"✅ Contenu vide rejeté: {e}")
        return True
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


def run_all_tests():
    """Exécuter tous les tests"""
    print("=" * 50)
    print("🚀 Tests de text_extractor.py")
    print("=" * 50)
    
    tests = [
        ("Extraction TXT", test_txt_extraction),
        ("Chunking", test_chunking),
        ("Pipeline complet", test_full_pipeline),
        ("Validation formats", test_file_validation),
        ("Contenu vide", test_empty_content),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' a planté: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{status} - {name}")
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés !")
        return 0
    else:
        print(f"⚠️ {total - passed} test(s) ont échoué")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

