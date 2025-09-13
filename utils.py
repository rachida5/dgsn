# utils.py
import io
import os
import base64
import numpy as np
from PIL import Image
from datetime import date
from deepface import DeepFace
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, Table, TableStyle, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# Initialisation DeepFace
def initialize_deepface():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    deepface_home = os.path.join(script_dir, "deepface_data")
    os.makedirs(deepface_home, exist_ok=True)
    os.environ['DEEPFACE_HOME'] = deepface_home

# Utilitaires d'image
def image_to_bytes(img: Image.Image) -> bytes:
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    return buffered.getvalue()

def preprocess_image(image: Image.Image) -> np.ndarray:
    return np.array(image.convert("RGB"))

def is_valid_image(image_bytes: bytes) -> bool:
    try:
        Image.open(io.BytesIO(image_bytes))
        return True
    except Exception:
        return False

# Reconnaissance faciale
def find_match(uploaded_image: Image.Image, cursor, model_name: str = "Facenet", threshold: float = 0.40, top_k: int = 3):
    uploaded_array = preprocess_image(uploaded_image)
    cursor.execute("""
        SELECT c.id, c.nom, c.crime, c.description, ic.image
        FROM criminals c
        JOIN images_criminels ic ON ic.criminal_id = c.id
        ORDER BY c.id
    """)
    rows = cursor.fetchall()
    if not rows:
        return []
    
    by_person = {}
    for cid, nom, crime, desc, img_bytes in rows:
        if not img_bytes or not is_valid_image(img_bytes):
            continue
        ref_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        by_person.setdefault(cid, {"nom": nom, "crime": crime, "description": desc, "refs": []})
        by_person[cid]["refs"].append(ref_img)
        
    results = []
    for cid, info in by_person.items():
        best_dist, best_ref = None, None
        for ref_img in info["refs"]:
            ref_arr = preprocess_image(ref_img)
            try:
                res = DeepFace.verify(uploaded_array, ref_arr, model_name=model_name, enforce_detection=False)
                dist = res.get("distance", 1.0)
                if best_dist is None or dist < best_dist:
                    best_dist, best_ref = dist, ref_img
            except Exception:
                continue
        
        if best_dist is not None and best_dist <= threshold:
            similarity = round((1 - best_dist) * 100, 2)
            results.append({
                "id": cid,
                "nom": info["nom"],
                "crime": info["crime"],
                "description": info["description"],
                "similarity": similarity,
                "distance": best_dist,
                "reference_image": best_ref
            })
            
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:max(1, int(top_k))]


# Génération PDF
def generate_pdf(criminal_data, image_data, similarity, current_date):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=3*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = []

    # Styles personnalisés
    title_style = ParagraphStyle(name='Title', fontSize=20, textColor=colors.black, alignment=1, spaceAfter=10)
    label_style = ParagraphStyle(name='Label', fontSize=12, textColor=colors.HexColor('#495057'), fontName='Helvetica-Bold', spaceAfter=4)
    value_style = ParagraphStyle(name='Value', fontSize=14, textColor=colors.black, spaceAfter=8)
    section_style = ParagraphStyle(name='Section', fontSize=16, textColor=colors.HexColor('#d32f2f'), fontName='Helvetica-Bold', spaceAfter=10, spaceBefore=10)
    confidential_style = ParagraphStyle(name='Confidential', fontSize=16, textColor=colors.red, alignment=1, fontName='Helvetica-Bold')

    # En-tête avec logo (centré)
    try:
        logo = ReportLabImage("logo.png", width=2*cm, height=2*cm)
        logo.hAlign = 'CENTER'
        elements.append(logo)
    except Exception:
        elements.append(Paragraph("CASIER JUDICIAIRE", title_style))
        
    elements.append(Spacer(1, 0.5*cm))


    # Photo du criminel (centrée)
    if image_data:
        try:
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((150, 200))
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG")
            img_element = ReportLabImage(img_buffer, width=5*cm, height=6.5*cm)
            img_element.hAlign = 'CENTER'
            elements.append(img_element)

        except Exception:
            elements.append(Paragraph("Photo non disponible", value_style))
    else:
        elements.append(Paragraph("Pas de photo disponible", value_style))

    elements.append(Spacer(1, 0.5*cm))
    
    # Informations d'identité
    info_data = [
        [Paragraph("IDENTITÉ", section_style)],
        [Paragraph("Nom complet", label_style), Paragraph(f"{criminal_data.get('nom', '')} {criminal_data.get('prenom', '')}", value_style)],
        [Paragraph("Alias/Surnom", label_style), Paragraph(str(criminal_data.get('alias', 'N/A')), value_style)],
        [Paragraph("Âge", label_style), Paragraph(f"{criminal_data.get('age', 'N/A')} ans", value_style)],
        [Paragraph("Date de naissance", label_style), Paragraph(str(criminal_data.get('date_naissance', 'N/A')), value_style)],
        [Paragraph("Lieu de naissance", label_style), Paragraph(str(criminal_data.get('lieu_naissance', 'N/A')), value_style)],
        [Paragraph("Nationalité", label_style), Paragraph(str(criminal_data.get('nationalite', 'N/A')), value_style)],
        [Paragraph("Téléphone", label_style), Paragraph(str(criminal_data.get('telephone', 'N/A')), value_style)],
        [Paragraph("Adresse", label_style), Paragraph(str(criminal_data.get('adresse', 'N/A')), value_style)],
    ]

    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 1), (-1, -1), 1, colors.HexColor('#e9ecef')),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 0.5*cm))

    # Informations judiciaires
    judicial_data = [
        [Paragraph("INFORMATIONS JUDICIAIRES", section_style)],
        [Paragraph("Infractioncrime", label_style), Paragraph(str(criminal_data.get('crime', 'N/A')), value_style)],
        [Paragraph("Date d'arrestation", label_style), Paragraph(str(criminal_data.get('date_arrestation', 'N/A')), value_style)],
        [Paragraph("Niveau d'implication", label_style), Paragraph(str(criminal_data.get('implication', 'N/A')), value_style)],
        [Paragraph("Description détaillée", label_style), Paragraph(str(criminal_data.get('description', 'N/A')), value_style)],
    ]
    judicial_table = Table(judicial_data, colWidths=[5*cm, 12*cm])
    judicial_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 1), (-1, -1), 1, colors.HexColor('#e9ecef')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ffcdd2')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    elements.append(judicial_table)
    elements.append(Spacer(1, 0.5*cm))

    # Pied de page
    def footer(canvas, doc):
        canvas.saveState()
        footer_table = Table([
            [Paragraph(f"Document généré le {current_date}", value_style)],
            [Paragraph("⚖️ DOCUMENT CONFIDENTIEL", confidential_style)],
        ], colWidths=[A4[0] - 3*cm])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#666666')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#d32f2f')),
        ]))
        
        w, h = footer_table.wrap(doc.width, doc.bottomMargin)
        footer_table.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - doc.topMargin - doc.bottomMargin, id='normal')
    template = PageTemplate(id='main', frames=[frame], onPage=footer)
    doc.addPageTemplates([template])
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def calculate_birthdate_from_age(age, month, day):
    today = date.today()
    birth_year = today.year - age
    if today.month < month or (today.month == month and today.day < day):
        birth_year -= 1
    return date(birth_year, month, day)