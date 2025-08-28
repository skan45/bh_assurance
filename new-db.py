from neo4j import GraphDatabase

# Neo4j connection
uri = "bolt://localhost:7687"
username = "neo4j"          # replace with your Neo4j username
password = "new_password"  # replace with your Neo4j password

# Path to the generated Cypher script
cql_file = "final_script.cql"

# Connect to Neo4j
driver = GraphDatabase.driver(uri, auth=(username, password))

def clear_database(session):
    """Delete all nodes and relationships in the database."""
    session.run("MATCH (n) DETACH DELETE n;")
    print("Database cleared.")

def run_cypher_script(session, file_path):
    """Run all statements from a Cypher script file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        # Split by double newlines or semicolons to separate statements
        statements = [stmt.strip() for stmt in content.split("\n\n") if stmt.strip()]

    for i, stmt in enumerate(statements, 1):
        try:
            session.run(stmt)
            print(f"Statement {i} executed successfully")
        except Exception as e:
            print(f"Failed to execute statement {i}:\n{stmt}\nError: {e}\n")

if __name__ == "__main__":
    with driver.session() as session:
        clear_database(session)            # optional: clear DB first
        run_cypher_script(session, cql_file)
    driver.close()
    print("All statements processed.")
