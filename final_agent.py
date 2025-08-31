import os
import re
import json
from datetime import datetime, timezone
import numpy as np
import faiss
from fastembed import TextEmbedding
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

load_dotenv()

# Configuration for FAISS (Part 1: Product Comprehension)
FAISS_INDEX_FILE = "process_PDF/embeddings.index"
METADATA_FILE = "process_PDF/metadata.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

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
    """
    prompt = f"Summarize this user query into 3-5 words suitable for a chat name:\n\n{text}"
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=20  # Keep it short
    )

    summary = response.choices[0].message.content.strip()

    # Optional: fallback if empty
    if not summary:
        summary = "New Chat"

    return summary

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

# Query FAISS and generate response with OpenAI, using conversation memory
def ask_bh_assurance(query: str, embedding_model: TextEmbedding, faiss_index_file: str = FAISS_INDEX_FILE, metadata_file: str = METADATA_FILE):
    # Generate query embedding
    query_embedding = list(embedding_model.embed([query]))[0]
    query_embedding = np.array([query_embedding], dtype=np.float32)
    faiss.normalize_L2(query_embedding)
    
    # Load FAISS index
    try:
        index = faiss.read_index(faiss_index_file)
    except Exception as e:
        print(f"Error loading FAISS index: {str(e)}")
        return "Error: Could not load FAISS index. Ensure embeddings.index exists."
    
    # Load metadata
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"Error loading metadata: {str(e)}")
        return "Error: Could not load metadata. Ensure metadata.json exists."
    
    # Perform similarity search
    limit = 5
    distances, indices = index.search(query_embedding, limit)
    context = ""
    for i, idx in enumerate(indices[0]):
        if idx < len(metadata):
            payload = metadata[idx]
            content = payload.get('content', '')
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

{history_text}
User: {query}

Context from BH Assurance documentation:
{context}

Respond in a chat format, making sure your answer is friendly, direct, and easy to understand.
"""
    # Initialize OpenAI client
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not set in environment (.env)."
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7
        )
        answer = response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"
    # Store the query and answer in memory
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
                "2) Verify the URI (neo4j://127.0.0.1:7687) matches your Neo4j Desktop settings. "
                "3) Check username (neo4j) and password (azerty2002) in Neo4j Desktop."
            )
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        # Memory settings
        self.memory_enabled = memory_enabled
        self.memory_path = memory_path or os.path.join(os.getcwd(), "agent_memory.json")
        self.memory_max = memory_max
        self._memory_cache: list[dict] = []
        # Conversational ephemeral context (not persisted): track identified user & last sinistres list
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

    def _generate_cypher_query(self, natural_language_query: str) -> str:
        kg_schema = """
        Knowledge Graph Schema:


    PersonneMorale
    - `ref_personne`: Unique identifier for the moral person (integer).
    - `raison_sociale`: Company name (string).
    - `matricule_fiscale`: Fiscal ID (string).
    - `lib_secteur_activite`: Sector of activity (string).
    - `lib_activite`: Activity (string).
    - `ville`: City (string).
    - `lib_gouvernorat`: Governorate (string).
    - `ville_gouvernorat`: Governorate city (string).

    PersonnePhysique
    - `ref_personne`: Unique identifier for the physical person (integer).
    - `nom_prenom`: Full name (string).
    - `date_naissance`: Date of birth (date string YYYY-MM-DD).
    - `lieu_naissance`: Place of birth (string).
    - `code_sexe`: Gender code (string).
    - `situation_familiale`: Marital status (string).
    - `num_piece_identite`: ID number (integer).
    - `lib_secteur_activite`: Sector of activity (string).
    - `lib_profession`: Profession (string).
    - `ville`: City (string).
    - `lib_gouvernorat`: Governorate (string).
    - `ville_gouvernorat`: Governorate city (string).

    Contrat
    - `num_contrat`: Contract number (integer).
    - `lib_produit`: Product name (string).
    - `effet_contrat`: Contract effective date (date string YYYY-MM-DD).
    - `date_expiration`: Contract expiration date (date string YYYY-MM-DD).
    - `prochain_terme`: Next term (string).
    - `lib_etat_contrat`: Contract status (string).
    - `branche`: Branch (string).
    - `somme_quittances`: Sum of receipts (float, TND).
    - `statut_paiement`: Payment status (string).
    - `capital_assure`: Insured capital (float, TND).

    Sinistre
    - `num_sinistre`: Claim number (integer).
    - `lib_branche`: Branch (string).
    - `lib_sous_branche`: Sub-branch (string).
    - `lib_produit`: Product name (string).
    - `nature_sinistre`: Nature of claim (string).
    - `lib_type_sinistre`: Type of claim (string).
    - `taux_responsabilite`: Responsibility rate (float).
    - `date_survenance`: Date of occurrence (date string YYYY-MM-DD).
    - `date_declaration`: Date of declaration (date string YYYY-MM-DD).
    - `date_ouverture`: Date of opening (date string YYYY-MM-DD).
    - `observation_sinistre`: Claim observation (string).
    - `lib_etat_sinistre`: Claim status (string).
    - `lieu_accident`: Accident location (string).
    - `motif_reouverture`: Reopening reason (string).
    - `montant_encaisse`: Amount collected (float).
    - `montant_a_encaisser`: Amount to be collected (float).

    Branche
    - `lib_branche`: Branch name (string).

    SousBranche
    - `lib_sous_branche`: Sub-branch name (string).

    Produit
    - `lib_produit`: Product name (string).

    Garantie
    - `code_garantie`: Unique code for the guarantee (integer).
    - `lib_garantie`: Guarantee name (string).
    - `description`: Description of the guarantee (string).

    ProfilCible
    - `lib_profil`: Target profile description (string, e.g., "Emprunteurs" or "chefs de famille").

    Relationships:

    - `[:A_SOUSCRIT]`: Connects `PersonneMorale` or `PersonnePhysique` nodes to `Contrat` nodes, indicating that a person has subscribed to a contract.
    - `[:CONCERNE]`: Connects `Sinistre` nodes to `Contrat` nodes, indicating that a claim concerns a specific contract.
    - `[:EST_UNE_SOUS_BRANCHE_DE]`: Connects `SousBranche` nodes to `Branche` nodes, indicating a hierarchical relationship where a sub-branch belongs to a branch.
    - `[:EST_UN_PRODUIT_DE]`: Connects `Produit` nodes to `SousBranche` nodes, indicating that a product belongs to a sub-branch.
    - `[:PORTE_SUR]`: Connects `Contrat` nodes to `Produit` nodes, indicating that a contract is for a specific product.
    - `[:DE_BRANCHE]`: Connects `Contrat` or `Sinistre` nodes to `Branche` nodes, indicating the branch of the contract or claim.
    - `[:DE_SOUS_BRANCHE]`: Connects `Sinistre` nodes to `SousBranche` nodes, indicating the sub-branch of the claim.
    - `[:OFFRE]`: Connects `Produit` nodes to `Garantie` nodes, indicating that a product offers a specific guarantee.
    - `[:INCLUT]`: Connects `Contrat` nodes to `Garantie` nodes, indicating that a contract includes a specific guarantee. Properties: `capital_assure` (float, TND) - The insured capital amount for this guarantee in the contract.
    - `[:DESTINE_A]`: Connects `Produit` nodes to `ProfilCible` nodes, indicating the target profiles for a product (a product can connect to multiple profiles based on semi-colon separated values in the data).
    """


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

{conversation_context}Si la question utilisateur fait référence à un client, TOUJOURS utiliser le motif multi-label (p:PersonneMorale|PersonnePhysique) pour le client, et filtrer sur la propriété appropriée :
- Si la question ou le contexte contient "matricule fiscale", filtrer sur p.matricule_fiscale.
- Sinon, filtrer sur p.ref_personne.
N'utilise jamais uniquement PersonneMorale ou PersonnePhysique seul.
Si la question contient des pronoms ou références comme "mes sinistres", "leur numéro", "ceux-ci" ou "les précédents", utilise le contexte conversationnel ci-dessus pour résoudre à quelles entités (personne ou sinistres) cela fait référence. Si le contexte n'existe pas, ne devine pas : reformule la requête pour chercher explicitement. N'invente jamais de numéros.

Natural Language Query: {natural_language_query}

Cypher Query:

    Règles importantes de génération (NE PAS VIOLER):
1. Toujours utiliser MATCH (ou OPTIONAL MATCH) pour chaque motif avant de le RETURN; NE JAMAIS retourner directement un motif comme (c)-[:REL]->(g).
2. Dans RETURN, ne mettre que des variables (ex: c, g, r.capital_assure) pas des motifs entiers.
3. Pour tester l'existence d'un motif, utiliser EXISTS {{ MATCH ... }} ou une clause MATCH séparée + WHERE, jamais RETURN (a)-[:R]->(b).
4. Utiliser DISTINCT quand la question parle de "quels / quelles" ensembles uniques.
5. Préfixer les agrégations (COUNT, SUM) uniquement si demandé.
6. Limiter le nombre de lignes avec LIMIT 100 si aucune limite implicite.
7. Toujours respecter les labels existants du schéma.
8. Ne pas inventer de propriétés.
9. Les mots "client", "assuré", "souscripteur" désignent indistinctement une personne morale OU physique : modéliser avec un motif multi-label (p:PersonneMorale|PersonnePhysique). Conserver les propriétés (ex: ref_personne, matricule_fiscale) dans le même map.
10. Si le rôle (client / assuré) n'est pas précisé mais on cherche des contrats, utiliser (p:PersonneMorale|PersonnePhysique)-[:A_SOUSCRIT]->(c:Contrat).
11. Ne retourne jamais directement le nom d'un type de relation (ex: INCLUT, CONCERNE) sans alias; si besoin d'une relation, aliaser (p)-[r:INCLUT]->(g) et RETURN r, pas INCLUT.
"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates natural language to Cypher queries based on the provided schema. Only return the Cypher query, no additional text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        cypher_query = response.choices[0].message.content.strip()
        if cypher_query.startswith("```cypher") and cypher_query.endswith("```"):
            cypher_query = cypher_query[len("```cypher\n"): -len("```")].strip()
        return self._sanitize_cypher(cypher_query)

    def _sanitize_cypher(self, query: str) -> str:
        query = query.strip().rstrip(';').strip()
        declared_vars = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:', query))
        declared_vars.update(re.findall(r'\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', query))

        def _fix_return(line: str) -> str:
            parts = [p.strip() for p in line.split(',')]
            cleaned = []
            for p in parts:
                if '-[' in p or ')-' in p:
                    vars_found = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', p)
                    keywords = {'MATCH','WITH','WHERE','RETURN','DISTINCT','OPTIONAL','CALL','ORDER','BY','LIMIT','SKIP','AS','AND','OR','NOT','EXISTS'}
                    vars_kept = [v for v in vars_found if v.upper() not in keywords]
                    if vars_kept:
                        cleaned.extend(vars_kept)
                else:
                    cleaned.append(p)
            seen = set(); dedup = []
            for c in cleaned:
                if c.isupper() and c not in declared_vars:
                    continue
                if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', c) and c not in declared_vars:
                    continue
                if c not in seen:
                    seen.add(c); dedup.append(c)
            return ', '.join(dedup) if dedup else line
        lines = query.split('\n')
        for i, l in enumerate(lines):
            if re.match(r'\s*RETURN\b', l, re.IGNORECASE):
                prefix, rest = l.split('RETURN', 1)
                fixed = _fix_return(rest)
                lines[i] = f"{prefix}RETURN {fixed}".rstrip()
        query = '\n'.join(lines)
        if re.search(r'\bRETURN\b', query, re.IGNORECASE) and not re.search(r'\bLIMIT\b', query, re.IGNORECASE):
            query += "\nLIMIT 100"
        return query

    def _refine_query_on_error(self, nl_query: str, bad_cypher: str, error_text: str) -> str:
        repair_prompt = f"""La requête Cypher générée a provoqué une erreur Neo4j.
Question naturelle: {nl_query}
Requête Cypher initiale:
{bad_cypher}
Message d'erreur:
{error_text}

Produis une version corrigée qui respecte les règles:
- Ne retourne que des variables dans RETURN.
- Utilise MATCH / OPTIONAL MATCH appropriés.
- Utilise EXISTS {{ MATCH ... }} si tu testes la simple existence.
- N'invente aucun label ou propriété hors schéma.
- Ajoute LIMIT 100 si pas de limite.
Seulement la requête Cypher, rien d'autre."""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu répares des requêtes Cypher invalides. Tu renvoies uniquement la requête corrigée."},
                {"role": "user", "content": repair_prompt}
            ],
            max_tokens=400
        )
        fixed = response.choices[0].message.content.strip()
        if fixed.startswith("```cypher") and fixed.endswith("```"):
            fixed = fixed[len("```cypher\n"): -len("```")].strip()
        return self._sanitize_cypher(fixed)

    def format_results(self, natural_language_query: str, results: List[Dict[str, Any]]) -> str:
        if not results:
            neg_prompt = (
                "La requête utilisateur suivante n'a retourné aucun résultat dans la base Neo4j.\n"
                f"Requête utilisateur: {natural_language_query}\n\n"
                "Consignes:\n"
                "1. Réponds en français.\n"
                "2. La réponse doit commencer par \"Non\".\n"
                "3. Reformule brièvement la question pour contextualiser.\n"
                "4. Indique que les données correspondantes ne sont pas trouvées / n'existent pas.\n"
                "5. Suggère (facultatif) une piste de reformulation en une phrase.\n"
                "6. Ne pas inventer de chiffres ou d'objets inexistants.\n\n"
                "Réponse:" 
            )
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Tu rédiges des réponses négatives concises et utiles en français. Commence toujours par 'Non'."},
                        {"role": "user", "content": neg_prompt}
                    ],
                    max_tokens=120
                )
                txt = response.choices[0].message.content.strip()
                if not txt.lower().startswith("non"):
                    txt = "Non, aucun résultat correspondant n'a été trouvé." if not txt else f"Non. {txt}"
                return txt
            except Exception:
                return "Non, aucun résultat correspondant n'a été trouvé."

        results_json = json.dumps(results, indent=2, ensure_ascii=False)
        prompt = (
            "You are a helpful assistant that formats query results into a clear, concise, and natural language "
            "response in French, tailored to the original question. Use the provided query and results to generate "
            "a well-written phrase or paragraph that directly answers the question. Avoid technical jargon and focus "
            "on a user-friendly response. If the results are empty, indicate that no data was found.\n\n"
            f"Original Query: {natural_language_query}\n"
            f"Query Results: {results_json}\n\n"
            "Formatted Response (in French):"
        )
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates clear and concise responses in French based on query results."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        formatted_response = response.choices[0].message.content.strip()
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
def classify_query(query: str) -> str:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
Classify the following query into one of two categories:
- "product": If the query is about general understanding of insurance products, guarantees, differences between formulas, or general contract details without referencing specific clients, sinistres, or payments.
- "client": If the query is about specific client data, such as guarantees subscribed by a client, if a sinistre is covered, payment status, sinistre status, or coverage of a sinistre for a client.

Query: {query}

Return only the category name: "product" or "client".
"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.0
        )
        category = response.choices[0].message.content.strip().lower()
        if category not in ["product", "client"]:
            category = "product"
        return category
    except Exception:
        return "product"

# Function to handle devis request with API call and PDF generation
def handle_devis_request():
    print("Super ! Pour générer un devis d'assurance auto, j'ai besoin de quelques informations. Veuillez fournir les éléments suivants :")
    params = {}
    required_params = [
        "n_cin (Numéro CIN)",
        "valeur_venale (Valeur vénale du véhicule en TND)",
        "nature_contrat (Nature du contrat : r pour régulier)",
        "nombre_place (Nombre de places)",
        "valeur_a_neuf (Valeur à neuf du véhicule en TND)",
        "date_premiere_mise_en_circulation (Date de première mise en circulation, AAAA-MM-JJ)",
        "capital_bris_de_glace (Capital bris de glace en TND)",
        "capital_dommage_collision (Capital dommage collision en TND)",
        "puissance (Puissance du moteur en CV)",
        "classe (Classe du véhicule)"
    ]

    for param in required_params:
        key, prompt = param.split(" (", 1)
        key = key.strip()
        while True:
            value = input(f"Veuillez saisir {prompt[:-1]} : ")
            if key in ["n_cin", "nombre_place", "puissance", "classe"]:
                if value.isdigit():
                    params[key] = value
                    break
                else:
                    print("Veuillez entrer un nombre valide.")
            elif key in ["valeur_venale", "valeur_a_neuf", "capital_bris_de_glace", "capital_dommage_collision"]:
                try:
                    float_value = float(value)
                    if float_value >= 0:
                        params[key] = value
                        break
                    else:
                        print("Veuillez entrer une valeur positive.")
                except ValueError:
                    print("Veuillez entrer un nombre valide.")
            elif key == "date_premiere_mise_en_circulation":
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                    params[key] = value
                    break
                except ValueError:
                    print("Veuillez entrer une date valide au format AAAA-MM-JJ.")
            elif key == "nature_contrat":
                if value.lower() in ["r", "regulier"]:
                    params[key] = "r"
                    break
                else:
                    print("Veuillez entrer 'r' pour un contrat régulier.")

    # Préparer les styles avant d'utiliser story
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontSize=16, leading=20, alignment=1, spaceAfter=12)
    section_style = ParagraphStyle(name='SectionStyle', fontSize=12, leading=14, spaceAfter=8)
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    table_header_style = ParagraphStyle(name='TableHeader', fontSize=10, leading=12, alignment=0, fontName='Helvetica-Bold')

    story = []
    story.append(Paragraph("Devis d'Assurance Automobile", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>Paramètres du devis saisis :</b>", section_style))
    params_table_data = [["Champ", "Valeur"]]
    for k, v in params.items():
        params_table_data.append([k, v])
    params_table = Table(params_table_data)
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 0.5*cm))

    # Send API request
    url = "https://apidevis.onrender.com/api/auto/packs"
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        devis_data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error fetching devis data from API: {str(e)}"

    # Generate PDF
    doc = SimpleDocTemplate("devis.pdf", pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(name='TitleStyle', fontSize=16, leading=20, alignment=1, spaceAfter=12)
    section_style = ParagraphStyle(name='SectionStyle', fontSize=12, leading=14, spaceAfter=8)
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    table_header_style = ParagraphStyle(name='TableHeader', fontSize=10, leading=12, alignment=0, fontName='Helvetica-Bold')
    
    story = []
    story = []
    story.append(Paragraph("Devis d'Assurance Automobile", title_style))
    story.append(Spacer(1, 0.5*cm))
    # Ajout des paramètres utilisateur juste après le titre
    story.append(Paragraph("<b>Paramètres du devis saisis :</b>", section_style))
    params_table_data = [["Champ", "Valeur"]]
    for k, v in params.items():
        params_table_data.append([k, v])
    params_table = Table(params_table_data)
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 0.5*cm))

    # Ajout du fournisseur et des packs
    header = devis_data.get('header', {})
    provider_info = f"<b>Fournisseur :</b> {header.get('providerDescription', 'N/A')} (Code: {header.get('providerCode', 'N/A')})"
    story.append(Paragraph(provider_info, section_style))
    story.append(Spacer(1, 0.5*cm))

    for pack in devis_data['body']['result']:
        pack_code = pack.get('codeProduit', 'N/A')
        pack_status = pack.get('packDisponible', 'N/A')
        is_applicable = pack.get('packApplicable', False)
        pack_title = f"Pack {pack_code} - {'Disponible' if is_applicable else 'Non Disponible'}"
        story.append(Paragraph(pack_title, section_style))
        total_prime = f"{float(pack.get('montantTotalPrime', 0)):.3f} TND" if pack.get('montantTotalPrime', 0) != 0 else "-"
        monthly_prime = f"{float(pack.get('montantPrimeDivisePar12', 0)):.3f} TND" if pack.get('montantPrimeDivisePar12', 0) != 0 else "-"
        story.append(Paragraph(f"<b>Prime Totale :</b> {total_prime}", normal_style))
        story.append(Paragraph(f"<b>Prime Mensuelle :</b> {monthly_prime}", normal_style))
        if not is_applicable:
            reason = pack.get('packDisponible', '')
            story.append(Paragraph(f"<b>Raison :</b> {reason}", ParagraphStyle(name='Reason', fontSize=10, textColor=colors.red)))
        story.append(Spacer(1, 0.3*cm))
        guarantees = pack.get('garantieCourtierModels', [])
        table_data = [["Garantie", "Capital", "Franchise", "Code Garantie"]]
        for guarantee in guarantees:
            lib_garantie = guarantee.get('libGarantie', 'N/A')
            capital = f"{float(guarantee.get('capital', 0)):.3f} TND" if guarantee.get('capital', 0) != 0 else '-'
            franchise = guarantee.get('codeFranchise', '-') or '-'
            code_garantie = guarantee.get('codeGarantie', 'N/A')
            table_data.append([lib_garantie, capital, franchise, code_garantie])
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))

    doc.build(story)
    print("Le PDF du devis a été généré avec succès sous le nom 'devis.pdf' !")
    return "Votre devis a été généré ! Le fichier 'devis.pdf' sera téléchargé dans un instant. N'hésitez pas à demander si vous avez besoin d'autre chose !"

# Main unified agent logic
if __name__ == "__main__":
    # Initialize FAISS components
    embedding_model = initialize_embedding_model()
    
    # Initialize Neo4j agent
    neo4j_agent = Neo4jAgent(memory_enabled=True)
    
    print("Tapez votre question d'assurance (ou 'exit' pour quitter) :")
    last_client_ref = None
    last_client_matricule = None
    while True:
        query = input("> ").lower()
        if query == "exit":
            break

        import re
        # Detect client by ref_personne
        match_ref = re.search(r"client\s*(\d+)", query)
        # Detect client by matricule fiscale
        match_mat = re.search(r"matricule\s*fiscale\s*(?:est|=|:)?\s*(\w+)", query)

        if match_mat:
            last_client_matricule = match_mat.group(1)
            neo4j_agent._conversation['person_matricule'] = last_client_matricule
        elif match_ref:
            last_client_ref = match_ref.group(1)
            neo4j_agent._conversation['person_ref'] = last_client_ref

        # Check for devis request
        if any(keyword in query for keyword in ["devis", "quote", "quotation", "assurance estimate"]):
            response = handle_devis_request()
        else:
            category = classify_query(query)
            print(f"Classé comme : {category}")

            # Ajout du contexte client si connu
            if last_client_matricule and "matricule_fiscale" not in query:
                query += f" (matricule fiscale est {last_client_matricule})"
            elif last_client_ref and "ref_personne" not in query:
                query += f" (ref_personne est {last_client_ref})"

            if category == "product":
                response = ask_bh_assurance(query, embedding_model)
            else:
                response = neo4j_agent.execute_query(query)

        print(f"Réponse : {response}\n")

    neo4j_agent.close()
