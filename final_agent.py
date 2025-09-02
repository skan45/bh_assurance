from datetime import datetime, timezone
import numpy as np
from qdrant_client import QdrantClient
import httpx
from fastembed import TextEmbedding
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
import re 
import requests
import os 
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

load_dotenv()

# Configuration for FAISS (Part 1: Product Comprehension)
FAISS_INDEX_FILE = "process_PDF/embeddings.index"
METADATA_FILE = "process_PDF/metadata.json"


QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "pdf_embeddings")

# Ollama configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

# Configuration for Neo4j Agent (Part 2: Client Data Analysis)
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "")

# Persistent conversation memory for FAISS (Product) Agent
conversation_history = []
CONVERSATION_FILE = "conversation_history.json"

async def summarize_text(text: str) -> str:
    """
    Summarizes a user query into a short 3-5 word phrase to be used as chat name.
    Uses Ollama's local LLaMA 2 7B model.
    """
    prompt = f"Summarize this user query into 3-5 words suitable for a chat name:\n\n{text}"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            response = await client.post(
                f"{OLLAMA_URL}/v1/completions",
                json={
                    "model": "llama2:7b",  # Ollama model
                    "prompt": prompt,
                    "stream": False       # Important: get full response in one go
                }
            )

        if response.status_code != 200:
            print(f"Ollama returned status {response.status_code}: {response.text}")
            return "New Chat"

        data = response.json()
        summary = data.get("response", "").strip()

        # Fallback if the model gives an empty response
        if not summary:
            summary = "New Chat"

        return summary
    except httpx.TimeoutException:
        print("Timeout when calling Ollama for summarization")
        return "New Chat"
    except Exception as e:
        print(f"Error calling Ollama for summarization: {e}")
        return "New Chat"
def save_conversation_to_file():
    try:
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {e}")

# Initialize embedding model
def initialize_embedding_model():
    return TextEmbedding()

# Clean retrieved content
def clean_content(raw_text: str) -> str:
    text = raw_text
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r" +", " ", text)
    return text.strip()

async def ask_bh_assurance(query: str, embedding_model):
    """
    Ask BH Assurance questions using Qdrant for context and Ollama (LLaMA 2 7B) for response.
    """
    # Connect to Qdrant
    

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Generate query embedding
    query_embedding = list(embedding_model.embed([query]))[0]

    # Perform similarity search
    try:
        hits = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=5
        )
    except Exception as e:
        return f"Error querying Qdrant: {str(e)}"

    # Build context from top hits
    context = ""
    for hit in hits:
        payload = hit.payload
        content = payload.get("content", "")
        cleaned_content = clean_content(content)
        context += cleaned_content + "\n\n"

    # Build conversation history for prompt
    history_text = ""
    if conversation_history:
        history_text = "Previous conversation:\n"
        for i, (q, r) in enumerate(conversation_history):
            history_text += f"Q{i+1}: {q}\nA{i+1}: {r}\n"

    prompt = f"""
You are a friendly, helpful, and knowledgeable assistant for BH Assurance, a leading insurance provider in Tunisia. Answer user questions about BH Assurance auto insurance contracts in a conversational, chat-like style—just like ChatGPT-4. Be clear, supportive, and approachable. Use specific details from BH Assurance documentation naturally, but don't reference the source. If you don't know something, give a general but helpful answer and suggest contacting BH Assurance for more info.

Do not include any greeting—start answering the user's question directly.

{history_text}
User: {query}

Context from BH Assurance documentation:
{context}

Respond in a chat format, making sure your answer is friendly, direct, and easy to understand.
"""

    # Call Ollama API instead of OpenAI
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=30.0)) as client:
            response = await client.post(
                f"{OLLAMA_URL}/v1/completions",
                json={
                    "model": "llama2:7b",
                    "prompt": prompt,
                    "stream": False,       # Get full response at once
                }
            )

        if response.status_code != 200:
            return f"Error generating response from Ollama: {response.text}"

        answer = response.json().get("response", "").strip()
        if not answer:
            answer = "Sorry, I couldn't generate an answer. Please contact BH Assurance for help."

    except httpx.TimeoutException:
        return "Sorry, the request timed out. Please try again or contact BH Assurance for help."
    except Exception as e:
        return f"Error generating response from Ollama: {str(e)}"

    # Save conversation
    conversation_history.append((query, answer))
    save_conversation_to_file()

    return answer

# Neo4j Agent Class (Part 2: Client Data Analysis)
class Neo4jAgent:
    def __init__(self, memory_enabled: bool = False, memory_path: str | None = None, memory_max: int = 100):
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASSWORD
        self.database = NEO4J_DATABASE
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
        except Exception as e:
            raise SystemExit(
                f"Connection failed to {self.uri} as {self.user}: {e}\n"
                "Tips: 1) Ensure Neo4j Desktop is running and the database is active. "
                "2) Verify the URI matches your Neo4j settings. "
                "3) Check username and password."
            )

        # Memory settings
        self.memory_enabled = memory_enabled
        self.memory_path = memory_path or os.path.join(os.getcwd(), "agent_memory.json")
        self.memory_max = memory_max
        self._memory_cache: list[dict] = []
        self._conversation: dict[str, Any] = {
            'person_matricule': None,
            'sinistres': []
        }
        if self.memory_enabled:
            self._load_memory()

    def close(self):
        self.driver.close()
        if self.memory_enabled:
            self._save_memory()

    # ---------------- Memory management -----------------
    def _load_memory(self):
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._memory_cache = data[-self.memory_max:]
        except Exception:
            self._memory_cache = []

    def _save_memory(self):
        try:
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self._memory_cache[-self.memory_max:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _add_memory(self, nl_query: str, cypher: str, result_sample: list[dict]):
        if not self.memory_enabled:
            return
        ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        entry = {
            "timestamp": ts,
            "query": nl_query,
            "cypher": cypher,
            "result_keys": list(result_sample[0].keys()) if result_sample else [],
            "result_count": len(result_sample),
        }
        self._memory_cache.append(entry)
        if len(self._memory_cache) > self.memory_max:
            self._memory_cache = self._memory_cache[-self.memory_max:]

    def _relevant_memory(self, nl_query: str, k: int = 3) -> list[dict]:
        if not self.memory_enabled or not self._memory_cache:
            return []
        tokens = {t for t in re.findall(r"[a-zA-Zéèêàùûôï0-9_]+", nl_query.lower()) if len(t) > 3}
        scored = []
        for e in self._memory_cache:
            etoks = {t for t in re.findall(r"[a-zA-Zéèêàùûôï0-9_]+", e['query'].lower()) if len(t) > 3}
            overlap = len(tokens & etoks)
            if overlap > 0:
                scored.append((overlap, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:k]]

    # ---------------- Cypher generation -----------------
    async def _generate_cypher_query(self, natural_language_query: str) -> str:
        kg_schema = """Knowledge Graph Schema: PersonneMorale - ref_personne: Unique identifier for the moral person (integer). - raison_sociale: Company name (string). - matricule_fiscale: Fiscal ID (string). - lib_secteur_activite: Sector of activity (string). - lib_activite: Activity (string). - ville: City (string). - lib_gouvernorat: Governorate (string). - ville_gouvernorat: Governorate city (string). PersonnePhysique - ref_personne: Unique identifier for the physical person (integer). - nom_prenom: Full name (string). - date_naissance: Date of birth (date string YYYY-MM-DD). - lieu_naissance: Place of birth (string). - code_sexe: Gender code (string). - situation_familiale: Marital status (string). - num_piece_identite: ID number (integer). - lib_secteur_activite: Sector of activity (string). - lib_profession: Profession (string). - ville: City (string). - lib_gouvernorat: Governorate (string). - ville_gouvernorat: Governorate city (string). Contrat - num_contrat: Contract number (integer). - lib_produit: Product name (string). - effet_contrat: Contract effective date (date string YYYY-MM-DD). - date_expiration: Contract expiration date (date string YYYY-MM-DD). - prochain_terme: Next term (string). - lib_etat_contrat: Contract status (string). - branche: Branch (string). - somme_quittances: Sum of receipts (float, TND). - statut_paiement: Payment status (string). - capital_assure: Insured capital (float, TND). Sinistre - num_sinistre: Claim number (integer). - lib_branche: Branch (string). - lib_sous_branche: Sub-branch (string). - lib_produit: Product name (string). - nature_sinistre: Nature of claim (string). - lib_type_sinistre: Type of claim (string). - taux_responsabilite: Responsibility rate (float). - date_survenance: Date of occurrence (date string YYYY-MM-DD). - date_declaration: Date of declaration (date string YYYY-MM-DD). - date_ouverture: Date of opening (date string YYYY-MM-DD). - observation_sinistre: Claim observation (string). - lib_etat_sinistre: Claim status (string). - lieu_accident: Accident location (string). - motif_reouverture: Reopening reason (string). - montant_encaisse: Amount collected (float). - montant_a_encaisser: Amount to be collected (float). Branche - lib_branche: Branch name (string). SousBranche - lib_sous_branche: Sub-branch name (string). Produit - lib_produit: Product name (string). Garantie - code_garantie: Unique code for the guarantee (integer). - lib_garantie: Guarantee name (string). - description: Description of the guarantee (string). ProfilCible - lib_profil: Target profile description (string, e.g., "Emprunteurs" or "chefs de famille"). Relationships: - [:A_SOUSCRIT], [:CONCERNE], [:EST_UNE_SOUS_BRANCHE_DE], [:EST_UN_PRODUIT_DE], [:PORTE_SUR], [:DE_BRANCHE], [:DE_SOUS_BRANCHE], [:OFFRE], [:INCLUT], [:DESTINE_A] """ # Memory context memory_context = "" if self.memory_enabled: rel_mem = self._relevant_memory(natural_language_query, k=3) if rel_mem: mem_lines = [] for m in rel_mem: mem_lines.append(f"- Q: {m['query']} => Cypher: {m['cypher'][:220]}... (résultats: {m['result_count']})") memory_context = "Historique pertinent récent:\n" + "\n".join(mem_lines) + "\n\n" # Conversation context conversation_context = "" if self._conversation.get('person_matricule'): conversation_context += f"L'utilisateur s'est précédemment identifié comme client avec matricule_fiscale = {self._conversation['person_matricule']}.\n" if self._conversation.get('sinistres'): nums = ', '.join(str(n) for n in self._conversation['sinistres'][:15]) conversation_context += f"Les derniers sinistres référencés dans la conversation ont les num_sinistre: {nums}.\n" if conversation_context: conversation_context = "Contexte conversationnel:\n" + conversation_context + "\n" # Prompt for Ollama prompt = f"""Given the following Knowledge Graph schema, translate the natural language query into a Cypher query. {kg_schema} {conversation_context}{memory_context} Natural Language Query: {natural_language_query} Return only the Cypher query. Do not include extra text or explanations."""  # Keep your full KG schema here

        memory_context = ""
        if self.memory_enabled:
            rel_mem = self._relevant_memory(natural_language_query, k=3)
            if rel_mem:
                mem_lines = []
                for m in rel_mem:
                    mem_lines.append(f"- Q: {m['query']} => Cypher: {m['cypher'][:220]}... (résultats: {m['result_count']})")
                memory_context = "Historique pertinent récent:\n" + "\n".join(mem_lines) + "\n\n"

        conversation_context = ""
        if self._conversation.get('person_matricule'):
            conversation_context += f"L'utilisateur s'est précédemment identifié comme client avec matricule_fiscale = {self._conversation['person_matricule']}.\n"
        if self._conversation.get('sinistres'):
            nums = ', '.join(str(n) for n in self._conversation['sinistres'][:15])
            conversation_context += f"Les derniers sinistres référencés dans la conversation ont les num_sinistre: {nums}.\n"
        if conversation_context:
            conversation_context = "Contexte conversationnel:\n" + conversation_context + "\n"

        prompt = f"""Given the following Knowledge Graph schema, translate the natural language query into a Cypher query.

{kg_schema}

{conversation_context}{memory_context}

Natural Language Query: {natural_language_query}

Return only the Cypher query. Do not include extra text or explanations.
"""

        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=30.0)) as client:
            try:
                response = await client.post(
                    f"{OLLAMA_URL}/v1/completions",
                    json={
                        "model": "llama2:7b",
                        "prompt": prompt,
                        "max_tokens": 500,
                        "temperature": 0,
                        "stream":False
                    }
                )
                data = response.json()
                cypher_query = data.get("response", "")
            except Exception as e:
                print(f"Ollama request failed: {e}")
                cypher_query = ""

        if cypher_query.startswith("```cypher") and cypher_query.endswith("```"):
            cypher_query = cypher_query[len("```cypher\n"): -len("```")].strip()

        return self._sanitize_cypher(cypher_query)

    # ---------------- Sanitize -----------------
    def _sanitize_cypher(self, query: str) -> str:
        query = query.strip().rstrip(';').strip()
        lines = query.split('\n')
        for i, l in enumerate(lines):
            if re.match(r'\s*RETURN\b', l, re.IGNORECASE):
                parts = [p.strip() for p in l.split('RETURN', 1)[1].split(',')]
                cleaned = [p for p in parts if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', p)]
                lines[i] = f"RETURN {', '.join(cleaned)}"
        query = '\n'.join(lines)
        if re.search(r'\bRETURN\b', query, re.IGNORECASE) and not re.search(r'\bLIMIT\b', query, re.IGNORECASE):
            query += "\nLIMIT 100"
        return query

    # ---------------- Refine query on error -----------------
    async def _refine_query_on_error(self, nl_query: str, bad_cypher: str, error_text: str) -> str:
        repair_prompt = f"""La requête Cypher a provoqué une erreur Neo4j.
Question: {nl_query}
Requête Cypher initiale:
{bad_cypher}
Message d'erreur:
{error_text}

Corrige la requête en respectant les règles:
- RETURN uniquement des variables.
- MATCH / OPTIONAL MATCH appropriés.
- EXISTS {{ MATCH ... }} pour tester l'existence.
- Aucun label ou propriété inventé.
- Ajoute LIMIT 100 si absent.
Renvoie seulement la requête Cypher corrigée.
"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=30.0)) as client:
            try:
                response = await client.post(
                    f"{OLLAMA_URL}/v1/completions",
                    json={
                        "model": "llama2:7b",
                        "prompt": repair_prompt,
                        "max_tokens": 400,
                        "temperature": 0,
                        "stream": False
                    }
                )
                data = response.json()
                fixed = data.get("response", "")
            except Exception as e:
                print(f"Ollama request failed: {e}")
                fixed = bad_cypher
        if fixed.startswith("```cypher") and fixed.endswith("```"):
            fixed = fixed[len("```cypher\n"): -len("```")].strip()
        return self._sanitize_cypher(fixed)

    # ---------------- Format results -----------------
    async def format_results(self, natural_language_query: str, results: List[Dict[str, Any]]) -> str:
        if not results:
            neg_prompt = f"""La requête utilisateur n'a retourné aucun résultat dans Neo4j.
Question: {natural_language_query}
Réponds en français, commence par "Non", explique brièvement et suggère une reformulation possible.
"""
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=30.0)) as client:
                try:
                    response = await client.post(
                        f"{OLLAMA_URL}/v1/completions",
                        json={
                            "model": "llama2:7b",
                            "prompt": neg_prompt,
                            "max_tokens": 120,
                            "temperature": 0,
                            "stream": False
                        }
                    )
                    data = response.json()
                    txt = data.get("response", "")
                    if not txt.lower().startswith("non"):
                        txt = "Non, aucun résultat correspondant n'a été trouvé." if not txt else f"Non. {txt}"
                    return txt
                except Exception:
                    return "Non, aucun résultat correspondant n'a été trouvé."

        results_json = json.dumps(results, indent=2, ensure_ascii=False)
        prompt = f"""Formate les résultats suivants en réponse claire en français, adaptée à la question:
Question: {natural_language_query}
Résultats: {results_json}
Réponse formatée:"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=30.0)) as client:
            try:
                response = await client.post(
                    f"{OLLAMA_URL}/v1/completions",
                    json={
                        "model": "llama2:7b",
                        "prompt": prompt,
                        "max_tokens": 1000,
                        "temperature": 0,
                        "stream": False
                    }
                )
                data = response.json()
                formatted_response = data.get("response", "")
            except Exception:
                formatted_response = "Voici les résultats trouvés."
        formatted_response = re.sub(r"€\s*", " TND ", formatted_response)
        formatted_response = re.sub(r"\b(euros?|EUROS?)\b", "TND", formatted_response, flags=re.IGNORECASE)
        return formatted_response

    def execute_query(self, natural_language_query: str):
        cypher_query = self._generate_cypher_query(natural_language_query)
        print(f"Generated Cypher Query: {cypher_query}")
        attempts = 0
        last_error = None
        records = []
        while attempts < 3:
            try:
                with self.driver.session(database=self.database) as session:
                    result = session.run(cypher_query)
                    records = [record.data() for record in result]
                break
            except Exception as e:
                msg = str(e)
                last_error = msg
                if ('pattern expression' in msg.lower() or 'syntax error' in msg.lower() or 'not defined' in msg.lower()):
                    print("Attempting to auto-fix Cypher after error: ", msg)
                    cypher_query = self._refine_query_on_error(natural_language_query, cypher_query, msg)
                    print(f"Refined Cypher Query (attempt {attempts+2}): {cypher_query}")
                    attempts += 1
                    continue
                else:
                    raise
        if attempts == 3 and last_error:
            raise RuntimeError(f"Failed after retries. Last error: {last_error}")
        self._update_conversation_context(natural_language_query, records)
        formatted_result = self.format_results(natural_language_query, records)
        self._add_memory(natural_language_query, cypher_query, records[:1])
        return formatted_result

    def _update_conversation_context(self, nl_query: str, records: list[dict]):
        matricule_match = re.search(r"matricule\s+fiscale\s*(?:est|=|:)?\s*([A-Z0-9]+)", nl_query, flags=re.IGNORECASE)
        if matricule_match:
            new_mat = matricule_match.group(1).strip()
            if new_mat and new_mat != self._conversation.get('person_matricule'):
                self._conversation['person_matricule'] = new_mat
                self._conversation['sinistres'] = []
        sin_numbers = set(self._conversation.get('sinistres', []))
        for rec in records:
            for val in rec.values():
                try:
                    if isinstance(val, dict) and 'num_sinistre' in val:
                        sin_numbers.add(val['num_sinistre'])
                    else:
                        num = getattr(val, 'get', None)
                        if callable(num):
                            maybe = val.get('num_sinistre')
                            if maybe is not None:
                                sin_numbers.add(maybe)
                except Exception:
                    continue
            if 'num_sinistre' in rec:
                try:
                    sin_numbers.add(rec['num_sinistre'])
                except Exception:
                    pass
        if sin_numbers:
            self._conversation['sinistres'] = list(sorted(sin_numbers))[-50:]

# Classification function to determine query type
async def classify_query(query: str) -> str:
    prompt = f"""
Classify the following query into one of two categories:
- "product": If the query is about general understanding of insurance products, guarantees, differences between formulas, or general contract details without referencing specific clients, sinistres, or payments.
- "client": If the query is about specific client data, such as guarantees subscribed by a client, if a sinistre is covered, payment status, sinistre status, or coverage of a sinistre for a client.

Query: {query}

Return only the category name: "product" or "client".
"""

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
        try:
            resp = await client.post(
                f"{OLLAMA_URL}/v1/completions",
                json={"model": "llama2:7b", "prompt": prompt, "stream": False}
            )
            resp.raise_for_status()
            result = resp.json()
            # Ollama may return text in 'response' field
            category = result.get("response", "").strip().lower()
            if category not in ["product", "client"]:
                category = "product"
            return category
        except Exception as e:
            print("Error calling Ollama:", e)
            return "product"



