import os
import argparse
from typing import List, Dict, Any, Iterator
import pandas as pd
from neo4j import GraphDatabase
try:
    from tqdm import tqdm
except ImportError:  # fallback if not installed
    def tqdm(iterable, **kwargs):
        return iterable

# -----------------------------
# Helpers
# -----------------------------

def to_str(x):
    if pd.isna(x):
        return None
    s = str(x)
    return s.strip()

def to_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None

def to_int(x):
    try:
        if pd.isna(x):
            return None
        # Some numeric ids may come as floats in Excel
        return int(float(x))
    except Exception:
        return None

def to_date_str(x):
    if pd.isna(x):
        return None
    # try parse
    try:
        dt = pd.to_datetime(x, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def chunkify(lst: List[Dict[str, Any]], size: int) -> Iterator[List[Dict[str, Any]]]:
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

# -----------------------------
# Cypher statements (parameterized)
# -----------------------------

CONSTRAINTS = [
    "CREATE CONSTRAINT personne_physique_ref IF NOT EXISTS FOR (n:PersonnePhysique) REQUIRE n.ref_personne IS UNIQUE",
    "CREATE CONSTRAINT personne_morale_ref IF NOT EXISTS FOR (n:PersonneMorale) REQUIRE n.ref_personne IS UNIQUE",
    "CREATE CONSTRAINT contrat_num IF NOT EXISTS FOR (n:Contrat) REQUIRE n.num_contrat IS UNIQUE",
    "CREATE CONSTRAINT sinistre_num IF NOT EXISTS FOR (n:Sinistre) REQUIRE n.num_sinistre IS UNIQUE",
    "CREATE CONSTRAINT produit_name IF NOT EXISTS FOR (n:Produit) REQUIRE n.lib_produit IS UNIQUE",
    "CREATE CONSTRAINT sous_branche_name IF NOT EXISTS FOR (n:SousBranche) REQUIRE n.lib_sous_branche IS UNIQUE",
    "CREATE CONSTRAINT branche_name IF NOT EXISTS FOR (n:Branche) REQUIRE n.lib_branche IS UNIQUE",
]

CYPHER_MERGE_MAPPING = """
UNWIND $rows AS row
MERGE (b:Branche {lib_branche: row.lib_branche})
MERGE (sb:SousBranche {lib_sous_branche: row.lib_sous_branche})
MERGE (p:Produit {lib_produit: row.lib_produit})
MERGE (sb)-[:EST_UNE_SOUS_BRANCHE_DE]->(b)
MERGE (p)-[:EST_UN_PRODUIT_DE]->(sb)
"""

CYPHER_PERSONNE_MORALE = """
UNWIND $rows AS row
MERGE (p:PersonneMorale {ref_personne: row.ref_personne})
SET p.raison_sociale = row.raison_sociale,
    p.matricule_fiscale = row.matricule_fiscale,
    p.lib_secteur_activite = row.lib_secteur_activite,
    p.lib_activite = row.lib_activite,
    p.ville = row.ville,
    p.lib_gouvernorat = row.lib_gouvernorat,
    p.ville_gouvernorat = row.ville_gouvernorat
"""

CYPHER_PERSONNE_PHYSIQUE = """
UNWIND $rows AS row
MERGE (p:PersonnePhysique {ref_personne: row.ref_personne})
SET p.nom_prenom = row.nom_prenom,
    p.date_naissance = row.date_naissance,
    p.lieu_naissance = row.lieu_naissance,
    p.code_sexe = row.code_sexe,
    p.situation_familiale = row.situation_familiale,
    p.num_piece_identite = row.num_piece_identite,
    p.lib_secteur_activite = row.lib_secteur_activite,
    p.lib_profession = row.lib_profession,
    p.ville = row.ville,
    p.lib_gouvernorat = row.lib_gouvernorat,
    p.ville_gouvernorat = row.ville_gouvernorat
"""

CYPHER_CONTRATS = """
UNWIND $rows AS row
MERGE (c:Contrat {num_contrat: row.num_contrat})
SET c.lib_produit = row.lib_produit,
    c.effet_contrat = row.effet_contrat,
    c.date_expiration = row.date_expiration,
    c.prochain_terme = row.prochain_terme,
    c.lib_etat_contrat = row.lib_etat_contrat,
    c.branche = row.branche,
    c.somme_quittances = row.somme_quittances,
    c.statut_paiement = row.statut_paiement,
    c.capital_assure = row.capital_assure
WITH row, c
// link holder (either PersonnePhysique or PersonneMorale)
OPTIONAL MATCH (pp:PersonnePhysique {ref_personne: row.ref_personne})
OPTIONAL MATCH (pm:PersonneMorale {ref_personne: row.ref_personne})
WITH row, c, coalesce(pp, pm) AS holder
FOREACH (_ IN CASE WHEN holder IS NULL THEN [] ELSE [1] END |
  MERGE (holder)-[:A_SOUSCRIT]->(c)
)
// link to Produit by lib_produit if exists
FOREACH (_ IN CASE WHEN row.lib_produit IS NULL THEN [] ELSE [1] END |
  MERGE (p:Produit {lib_produit: row.lib_produit})
  MERGE (c)-[:PORTE_SUR]->(p)
)
// link to Branche by branche if exists
FOREACH (_ IN CASE WHEN row.branche IS NULL THEN [] ELSE [1] END |
  MERGE (b:Branche {lib_branche: row.branche})
  MERGE (c)-[:DE_BRANCHE]->(b)
)
"""

CYPHER_SINISTRES = """
UNWIND $rows AS row
MERGE (s:Sinistre {num_sinistre: row.num_sinistre})
SET s.lib_branche = row.lib_branche,
    s.lib_sous_branche = row.lib_sous_branche,
    s.lib_produit = row.lib_produit,
    s.nature_sinistre = row.nature_sinistre,
    s.lib_type_sinistre = row.lib_type_sinistre,
    s.taux_responsabilite = row.taux_responsabilite,
    s.date_survenance = row.date_survenance,
    s.date_declaration = row.date_declaration,
    s.date_ouverture = row.date_ouverture,
    s.observation_sinistre = row.observation_sinistre,
    s.lib_etat_sinistre = row.lib_etat_sinistre,
    s.lieu_accident = row.lieu_accident,
    s.motif_reouverture = row.motif_reouverture,
    s.montant_encaisse = row.montant_encaisse,
    s.montant_a_encaisser = row.montant_a_encaisser
WITH row, s
// link to Contrat
OPTIONAL MATCH (c:Contrat {num_contrat: row.num_contrat})
FOREACH (_ IN CASE WHEN c IS NULL THEN [] ELSE [1] END |
  MERGE (s)-[:CONCERNE]->(c)
)
// link to Produit taxonomy
FOREACH (_ IN CASE WHEN row.lib_produit IS NULL THEN [] ELSE [1] END |
  MERGE (p:Produit {lib_produit: row.lib_produit})
  MERGE (s)-[:PORTE_SUR]->(p)
)
FOREACH (_ IN CASE WHEN row.lib_branche IS NULL THEN [] ELSE [1] END |
  MERGE (b:Branche {lib_branche: row.lib_branche})
  MERGE (s)-[:DE_BRANCHE]->(b)
)
FOREACH (_ IN CASE WHEN row.lib_sous_branche IS NULL THEN [] ELSE [1] END |
  MERGE (sb:SousBranche {lib_sous_branche: row.lib_sous_branche})
  MERGE (s)-[:DE_SOUS_BRANCHE]->(sb)
)
"""

# -----------------------------
# Loading logic
# -----------------------------

def run_constraints(session):
    for stmt in CONSTRAINTS:
        session.run(stmt)


def _execute_batches(driver, database: str, cypher: str, rows, batch_size: int, desc: str, progress: bool):
    total = len(rows)
    for i in tqdm(range(0, total, batch_size), desc=desc, disable=not progress):
        chunk = rows[i:i+batch_size]
        # open a short-lived session per batch to avoid stale/closed session issues
        with driver.session(database=database) as session:
            session.run(cypher, rows=chunk)


def load_mapping(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "lib_branche": to_str(r.get("LIB_BRANCHE")),
            "lib_sous_branche": to_str(r.get("LIB_SOUS_BRANCHE")),
            "lib_produit": to_str(r.get("LIB_PRODUIT")),
        })
    _execute_batches(driver, database, CYPHER_MERGE_MAPPING, rows, batch_size, "Mapping produits", progress)


def load_personne_morale(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "ref_personne": to_int(r.get("REF_PERSONNE")),
            "raison_sociale": to_str(r.get("RAISON_SOCIALE")),
            "matricule_fiscale": to_str(r.get("MATRICULE_FISCALE")),
            "lib_secteur_activite": to_str(r.get("LIB_SECTEUR_ACTIVITE")),
            "lib_activite": to_str(r.get("LIB_ACTIVITE")),
            "ville": to_str(r.get("VILLE")),
            "lib_gouvernorat": to_str(r.get("LIB_GOUVERNORAT")),
            "ville_gouvernorat": to_str(r.get("VILLE_GOUVERNORAT")),
        })
    _execute_batches(driver, database, CYPHER_PERSONNE_MORALE, rows, batch_size, "Personnes morales", progress)


def load_personne_physique(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "ref_personne": to_int(r.get("REF_PERSONNE")),
            "nom_prenom": to_str(r.get("NOM_PRENOM")),
            "date_naissance": to_date_str(r.get("DATE_NAISSANCE")),
            "lieu_naissance": to_str(r.get("LIEU_NAISSANCE")),
            "code_sexe": to_str(r.get("CODE_SEXE")),
            "situation_familiale": to_str(r.get("SITUATION_FAMILIALE")),
            "num_piece_identite": to_int(r.get("NUM_PIECE_IDENTITE")),
            "lib_secteur_activite": to_str(r.get("LIB_SECTEUR_ACTIVITE")),
            "lib_profession": to_str(r.get("LIB_PROFESSION")),
            "ville": to_str(r.get("VILLE")),
            "lib_gouvernorat": to_str(r.get("LIB_GOUVERNORAT")),
            "ville_gouvernorat": to_str(r.get("VILLE_GOUVERNORAT")),
        })
    _execute_batches(driver, database, CYPHER_PERSONNE_PHYSIQUE, rows, batch_size, "Personnes physiques", progress)


def load_contrats(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "num_contrat": to_int(r.get("NUM_CONTRAT")),
            "lib_produit": to_str(r.get("LIB_PRODUIT")),
            "effet_contrat": to_date_str(r.get("EFFET_CONTRAT")),
            "date_expiration": to_date_str(r.get("DATE_EXPIRATION")),
            "prochain_terme": to_str(r.get("PROCHAIN_TERME")),
            "lib_etat_contrat": to_str(r.get("LIB_ETAT_CONTRAT")),
            "branche": to_str(r.get("branche")),
            "somme_quittances": to_float(r.get("somme_quittances")),
            "statut_paiement": to_str(r.get("statut_paiement")),
            "capital_assure": to_float(r.get("Capital_assure")),
            "ref_personne": to_int(r.get("REF_PERSONNE")),
        })
    _execute_batches(driver, database, CYPHER_CONTRATS, rows, batch_size, "Contrats", progress)


def load_sinistres(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "num_sinistre": to_int(r.get("NUM_SINISTRE")),
            "num_contrat": to_int(r.get("NUM_CONTRAT")),
            "lib_branche": to_str(r.get("LIB_BRANCHE")),
            "lib_sous_branche": to_str(r.get("LIB_SOUS_BRANCHE")),
            "lib_produit": to_str(r.get("LIB_PRODUIT")),
            "nature_sinistre": to_str(r.get("NATURE_SINISTRE")),
            "lib_type_sinistre": to_str(r.get("LIB_TYPE_SINISTRE")),
            "taux_responsabilite": to_float(r.get("TAUX_RESPONSABILITE")),
            "date_survenance": to_date_str(r.get("DATE_SURVENANCE")),
            "date_declaration": to_date_str(r.get("DATE_DECLARATION")),
            "date_ouverture": to_date_str(r.get("DATE_OUVERTURE")),
            "observation_sinistre": to_str(r.get("OBSERVATION_SINISTRE")),
            "lib_etat_sinistre": to_str(r.get("LIB_ETAT_SINISTRE")),
            "lieu_accident": to_str(r.get("LIEU_ACCIDENT")),
            "motif_reouverture": to_str(r.get("MOTIF_REOUVERTURE")),
            "montant_encaisse": to_float(r.get("MONTANT_ENCAISSE")),
            "montant_a_encaisser": to_float(r.get("MONTANT_A_ENCAISSER")),
        })
    _execute_batches(driver, database, CYPHER_SINISTRES, rows, batch_size, "Sinistres", progress)

# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Load insurance Excel into Neo4j KG")
    parser.add_argument(
        "--excel",
        required=False,
        default="Données_Assurance_S1.1.xlsx",
        help="Path to the Excel workbook (default: Données_Assurance_S1.1.xlsx in current folder)"
    )
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "neo4j+s://cd477924.databases.neo4j.io"), help="Neo4j bolt/neo4j URI (use neo4j+s:// for Aura)")
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"), help="Neo4j username")
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD","RZbkJ7D1h9qp4HdiVKK1l8K3Y5I3tZjnwF939p0Uoz0"), help="Neo4j password (or set NEO4J_PASSWORD env var)")
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"), help="Database name (Aura default 'neo4j')")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bars")
    args = parser.parse_args()

    excel_path = args.excel
    # If relative, resolve relative to script directory
    if not os.path.isabs(excel_path):
        excel_path = os.path.join(os.path.dirname(__file__), excel_path)

    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found at: {excel_path}")

    # Read sheets
    xls = pd.ExcelFile(excel_path)
    required_sheets = ["personne_morale", "personne_physique", "Contrats", "sinistres", "Mapping_Produits"]
    for s in required_sheets:
        if s not in xls.sheet_names:
            raise RuntimeError(f"Missing required sheet: {s}")

    df_personne_morale = pd.read_excel(excel_path, sheet_name="personne_morale")
    df_personne_physique = pd.read_excel(excel_path, sheet_name="personne_physique")
    df_contrats = pd.read_excel(excel_path, sheet_name="Contrats")
    df_sinistres = pd.read_excel(excel_path, sheet_name="sinistres")
    df_mapping = pd.read_excel(excel_path, sheet_name="Mapping_Produits")

    if not args.password:
        raise SystemExit("Missing password. Provide --password or set NEO4J_PASSWORD.")

    # Connectivity test & driver creation
    try:
        driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
        driver.verify_connectivity()
    except Exception as e:
        raise SystemExit(
            f"Connection failed to {args.uri} as {args.user}: {e}\n"
            "Tips: 1) Use neo4j+s:// URI for Aura (copy from Connection Details). "
            "2) Ensure username/password are correct. 3) If rotating credentials, re-download the Aura connection string." )

    # One session for constraints (schema ops) then short sessions per batch for data
    with driver.session(database=args.database) as session:
        run_constraints(session)

    # Load taxonomy first
    load_mapping(driver, args.database, df_mapping, args.batch_size, progress=not args.no_progress)

    # Load entities
    load_personne_morale(driver, args.database, df_personne_morale, args.batch_size, progress=not args.no_progress)
    load_personne_physique(driver, args.database, df_personne_physique, args.batch_size, progress=not args.no_progress)
    load_contrats(driver, args.database, df_contrats, args.batch_size, progress=not args.no_progress)
    load_sinistres(driver, args.database, df_sinistres, args.batch_size, progress=not args.no_progress)

    driver.close()
    print("Load completed successfully.")

if __name__ == "__main__":
    main()


