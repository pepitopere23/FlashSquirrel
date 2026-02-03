
import os
from google import genai
from dotenv import load_dotenv

# Load environment
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: API Key missing.")
    exit(1)

print("🚦 Injecting test probe to Gemini 2.0 Flash (SDK v1.0+)...")
try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents="Ping. Reply with 'Pong'."
    )
    
    if response and response.text:
        print(f"✅ SUCCESS: API responded: {response.text.strip()}")
    else:
        print("⚠️ WARNING: Empty response received.")

except Exception as e:
    print(f"❌ FAILURE: API Connection failed: {e}")
