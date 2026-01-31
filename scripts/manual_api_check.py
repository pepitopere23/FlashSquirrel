
import os
import asyncio
import logging
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)

async def test_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ No API Key found")
        return

    print(f"🔑 Testing API Key: {api_key[:5]}...")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello, are you online?"
        )
        print(f"✅ Gemini Response: {response.text}")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_gemini())
