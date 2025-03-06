import cv2
import pytesseract
import pandas as pd
import PyMuPDF as fitz  # Correzione del modulo PyMuPDF
import json
import os
from flask import Flask, request, render_template, jsonify

# Configurazione percorso Tesseract (da installare separatamente)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows

app = Flask(__name__)

# Creazione della cartella templates se non esiste
if not os.path.exists("templates"):
    os.makedirs("templates")



def preprocess_image(image_path):
    """Pre-processa l'immagine per migliorare l'OCR"""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_text_from_image(image_path):
    """Estrae il testo da un'immagine con Tesseract OCR"""
    processed_img = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_img, lang='eng')  # Modifica la lingua se necessario
    return text.strip()

def extract_text_from_pdf(pdf_path):
    """Estrae il testo da un PDF"""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

def save_output(text, output_path, output_format="json"):
    """Salva l'output estratto in JSON o CSV"""
    data = {"extracted_text": text}
    
    if output_format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    elif output_format == "csv":
        df = pd.DataFrame([text], columns=["Extracted_Text"])
        df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Output salvato in {output_path}")

def process_file(input_path):
    """Gestisce l'estrazione OCR"""
    ext = os.path.splitext(input_path)[-1].lower()
    
    if ext in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(input_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(input_path)
    else:
        return "Formato non supportato"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nessun file caricato"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nessun file selezionato"})
    
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    
    extracted_text = process_file(file_path)
    
    return jsonify({"extracted_text": extracted_text})

if __name__ == '__main__':
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True)
