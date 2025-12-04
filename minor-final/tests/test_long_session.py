import os
import sys
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hypnoguide.core import ConversationBuffer, LongTermMemory, get_response

def test_long_session():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Skipping AI test: No API Key found.")
        return

    print("Testing Long Session Generation...")
    buffer = ConversationBuffer()
    memory = LongTermMemory()
    
    # Simulate user asking for a full session
    user_msg = "I am ready for a full relaxation session. Please guide me through it."
    response = get_response(user_msg, buffer, memory, api_key)
    
    print("Response received:")
    reply = response.get("reply", "")
    print(f"Length of reply: {len(reply)} chars")
    print(reply[:500] + "...") # Print first 500 chars
    
    if len(reply) > 500:
        print("SUCCESS: Generated a long script.")
    else:
        print("WARNING: Script might be too short.")

if __name__ == "__main__":
    test_long_session()
