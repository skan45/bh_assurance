import pandas as pd
import json

json_file = "middleware/cin_matricule_data.json"

# Function to check if input exists in JSON
def check_input(user_input):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if user_input.isdigit():  # It's a CIN
        if user_input in data["CIN"]:
            print("✅ CIN exists in database.")
        else:
            print("❌ CIN not found.")
    else:  # It's a Matricule Fiscale
        if user_input.upper() in [m.upper() for m in data["MATRICULE_FISCALE"]]:
            print("✅ Matricule Fiscale exists in database.")
        else:
            print("❌ Matricule Fiscale not found.")


