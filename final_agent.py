import os
import re
import json
from datetime import datetime, timezone
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

# Configuration for Qdrant Agent (Part 1: Product Comprehension)
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "docs_embeddings"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Configuration for Neo4j Agent (Part 2: Client Data Analysis)
NEO4J_URI = "neo4j+s://cd477924.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "RZbkJ7D1h9qp4HdiVKK1l8K3Y5I3tZjnwF939p0Uoz0"
NEO4J_DATABASE = "neo4j"

# Persistent conversation memory for Qdrant Agent
conversation_history = []
CONVERSATION_FILE = "conversation_history.json"

def save_conversation_to_file():
    try:
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {e}")

# Initialize Qdrant client and embedding model
def initialize_qdrant_and_embedding():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    embedding_model = TextEmbedding()
    return client, embedding_model

# Clean retrieved content
def clean_content(raw_text: str) -> str:
    text = raw_text
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r" +", " ", text)
    return text.strip()

# Query Qdrant and generate response with OpenAI, using conversation memory
def ask_bh_assurance(query: str, client: QdrantClient, embedding_model: TextEmbedding):
    query_embedding = list(embedding_model.embed([query]))[0]
    search_response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=5,
        with_payload=True
    )
    context = ""
    for result in search_response.points:
        payload = result.payload or {}
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
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        # Memory settings
        self.memory_enabled = memory_enabled
        self.memory_path = memory_path or os.path.join(os.getcwd(), "agent_memory.json")
        self.memory_max = memory_max
        self._memory_cache: list[dict] = []
        # Conversational ephemeral context (not persisted): track identified user & last sinistres list
        self._conversation: dict[str, Any] = {
            'person_matricule': None,     # last declared matricule fiscale by user
            'sinistres': []               # list of last returned claim numbers
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
        # Use timezone-aware UTC timestamp (avoid deprecated utcnow())
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
        # Simple keyword overlap scoring
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

        Node Labels and Properties:

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
        """

        # Assemble memory context if enabled
        memory_context = ""
        if self.memory_enabled:
            rel_mem = self._relevant_memory(natural_language_query, k=3)
            if rel_mem:
                mem_lines = []
                for m in rel_mem:
                    mem_lines.append(f"- Q: {m['query']} => Cypher: {m['cypher'][:220]}... (résultats: {m['result_count']})")
                memory_context = "Historique pertinent récent:\n" + "\n".join(mem_lines) + "\n\n"

        # Conversational context injection (ephemeral, based on previous turns within same run)
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

{conversation_context}If the user question contains des pronoms ou références comme "mes sinistres", "leur numéro", "ceux-ci" ou "les précédents", utilise le contexte conversationnel ci-dessus pour résoudre à quelles entités (personne ou sinistres) cela fait référence. Si le contexte n'existe pas, ne devine pas : reformule la requête pour chercher explicitement. N'invente jamais de numéros.

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
    9. Les mots "client", "assuré", "souscripteur" désignent indistinctement une personne morale OU physique : modéliser avec un motif multi-label (p:PersonneMorale|PersonnePhysique). Conserver les propriétés (ex: ref_personne) dans le même map.
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
        # Remove markdown code block delimiters if present
        if cypher_query.startswith("```cypher") and cypher_query.endswith("```"):
            cypher_query = cypher_query[len("```cypher\n"): -len("```")].strip()
        return self._sanitize_cypher(cypher_query)

    def _sanitize_cypher(self, query: str) -> str:
        """Basic cleanup to avoid returning raw path patterns in RETURN and add default LIMIT if missing."""
        # Remove trailing semicolons
        query = query.strip().rstrip(';').strip()
        # If RETURN clause contains relationship patterns, strip them to variables
        # Collect declared variable names from node and relationship patterns to validate RETURN tokens
        declared_vars = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:', query))
        declared_vars.update(re.findall(r'\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', query))

        def _fix_return(line: str) -> str:
            parts = [p.strip() for p in line.split(',')]
            cleaned = []
            for p in parts:
                if '-[' in p or ')-' in p:
                    # Attempt to extract variable names (tokens before ':' or '(' )
                    vars_found = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', p)
                    # Heuristic: keep short variable names present earlier in query (avoid keywords)
                    keywords = {'MATCH','WITH','WHERE','RETURN','DISTINCT','OPTIONAL','CALL','ORDER','BY','LIMIT','SKIP','AS','AND','OR','NOT','EXISTS'}
                    vars_kept = [v for v in vars_found if v.upper() not in keywords]
                    if vars_kept:
                        cleaned.extend(vars_kept)
                else:
                    cleaned.append(p)
            # De-duplicate order preserving
            seen = set(); dedup=[]
            for c in cleaned:
                # Remove bare relationship type names (all caps and not declared as variable)
                if c.isupper() and c not in declared_vars:
                    continue
                # Remove tokens that look like variable names but never declared
                if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', c) and c not in declared_vars:
                    continue
                if c not in seen:
                    seen.add(c); dedup.append(c)
            return ', '.join(dedup) if dedup else line
        # Process RETURN line
        lines = query.split('\n')
        for i,l in enumerate(lines):
            if re.match(r'\s*RETURN\b', l, re.IGNORECASE):
                prefix, rest = l.split('RETURN',1)
                fixed = _fix_return(rest)
                lines[i] = f"{prefix}RETURN {fixed}".rstrip()
        query = '\n'.join(lines)
        # Add LIMIT 100 if no LIMIT and not aggregation that already limited
        if re.search(r'\bRETURN\b', query, re.IGNORECASE) and not re.search(r'\bLIMIT\b', query, re.IGNORECASE):
            query += "\nLIMIT 100"
        return query

    def _refine_query_on_error(self, nl_query: str, bad_cypher: str, error_text: str) -> str:
        """Ask LLM to repair Cypher given the error."""
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
        """Format raw result records into a concise French answer using the LLM (negative answer if empty)."""
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
        # Update conversational context before formatting so follow-ups can reference it
        self._update_conversation_context(natural_language_query, records)
        formatted_result = self.format_results(natural_language_query, records)
        # Store memory with a small sample (first record) to keep size small
        self._add_memory(natural_language_query, cypher_query, records[:1])
        return formatted_result

    # ---------------- Conversational context helpers (ephemeral) -----------------
    def _update_conversation_context(self, nl_query: str, records: list[dict]):
        """Extract simple entities (matricule fiscale, sinistre numbers) for follow-up reference resolution."""
        # Detect new matricule in user query
        matricule_match = re.search(r"matricule\s+fiscale\s*(?:est|=|:)?\s*([A-Z0-9]+)", nl_query, flags=re.IGNORECASE)
        if matricule_match:
            new_mat = matricule_match.group(1).strip()
            if new_mat and new_mat != self._conversation.get('person_matricule'):
                self._conversation['person_matricule'] = new_mat
                # Clear previous sinistres when identifying a new person
                self._conversation['sinistres'] = []
        # Collect num_sinistre from returned records
        sin_numbers: set[int] = set(self._conversation.get('sinistres', []))
        for rec in records:
            # Look through dict values to find nodes/structures containing num_sinistre
            for val in rec.values():
                try:
                    # If value is a Neo4j node with dict-like interface
                    if isinstance(val, dict) and 'num_sinistre' in val:
                        sin_numbers.add(val['num_sinistre'])
                    else:
                        # Attempt attribute access
                        num = getattr(val, 'get', None)
                        if callable(num):
                            maybe = val.get('num_sinistre')
                            if maybe is not None:
                                sin_numbers.add(maybe)
                except Exception:
                    continue
            # Direct property on record (flattened)
            if 'num_sinistre' in rec:
                try:
                    sin_numbers.add(rec['num_sinistre'])
                except Exception:
                    pass
        if sin_numbers:
            # Keep a limited window
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
            category = "product"  # Default to product if unclear
        return category
    except Exception:
        return "product"  # Fallback

# Main unified agent logic
if __name__ == "__main__":
    # Initialize Qdrant components
    qdrant_client, embedding_model = initialize_qdrant_and_embedding()
    
    # Initialize Neo4j agent
    neo4j_agent = Neo4jAgent(memory_enabled=True)
    
    print("Type your insurance question (or 'exit' to quit):")
    while True:
        query = input("> ")
        if query.lower() == "exit":
            break
        
        # Classify the query
        category = classify_query(query)
        print(f"Classified as: {category}")
        
        if category == "product":
            response = ask_bh_assurance(query, qdrant_client, embedding_model)
        else:  # client
            response = neo4j_agent.execute_query(query)
        
        print(f"Response: {response}\n")
    
    # Cleanup
    neo4j_agent.close()