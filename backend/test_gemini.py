from google import genai
from app.config import get_settings

settings = get_settings()

print("Gemini key loaded:", bool(settings.gemini_api_key))
print("Key prefix:", settings.gemini_api_key[:8] if settings.gemini_api_key else "EMPTY")

client = genai.Client(api_key=settings.gemini_api_key)

try:
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents="Reply with exactly: GEMINI_OK"
    )

    print("===================================")
    print("GEMINI API WORKS")
    print("===================================")
    print(response.text)

except Exception as e:
    print("===================================")
    print("GEMINI API FAILED")
    print("===================================")
    print(type(e).__name__)
    print(str(e))