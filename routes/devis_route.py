# devis.py
import io
import requests
from datetime import datetime
from fastapi import APIRouter, HTTPException , Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from middleware.jwt_verifier import verify_jwt 

router = APIRouter()

# ---- Request Model ----
class DevisRequest(BaseModel):
    n_cin: str
    valeur_venale: float
    nature_contrat: str
    nombre_place: int
    valeur_a_neuf: float
    date_premiere_mise_en_circulation: str
    capital_bris_de_glace: float
    capital_dommage_collision: float
    puissance: int
    classe: int

# ---- Devis Handler ----
async def handle_devis_request(params: dict):
    required_params = [
        "n_cin",
        "valeur_venale",
        "nature_contrat",
        "nombre_place",
        "valeur_a_neuf",
        "date_premiere_mise_en_circulation",
        "capital_bris_de_glace",
        "capital_dommage_collision",
        "puissance",
        "classe"
    ]

    missing = [p for p in required_params if p not in params or not params[p]]
    if missing:
        return {"error": f"Missing required parameters: {', '.join(missing)}"}

    url = "https://apidevis.onrender.com/api/auto/packs"
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        devis_data = response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching devis data from API: {str(e)}"}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(name='TitleStyle', fontSize=16, leading=20, alignment=1, spaceAfter=12)
    section_style = ParagraphStyle(name='SectionStyle', fontSize=12, leading=14, spaceAfter=8)
    normal_style = styles['Normal']
    normal_style.fontSize = 10

    story = []
    story.append(Paragraph("Devis d'Assurance Automobile", title_style))
    story.append(Spacer(1, 0.5*cm))

    # Params
    story.append(Paragraph("<b>Paramètres du devis saisis :</b>", section_style))
    params_table_data = [["Champ", "Valeur"]]
    for k, v in params.items():
        params_table_data.append([k, str(v)])
    params_table = Table(params_table_data)
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 0.5*cm))

    # Provider
    header = devis_data.get('header', {})
    provider_info = f"<b>Fournisseur :</b> {header.get('providerDescription', 'N/A')} (Code: {header.get('providerCode', 'N/A')})"
    story.append(Paragraph(provider_info, section_style))
    story.append(Spacer(1, 0.5*cm))

    # Packs
    for pack in devis_data['body']['result']:
        pack_code = pack.get('codeProduit', 'N/A')
        is_applicable = pack.get('packApplicable', False)
        pack_title = f"Pack {pack_code} - {'Disponible' if is_applicable else 'Non Disponible'}"
        story.append(Paragraph(pack_title, section_style))

        total_prime = f"{float(pack.get('montantTotalPrime', 0)):.3f} TND" if pack.get('montantTotalPrime', 0) else "-"
        monthly_prime = f"{float(pack.get('montantPrimeDivisePar12', 0)):.3f} TND" if pack.get('montantPrimeDivisePar12', 0) else "-"
        story.append(Paragraph(f"<b>Prime Totale :</b> {total_prime}", normal_style))
        story.append(Paragraph(f"<b>Prime Mensuelle :</b> {monthly_prime}", normal_style))

        guarantees = pack.get('garantieCourtierModels', [])
        table_data = [["Garantie", "Capital", "Franchise", "Code Garantie"]]
        for guarantee in guarantees:
            table_data.append([
                guarantee.get('libGarantie', 'N/A'),
                f"{float(guarantee.get('capital', 0)):.3f} TND" if guarantee.get('capital', 0) else "-",
                guarantee.get('codeFranchise', '-') or "-",
                guarantee.get('codeGarantie', 'N/A')
            ])
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))

    doc.build(story)
    buffer.seek(0)

    return buffer

# ---- Route ----
@router.post("/devis")
async def generate_devis(request: DevisRequest, payload: dict = Depends(verify_jwt)):
    params = request.dict()
    pdf_buffer = await handle_devis_request(params)

    if isinstance(pdf_buffer, dict) and "error" in pdf_buffer:
        raise HTTPException(status_code=400, detail=pdf_buffer["error"])

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=devis.pdf"}
    )

