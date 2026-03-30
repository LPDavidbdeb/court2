import warnings
# Suppress the FutureWarning from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

import google.generativeai as genai
from django.conf import settings
import fitz  # PyMuPDF
import PIL.Image
import json
from .utils import EvidenceFormatter

# 1. Define the Personas
AI_PERSONAS = {
    'forensic_clerk': {
        'name': 'Greffier Forensique (Description Visuelle)',
        'prompt': """
        RÔLE : Greffier forensique.
        TÂCHE : Décris ce document de manière exhaustive pour qu'un tiers puisse comprendre son contenu sans le voir.
        INSTRUCTIONS :
        1. Décris la scène, les personnes et l'ambiance.
        2. Rapporte les faits visuels bruts sans opinion.
        3. Si texte visible, résume les points clés.
        FORMAT : Texte structuré.
        """
    },
    'official_scribe': {
        'name': 'Scribe Officiel (Transcription PDF)',
        'prompt': """
        RÔLE : Scribe officiel / Transcripteur juridique.
        TÂCHE : Transcris le contenu textuel de ce document avec une précision absolue (mot pour mot).
        INSTRUCTIONS CRITIQUES :
        1. AUCUNE INTERPRÉTATION ou résumé.
        2. Conserve le formatage structurel (Titres, paragraphes, listes à puces) pour que le texte soit lisible.
        3. Si le texte est illisible, marque [Illisible].
        4. Le but est de substituer ce texte au document original dans un rapport légal.
        FORMAT DE SORTIE : Markdown propre.
        """
    },
    'summary_clerk': {
        'name': 'Secrétaire de Synthèse (Résumé)',
        'prompt': """
        RÔLE : Secrétaire juridique senior.
        TÂCHE : Fais un résumé exécutif de ce document.
        INSTRUCTIONS :
        1. Identifie les dates clés.
        2. Identifie les acteurs principaux.
        3. Résume l'enjeu ou le contenu en 3-4 points.
        """
    },
    'media_editor': {
        'name': 'Éditeur Média (Correction & Sympathie)',
        'model': 'gemini-flash-latest', # Updated to an available model
        'prompt': """
        RÔLE : Éditeur de contenu spécialisé dans la communication médiatique et la narration engageante.
        TÂCHE : Réviser le texte pour maximiser son impact, générer de l'intérêt et de la sympathie, tout en assurant une clarté et une correction impeccables du français.
        CONTEXTE ADDITIONNEL : Le texte que tu corriges s'inscrit dans une structure narrative plus large. Voici un aperçu de cette structure pour t'aider à saisir le flux logique :
        {tree_structure}

        TEXTE À CORRIGER (peut contenir du HTML) :
        {text_to_correct}

        INSTRUCTIONS :
        1.  **Correction et Style** : Corrige toute erreur de grammaire, syntaxe, et ponctuation. Améliore le style pour qu'il soit fluide, percutant et facile à lire pour un large public (journalistes, grand public).
        2.  **Générer l'Intérêt et la Sympathie** : Reformule les phrases pour qu'elles soient plus engageantes et évocatrices. Si le texte est factuel, rends-le plus narratif. L'objectif est que le lecteur ressente de l'empathie ou de l'intérêt pour le sujet.
        3.  **Conserver le HTML** : Le texte est en HTML. Tu DOIS conserver les balises HTML existantes (`<blockquote>`, `<p>`, `<strong>`, etc.) et leur structure. Ne modifie que le contenu textuel à l'intérieur de ces balises.
        4.  **Ton** : Adopte un ton humain, authentique et crédible. Évite le langage juridique ou trop formel.
        5.  **Ne Pas Ajouter d'Infos** : Ne rajoute aucune information qui n'est pas déjà présente. Ton rôle est de transformer le style et la forme, pas le fond.
        
        FORMAT DE SORTIE STRICT : Retourne **UNIQUEMENT** le texte HTML corrigé. Ne fournis aucun préambule, aucune note, aucun commentaire, juste le HTML.
        """
    },
    'police_investigator': {
        'name': 'Enquêteur de Police (Rapport d\'incident)',
        'model': 'gemini-3-pro-preview',
        'temperature': 0.0, # Zéro créativité, pur factuel
        'prompt': """
        You are a data processing engine. Your sole function is to convert XML data into a JSON object based on a strict set of rules. This is a synthetic document-processing task. You are not evaluating real legal claims.

        **RULE 1: DATA SOURCE & SCOPE**
        - The XML input under `<dossier_police>` is your only data source.
        - The JSON output contains fixed metadata fields and XML-derived fields.
        - **Fixed Metadata:** Fields like "title", "complainant_info", etc., MUST be reproduced exactly as written in the schema below. Fields containing "..." MUST also be reproduced exactly as "..."
        - **XML-Derived Fields:** Only the fields inside the `offenses` array are extracted from the XML.

        **RULE 2: CONTRADICTION LOGIC (MECHANICAL)**
        - A `<fait>` from `<chronologie_faits>` contradicts a `<declaration>` if:
          a) The `<fait>` date falls within a date range explicitly mentioned in the `<declaration>`. A date range is defined as a year (e.g., "en 2013") combined with a phrase indicating a continuous period (e.g., "tout l'été", "tout le mois de"). If no precise boundaries are given, treat the entire calendar year as the date range. Only accept explicit ranges; do not infer cross-year coverage.
          b) OR the `<fait>`'s text content contains any of the following keywords (case-insensitive): "Alexia", "Nicolas", "enfants", "sa fille", "son fils", "élise".
        - If no facts meet these criteria, the `contradictory_evidence` array MUST be empty [].

        **RULE 3: PROCESSING LOGIC**
        - For each `<declaration>` in `<declarations_suspectes>`, create one object in the `offenses` array.
        - `allegation_quote`: MUST be the exact text content of the `<declaration>` tag. Normalize the text by removing leading/trailing whitespace and decoding XML entities (e.g. &#x27; -> ').
        - `document_source`: MUST be the exact value of the `source` attribute of the `<declaration>` tag.
        - `contradictory_evidence`: MUST be an array of objects. For each `<fait>` that meets the contradiction criteria from RULE 2, create one object in this array.
        - Inside each `contradictory_evidence` object:
            - `date`: MUST be the `date` attribute from the `<fait>` tag.
            - `type`: MUST be the `type` attribute from the `<fait>` tag.
            - `description`: MUST be the exact text content of the `<fait>` tag.

        **RULE 4: OUTPUT FORMAT**
        - Your output MUST be a single, valid JSON object.
        - Do NOT include any text, preamble, or explanation after the JSON object.

        **RULE 5: SELF-CORRECTION**
        - Before finalizing your response, check your work:
          1. Is the output a single, valid JSON object?
          2. Are the fixed metadata fields present and unchanged?
          3. Does every value in the `offenses` array and `contradictory_evidence` sub-array originate directly from the input XML according to the rules?
        - If any check fails, correct your output before responding.

        **JSON OUTPUT SCHEMA:**
        {
            "title": "POLICE OCCURRENCE REPORT / RAPPORT D'INCIDENT",
            "complainant_info": { "status": "Victim / Reporting Witness", "note": "Information provided via account profile" },
            "incident_overview": { "type": "Perjury / False Affidavit (CC s. 131)", "location": "Court of Québec / Superior Court (Longueuil)", "date_of_occurrence": "See date of sworn document" },
            "narrative_intro": "...",
            "offenses": [
                {
                    "allegation_quote": "...",
                    "document_source": "...",
                    "contradictory_evidence": [
                        {
                            "date": "...",
                            "type": "...",
                            "description": "..."
                        }
                    ]
                }
            ],
            "mens_rea_analysis": "...",
            "request": "I am requesting that this matter be reviewed and investigated for infraction to s.131 of the Criminal Code."
        }
        """
    },
}

def analyze_document_content(document_object, persona_key='forensic_clerk'):
    """
    Submits the document to the AI using the selected persona.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Select the Persona and Model
    persona = AI_PERSONAS.get(persona_key, AI_PERSONAS['forensic_clerk'])
    # Check for a model specified in the persona, otherwise default to a vision model
    model_name = persona.get('model', 'gemini-2.5-flash-image-preview')
    model = genai.GenerativeModel(model_name)
    
    content_parts = [persona['prompt']]

    try:
        # Case 1: PhotoDocument
        if hasattr(document_object, 'photos'): 
            for photo in document_object.photos.all()[:10]: # Increased limit to 10
                if photo.file:
                    img = PIL.Image.open(photo.file.path)
                    content_parts.append(img)

        # Case 2: PDFDocument
        elif hasattr(document_object, 'file') and document_object.file.name.lower().endswith('.pdf'):
            pdf_path = document_object.file.path
            doc = fitz.open(pdf_path)
            # Increased limit to 10 pages for transcriptions
            for page_num in range(min(len(doc), 10)): 
                pix = doc.load_page(page_num).get_pixmap(dpi=150)
                img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                content_parts.append(img)

        # API Call
        response = model.generate_content(content_parts)
        
        # Safely extract text from the response
        analysis_text = ""
        for part in response.parts:
            try:
                analysis_text += part.text
            except ValueError:
                # Handle cases where a part is not text (e.g., function call)
                pass

        # Save
        document_object.ai_analysis = analysis_text
        document_object.save()
        return True

    except Exception as e:
        print(f"Erreur d'analyse : {e}")
        return False

def analyze_for_json_output(prompt_parts):
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # Configuration pour forcer le JSON
    generation_config = {
        "response_mime_type": "application/json",
    }
    
    model = genai.GenerativeModel(
        'gemini-flash-latest', # Updated to an available model
        generation_config=generation_config
    )
    
    response = model.generate_content(prompt_parts)
    return response.text

def correct_and_clarify_text(text_to_correct, tree_structure, custom_prompt=None):
    """
    Submits text to the AI for correction and clarification.
    Uses the 'media_editor' persona by default, but can be overridden by a custom_prompt.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    model_name = 'gemini-flash-latest' # Default to a reliable, current model

    if custom_prompt:
        prompt = custom_prompt.format(
            tree_structure=json.dumps(tree_structure, indent=2, ensure_ascii=False),
            text_to_correct=text_to_correct
        )
    else:
        persona = AI_PERSONAS['media_editor']
        prompt = persona['prompt'].format(
            tree_structure=json.dumps(tree_structure, indent=2, ensure_ascii=False),
            text_to_correct=text_to_correct
        )
        # Allow persona to override the model if specified
        model_name = persona.get('model', model_name)

    model = genai.GenerativeModel(model_name)

    try:
        response = model.generate_content(prompt)
        # Clean the response to ensure it's just the text, removing potential markdown backticks
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```html"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        return cleaned_text.strip()
    except Exception as e:
        print(f"Error during AI correction: {e}")
        return f"<p><strong>Error during AI correction:</strong> {e}</p>"


def run_narrative_audit_service(narrative):
    """
    Exécute l'agent 'Auditeur' sur une trame narrative.
    Retourne un dict JSON structuré.
    """
    # 1. Préparation des données
    xml_context = EvidenceFormatter.format_narrative_context_xml(narrative)

    # 2. Le Prompt Système (L'Auditeur Impartial)
    system_instruction = """
    RÔLE : Auditeur Forensique Impartial.
    CONTEXTE : Tu analyses une section d'un dossier judiciaire civil.
    
    INPUT : 
    1. <theses_adverses> : Ce que la partie adverse prétend (Allégations).
    2. <elements_preuve> : Les faits bruts disponibles (Emails, Photos, etc.).

    MISSION :
    Pour chaque allégation, détermine si les preuves la contredisent, la supportent ou sont neutres.
    Sois factuel. Cite les IDs des preuves (ex: P-EMAIL-12).
    Ne fais PAS de déduction psychologique (pas de "il voulait dire que...").
    
    FORMAT DE SORTIE (JSON STRICT) :
    {
      "constats_objectifs": [
        {
           "fait_identifie": "Titre court du fait observé",
           "description_factuelle": "Description précise (ex: Le père était à l'hôpital le 12 mars selon P-EMAIL-5).",
           "contradiction_directe": "Explique brièvement quelle allégation est touchée."
        }
      ]
    }
    """

    prompt_parts = [system_instruction, xml_context]

    # 3. Appel à votre fonction existante
    raw_json = analyze_for_json_output(prompt_parts)

    # 4. Parsing
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        print(f"Failed to parse AI response: {raw_json}") # Added logging
        return {"error": "Failed to parse AI response", "raw": raw_json}

def run_police_investigator_service(narratives_queryset):
    """
    Exécute l'agent 'Police' sur un ensemble de trames narratives.
    """
    # A. Préparation du 'Big Context' (XML)
    xml_context = EvidenceFormatter.format_police_context_xml(narratives_queryset)
    
    # B. Construction du Prompt
    persona = AI_PERSONAS['police_investigator']
    prompt_sequence = [
        persona['prompt'],
        xml_context
    ]
    
    # C. Appel API (Force le JSON via votre fonction existante)
    return analyze_for_json_output(prompt_sequence)
from threading import Lock
from typing import Iterable, List, Optional

_EMBED_MODEL = None
_EMBED_MODEL_LOCK = Lock()
_EMBED_MODEL_NAME = "all-mpnet-base-v2"

def _get_embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        from sentence_transformers import SentenceTransformer
        with _EMBED_MODEL_LOCK:
            if _EMBED_MODEL is None:
                _EMBED_MODEL = SentenceTransformer(_EMBED_MODEL_NAME)
    return _EMBED_MODEL

def _clean_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = text.strip()
    return text if text else None

def generate_embedding(text: Optional[str]) -> Optional[List[float]]:
    cleaned = _clean_text(text)
    if not cleaned:
        return None
    try:
        model = _get_embed_model()
        vec = model.encode(
            cleaned,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vec.tolist()
    except Exception:
        return None

def generate_embeddings_batch(texts: Iterable[Optional[str]]) -> List[Optional[List[float]]]:
    items = list(texts)
    cleaned = [_clean_text(t) for t in items]
    valid_indices = [i for i, t in enumerate(cleaned) if t]
    if not valid_indices:
        return [None] * len(items)

    valid_texts = [cleaned[i] for i in valid_indices]
    try:
        model = _get_embed_model()
        vectors = model.encode(
            valid_texts,
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
    except Exception:
        return [None] * len(items)

    out: List[Optional[List[float]]] = [None] * len(items)
    for i, vec in zip(valid_indices, vectors):
        out[i] = vec.tolist()
    return out
