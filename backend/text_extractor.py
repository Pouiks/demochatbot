"""
Utilitaire pour extraire le texte de différents formats de fichiers
Supporte : PDF, DOCX, TXT
"""

import io
from typing import List
import PyPDF2
from docx import Document
import chardet


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extrait le texte d'un fichier PDF"""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = "\n\n".join(text_parts)
        return full_text.strip()
    except Exception as e:
        raise Exception(f"Erreur lors de l'extraction du PDF: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    """Extrait le texte d'un fichier DOCX"""
    try:
        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)
        
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        full_text = "\n\n".join(text_parts)
        return full_text.strip()
    except Exception as e:
        raise Exception(f"Erreur lors de l'extraction du DOCX: {str(e)}")


def extract_text_from_txt(file_content: bytes) -> str:
    """Extrait le texte d'un fichier TXT (détection automatique de l'encodage)"""
    try:
        # Détecter l'encodage
        detected = chardet.detect(file_content)
        encoding = detected['encoding'] or 'utf-8'
        
        text = file_content.decode(encoding)
        return text.strip()
    except Exception as e:
        raise Exception(f"Erreur lors de l'extraction du TXT: {str(e)}")


def extract_text_from_file(filename: str, file_content: bytes) -> str:
    """
    Extrait le texte d'un fichier en fonction de son extension
    
    Args:
        filename: Nom du fichier (avec extension)
        file_content: Contenu binaire du fichier
    
    Returns:
        Texte extrait du fichier
    
    Raises:
        ValueError: Si le format n'est pas supporté
        Exception: Si l'extraction échoue
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_content)
    elif filename_lower.endswith('.docx'):
        return extract_text_from_docx(file_content)
    elif filename_lower.endswith('.txt'):
        return extract_text_from_txt(file_content)
    else:
        raise ValueError(f"Format de fichier non supporté: {filename}. Formats acceptés: PDF, DOCX, TXT")


def chunk_text(text: str, max_length: int = 500, overlap: int = 50) -> List[str]:
    """
    Découpe un texte long en chunks intelligents
    
    Args:
        text: Texte à découper
        max_length: Longueur maximale d'un chunk (en caractères)
        overlap: Nombre de caractères de chevauchement entre chunks
    
    Returns:
        Liste de chunks de texte
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    sentences = text.replace('\n', ' ').split('. ')
    
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Ajouter le point manquant
        if not sentence.endswith('.'):
            sentence += '.'
        
        # Si ajouter cette phrase dépasse la limite
        if len(current_chunk) + len(sentence) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Chevauchement : prendre les derniers mots
                words = current_chunk.split()
                overlap_words = ' '.join(words[-10:]) if len(words) > 10 else current_chunk
                current_chunk = overlap_words + ' ' + sentence
            else:
                # Phrase trop longue, on la garde quand même
                chunks.append(sentence)
                current_chunk = ""
        else:
            current_chunk += ' ' + sentence if current_chunk else sentence
    
    # Ajouter le dernier chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def extract_and_chunk_file(filename: str, file_content: bytes, max_chunk_length: int = 500) -> List[str]:
    """
    Pipeline complet : extrait le texte et le découpe en chunks
    
    Args:
        filename: Nom du fichier
        file_content: Contenu binaire du fichier
        max_chunk_length: Longueur maximale d'un chunk
    
    Returns:
        Liste de chunks de texte prêts à être indexés
    """
    # Extraire le texte
    text = extract_text_from_file(filename, file_content)
    
    # Vérifier que le texte n'est pas vide
    if not text or len(text.strip()) < 10:
        raise ValueError("Le fichier ne contient pas assez de texte exploitable")
    
    # Découper en chunks
    chunks = chunk_text(text, max_length=max_chunk_length)
    
    return chunks

