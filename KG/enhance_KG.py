import os
import argparse
import csv
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
    if pd.isna(x):
        return None
    if isinstance(x, str):
        x = x.replace(',', '.').replace(' ', '')
    try:
        return float(x)
    except Exception:
        return None

def to_int(x):
    try:
        if pd.isna(x):
            return None
        if isinstance(x, str):
            x = x.replace(' ', '')
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
    "CREATE CONSTRAINT garantie_code IF NOT EXISTS FOR (n:Garantie) REQUIRE n.code_garantie IS UNIQUE",
]

CYPHER_GARANTIES = """
UNWIND $rows AS row
MERGE (g:Garantie {code_garantie: row.code_garantie})
SET g.lib_garantie = row.lib_garantie,
    g.description = row.description
WITH row, g
MERGE (b:Branche {lib_branche: row.lib_branche})
MERGE (sb:SousBranche {lib_sous_branche: row.lib_sous_branche})
MERGE (p:Produit {lib_produit: row.lib_produit})
MERGE (sb)-[:EST_UNE_SOUS_BRANCHE_DE]->(b)
MERGE (p)-[:EST_UN_PRODUIT_DE]->(sb)
MERGE (p)-[:OFFRE]->(g)
"""

CYPHER_CONTRAT_GARANTIES = """
UNWIND $rows AS row
MERGE (c:Contrat {num_contrat: row.num_contrat})
MERGE (g:Garantie {code_garantie: row.code_garantie})
SET g.lib_garantie = coalesce(g.lib_garantie, row.lib_garantie)
MERGE (c)-[r:INCLUT]->(g)
SET r.capital_assure = row.capital_assure
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


def load_garanties(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "code_garantie": to_int(r.get("CODE_GARANTIE")),
            "lib_garantie": to_str(r.get("LIB_GARANTIE")),
            "description": to_str(r.get("Description")),
            "lib_branche": to_str(r.get("LIB_BRANCHE")),
            "lib_sous_branche": to_str(r.get("LIB_SOUS_BRANCHE")),
            "lib_produit": to_str(r.get("LIB_PRODUIT")),
        })
    _execute_batches(driver, database, CYPHER_GARANTIES, rows, batch_size, "Garanties", progress)


def load_contrat_garanties(driver, database: str, df: pd.DataFrame, batch_size: int, progress: bool = True):
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "num_contrat": to_int(r.get("NUM_CONTRAT")),
            "code_garantie": to_int(r.get("CODE_GARANTIE")),
            "capital_assure": to_float(r.get("CAPITAL_ASSURE")),
            "lib_garantie": to_str(r.get("LIB_GARANTIE")),
        })
    _execute_batches(driver, database, CYPHER_CONTRAT_GARANTIES, rows, batch_size, "Contrat-Garanties", progress)

# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Load additional insurance Excel data into Neo4j KG")
    parser.add_argument(
        "--garanties",
        required=False,
        default="added_data\\Description_garanties.xlsx",
        help="Path to the Garanties Excel workbook (default: added_data\\Description_garanties.xlsx in current folder)"
    )
    parser.add_argument(
        "--contrat-garanties",
        required=False,
        default="added_data\\Données_Assurance_S1.2_S2.csv",
        help="Path to the Contrat-Garanties Excel workbook (default: added_data\\Données_Assurance_S1.2_S2.csv in current folder)"
    )
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "neo4j+s://cd477924.databases.neo4j.io"), help="Neo4j bolt/neo4j URI (use neo4j+s:// for Aura)")
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"), help="Neo4j username")
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD","RZbkJ7D1h9qp4HdiVKK1l8K3Y5I3tZjnwF939p0Uoz0"), help="Neo4j password (or set NEO4J_PASSWORD env var)")
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"), help="Database name (Aura default 'neo4j')")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bars")
    args = parser.parse_args()

    garanties_path = args.garanties
    if not os.path.isabs(garanties_path):
        garanties_path = os.path.join(os.path.dirname(__file__), garanties_path)
    if not os.path.exists(garanties_path):
        raise FileNotFoundError(f"Garanties Excel file not found at: {garanties_path}")

    contrat_garanties_path = args.contrat_garanties
    if not os.path.isabs(contrat_garanties_path):
        contrat_garanties_path = os.path.join(os.path.dirname(__file__), contrat_garanties_path)
    if not os.path.exists(contrat_garanties_path):
        raise FileNotFoundError(f"Contrat-Garanties Excel file not found at: {contrat_garanties_path}")

    # -----------------------------
    # Unified readers (Excel or CSV)
    # -----------------------------
    def read_table(path: str, sheet: str = "Sheet1") -> pd.DataFrame:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".xlsx", ".xlsm", ".xls"):
            # Explicit engine to avoid pandas guessing issues
            engine = None
            if ext in (".xlsx", ".xlsm"):
                engine = "openpyxl"  # openpyxl handles modern Excel formats
            try:
                return pd.read_excel(path, sheet_name=sheet, engine=engine)
            except Exception as e:
                raise RuntimeError(f"Failed to read Excel file '{path}': {e}") from e
        elif ext == ".csv":
            # Attempt encoding detection (optional dependency chardet)
            encodings_to_try = []
            try:
                import chardet  # type: ignore
                with open(path, 'rb') as bf:
                    raw_sample = bf.read(100000)
                detected = chardet.detect(raw_sample)
                if detected and detected.get('encoding'):
                    encodings_to_try.append(detected['encoding'])
            except Exception:
                pass
            # Append common fallbacks (UTF-8 with errors, cp1252, latin-1)
            encodings_to_try.extend(["utf-8", "cp1252", "latin-1"])  # order matters

            # Delimiter sniff (read raw text with first workable encoding)
            last_err = None
            sep = None
            for enc in encodings_to_try:
                try:
                    with open(path, 'r', encoding=enc, errors='strict') as tf:
                        sample = tf.read(4096)
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
                        sep = dialect.delimiter
                    except Exception:
                        # Heuristic: semicolon appears in European-formatted CSV
                        if sample.count(';') > sample.count(','):
                            sep = ';'
                        else:
                            sep = ','
                    # Now actually load with this encoding
                    df = pd.read_csv(path, sep=sep, engine='python', encoding=enc)
                    return df
                except Exception as e:
                    last_err = e
                    continue
            raise RuntimeError(f"Failed to read CSV file '{path}' after trying encodings {encodings_to_try}: {last_err}")
        else:
            raise ValueError(f"Unsupported file extension for '{path}'. Expected one of .xlsx, .xlsm, .xls, .csv")

    df_garanties = read_table(garanties_path, sheet="Sheet1")
    df_contrat_garanties = read_table(contrat_garanties_path, sheet="Sheet1")

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

    # Load data
    load_garanties(driver, args.database, df_garanties, args.batch_size, progress=not args.no_progress)
    load_contrat_garanties(driver, args.database, df_contrat_garanties, args.batch_size, progress=not args.no_progress)

    driver.close()
    print("Additional load completed successfully.")

if __name__ == "__main__":
    main()