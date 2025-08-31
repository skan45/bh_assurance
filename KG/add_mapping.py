import os
import argparse
from typing import Iterator, List , Dict, Any
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

def chunkify(lst: List[Dict[str, Any]], size: int) -> Iterator[List[Dict[str, Any]]]:
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

# -----------------------------
# Cypher statements (parameterized)
# -----------------------------

CONSTRAINTS = [
    "CREATE CONSTRAINT profil_cible_lib IF NOT EXISTS FOR (n:ProfilCible) REQUIRE n.lib_profil IS UNIQUE",
]

CYPHER_PROFILS = """
UNWIND $rows AS row
MERGE (b:Branche {lib_branche: row.lib_branche})
MERGE (sb:SousBranche {lib_sous_branche: row.lib_sous_branche})
MERGE (p:Produit {lib_produit: row.lib_produit})
MERGE (sb)-[:EST_UNE_SOUS_BRANCHE_DE]->(b)
MERGE (p)-[:EST_UN_PRODUIT_DE]->(sb)
WITH row, p
UNWIND split(row.profils_cibles, ';') AS profil
MERGE (pc:ProfilCible {lib_profil: trim(profil)})
MERGE (p)-[:DESTINE_A]->(pc)
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
        with driver.session(database=database) as session:
            session.run(cypher, rows=chunk)

def load_profils_cibles(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "lib_branche": to_str(r.get("LIB_BRANCHE")),
            "lib_sous_branche": to_str(r.get("LIB_SOUS_BRANCHE")),
            "lib_produit": to_str(r.get("LIB_PRODUIT")),
            "profils_cibles": to_str(r.get("Profils cibles")),
        })
    _execute_batches(driver, database, CYPHER_PROFILS, rows, batch_size, "Profils Cibles", progress)

# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Load product target profiles into Neo4j KG")
    parser.add_argument(
        "--profiles",
        required=False,
        default="added_data/Mapping produits vs profils_cibles.xlsx",
        help="Path to the Profiles Excel workbook (default: added_data/Mapping produits vs profils_cibles.xlsx)"
    )
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687"), help="Neo4j URI (default: neo4j://127.0.0.1:7687)")
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"), help="Neo4j username (default: neo4j)")
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD", "azerty2002"), help="Neo4j password (set NEO4J_PASSWORD env var or provide via --password)")
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"), help="Database name (default: neo4j)")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bars")
    args = parser.parse_args()

    profiles_path = args.profiles
    if not os.path.isabs(profiles_path):
        profiles_path = os.path.join(os.path.dirname(__file__), profiles_path)
    if not os.path.exists(profiles_path):
        raise FileNotFoundError(f"Profiles Excel file not found at: {profiles_path}")

    # Read Excel file
    try:
        df_profiles = pd.read_excel(profiles_path, sheet_name="Sheet1", engine="openpyxl")
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel file '{profiles_path}': {e}") from e

    if not args.password:
        raise SystemExit("Missing password. Provide --password or set NEO4J_PASSWORD.")

    # Connectivity test & driver creation
    try:
        driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
        driver.verify_connectivity()
    except Exception as e:
        raise SystemExit(
            f"Connection failed to {args.uri} as {args.user}: {e}\n"
            "Tips: 1) Ensure Neo4j is running and the database is active. "
            "2) Verify the URI (neo4j://127.0.0.1:7687) matches your settings. "
            "3) Check username (neo4j) and password (azerty2002).")

    # Run constraints
    with driver.session(database=args.database) as session:
        run_constraints(session)

    # Load data
    load_profils_cibles(driver, args.database, df_profiles, args.batch_size, progress=not args.no_progress)

    driver.close()
    print("Profile target load completed successfully.")

if __name__ == "__main__":
    main()