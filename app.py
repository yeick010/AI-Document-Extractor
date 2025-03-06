import cv2
import pytesseract
import pandas as pd
import fitz  #PyMuPDF
import json
import os
import logging
from flask import Flask, request, render_template, jsonify, send_file
from fpdf import FPDF

# Configura il logging
logging.basicConfig(filename="ocr_tool.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Creazione delle cartelle necessarie
os.makedirs("templates", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Funzione per pre-processare l'immagine
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

# Funzione per estrarre il testo da un'immagine
def extract_text_from_image(image_path, language="eng"):
    processed_img = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_img, lang=language)
    return text.strip()

# Funzione per estrarre il testo da un PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

# Funzione per gestire l'estrazione OCR
def process_file(input_path, language="eng"):
    ext = os.path.splitext(input_path)[-1].lower()
    if ext in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(input_path, language)
    elif ext == '.pdf':
        return extract_text_from_pdf(input_path)
    else:
        return "Formato non supportato"

# API per il caricamento e OCR
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Nessun file caricato"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nessun file selezionato"}), 400
        
        file_path = os.path.join("uploads", file.filename)
        file.save(file_path)
        logging.info(f"File ricevuto: {file.filename}")
        
        language = request.form.get("language", "eng")
        extracted_text = process_file(file_path, language)
        logging.info(f"Testo estratto: {extracted_text[:100]}")
        
        return jsonify({"extracted_text": extracted_text})
    except Exception as e:
        logging.error(f"Errore: {str(e)}")
        return jsonify({"error": "Errore durante l'elaborazione"}), 500

# API per il download del testo elaborato
@app.route('/download/<filename>/<format>')
def download_file(filename, format):
    text_path = f"outputs/{filename}.{format}"
    extracted_text = process_file(f"uploads/{filename}")
    
    if format == "txt":
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)
    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(190, 10, extracted_text)
        pdf.output(text_path)
    
    return send_file(text_path, as_attachment=True)

# Homepage
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
