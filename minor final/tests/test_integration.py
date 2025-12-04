import os
import sys
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hypnoguide.core import ConversationBuffer, LongTermMemory, get_response
from gtts import gTTS
import io

def test_integration():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Skipping AI test: No API Key found.")
        return

    print("Testing AI Response...")
    buffer = ConversationBuffer()
    memory = LongTermMemory()
    
    # Test a simple greeting
    user_msg = "Hello, I am interested in hypnotherapy."
    response = get_response(user_msg, buffer, memory, api_key)
    
    print("Response received:")
    print(json.dumps(response, indent=2))
    
    if "reply" in response:
        print("\nTesting TTS generation...")
        try:
            tts = gTTS(text=response["reply"], lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            print(f"TTS generated {audio_fp.getbuffer().nbytes} bytes of audio.")
        except Exception as e:
            print(f"TTS Failed: {e}")
    else:
        print("No reply found in response.")

if __name__ == "__main__":
    test_integration()
