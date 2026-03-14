from flask import Flask, request, make_response
from flask_cors import CORS
import google.generativeai as genai
import os
from PIL import Image 
from io import BytesIO

app = Flask(__name__)
# Tüm originlere izin ver
CORS(app, resources={r"/*": {"origins": "*"}})

# API Key Kontrolü
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash" 

SYSTEM_INSTRUCTION = (
    "Sen Matematik Canavarı 1.0'sın. Kaya Studios tarafından geliştirildin. "
    "8. sınıf öğrencilerine matematik sorularında yardımcı oluyorsun. "
    "KESİNLİKLE sadece Türkçe konuşmalısın. "
    "Soruları kısa, öz ve anlaşılır bir şekilde çöz."
)

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    # 1. TARAYICININ ÖN KONTROLÜ (PREFLIGHT) İÇİN ZORUNLU YANIT
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    # 2. ASIL İŞLEM (POST)
    if not GEMINI_API_KEY:
        res = make_response("Hata: GEMINI_API_KEY bulunamadı!", 500)
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res

    user_message = request.form.get('message', '')
    image_file = request.files.get('image')

    try:
        parts = []
        if image_file:
            img_data = image_file.read()
            if img_data:
                img = Image.open(BytesIO(img_data))
                parts.append(img)
        
        if user_message:
            parts.append(user_message)

        if not parts:
            res = make_response("İçerik boş!", 400)
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res

        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        ai_response = model.generate_content(parts)
        
        # Başarılı yanıt
        res = make_response(ai_response.text, 200)
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res

    except Exception as e:
        print(f"KRİTİK HATA: {str(e)}")
        res = make_response(f"Sunucu Hatası: {str(e)}", 500)
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
