from groq import Groq
from app.config import get_settings

settings = get_settings()

print("===================================")
print("GROQ DIRECT API TEST")
print("===================================")
print("Key loaded:", bool(settings.groq_api_key))
print("Key prefix:", settings.groq_api_key[:8])
print("Key length:", len(settings.groq_api_key))
print("Model:", settings.groq_model)

client = Groq(api_key=settings.groq_api_key)

try:
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: GROQ_OK"
            }
        ],
        temperature=0
    )

    print("\n===================================")
    print("GROQ API WORKS")
    print("===================================")
    print(response.choices[0].message.content)

except Exception as e:
    print("\n===================================")
    print("GROQ API FAILED")
    print("===================================")
    print(type(e).__name__)
    print(str(e))