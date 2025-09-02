sudo docker compose up -d --build
python3 -m venv venv 
source venv/bin/activate
pip install -r requirements.txt
python3 process_PDF/load_to_qdrant.py
python3 KG/create_KG.py
python3 KG/enhance_KG.py
python3 KG/add_mapping.py
python3 database/migrate_db.py
