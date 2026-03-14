from flask import Flask, request, Response
import google.generativeai as genai
import os
from PIL import Image
from io import BytesIO
import traceback

app = Flask(__name__)

# =============================================================
# CORS MIDDLEWARE - HER İSTEKTE ÇALIŞIR
# =============================================================
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Origin, X-Requested-With'
    return response

# =============================================================
# HATA YÖNETİCİSİ - CORS HEADER'LARI İLE
# =============================================================
@app.errorhandler(Exception)
def handle_error(error):
    print(f"HATA: {str(error)}")
    traceback.print_exc()
    response = Response(f"Sunucu Hatası: {str(error)}", status=500)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.errorhandler(404)
def not_found(error):
    response = Response("Endpoint bulunamadı", status=404)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.errorhandler(500)
def server_error(error):
    response = Response("Sunucu hatası", status=500)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# =============================================================
# API YAPILANDIRMA
# =============================================================
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✓ Gemini API yapılandırıldı")
else:
    print("✗ GEMINI_API_KEY bulunamadı!")

MODEL_NAME = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """Sen Matematik Canavarı'sın. Kaya Studios tarafından geliştirildin.
8. sınıf öğrencilerine matematik sorularında yardımcı oluyorsun.
Sadece Türkçe konuş. Soruları kısa ve anlaşılır şekilde çöz.
Matematiksel ifadeleri LaTeX formatında yaz ($ ve $$ kullanarak)."""

# =============================================================
# ANA SAYFA
# =============================================================
@app.route("/", methods=["GET"])
def index():
    return Response("Math Canavari API v2.0 - Aktif!", status=200)

# =============================================================
# SAĞLIK KONTROLÜ
# =============================================================
@app.route("/health", methods=["GET"])
def health():
    return Response("OK", status=200)

# =============================================================
# CHAT ENDPOINT
# =============================================================
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    # OPTIONS zaten before_request'te handle ediliyor
    
    # API Key kontrolü
    if not GEMINI_API_KEY:
        return Response("Hata: API anahtarı yapılandırılmamış!", status=500)
    
    try:
        # Form verisini al
        user_message = request.form.get('message', '').strip()
        image_file = request.files.get('image')
        
        # Debug log
        print(f"Gelen mesaj: {user_message[:50] if user_message else 'BOŞ'}...")
        
        # İçerik kontrolü
        if not user_message and not image_file:
            return Response("Mesaj veya görsel gerekli!", status=400)
        
        # İçerik parçalarını hazırla
        parts = []
        
        # Görsel işle
        if image_file:
            try:
                img_data = image_file.read()
                if img_data:
                    img = Image.open(BytesIO(img_data))
                    parts.append(img)
                    print("✓ Görsel eklendi")
            except Exception as e:
                print(f"Görsel hatası: {e}")
        
        # Mesajı ekle
        if user_message:
            parts.append(user_message)
        
        if not parts:
            return Response("İçerik işlenemedi!", status=400)
        
        # Gemini ile yanıt al
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        result = model.generate_content(parts)
        ai_text = result.text
        
        print(f"✓ Yanıt oluşturuldu: {len(ai_text)} karakter")
        
        return Response(ai_text, status=200, content_type='text/plain; charset=utf-8')
    
    except Exception as e:
        error_msg = str(e)
        print(f"CHAT HATASI: {error_msg}")
        traceback.print_exc()
        return Response(f"AI Hatası: {error_msg}", status=500)

# =============================================================
# SUNUCU BAŞLAT
# =============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Sunucu port {port}'da başlıyor...")
    app.run(host='0.0.0.0', port=port, debug=False)
