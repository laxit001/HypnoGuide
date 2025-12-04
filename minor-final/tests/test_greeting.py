import os
import sys
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hypnoguide.core import ConversationBuffer, LongTermMemory, get_response

def test_greeting_logic():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Skipping AI test: No API Key found.")
        return

    print("Testing Greeting Logic...")
    buffer = ConversationBuffer()
    memory = LongTermMemory()
    
    # Test 1: Simple Greeting
    print("\n--- Test 1: 'Hi' ---")
    user_msg = "Hi"
    response = get_response(user_msg, buffer, memory, api_key)
    reply = response.get("reply", "")
    print(f"Reply: {reply[:100]}...")
    
    if len(reply) > 500:
        print("FAIL: 'Hi' triggered a long session.")
    else:
        print("PASS: 'Hi' triggered a short response.")

    # Test 2: Explicit Session Request
    print("\n--- Test 2: 'I want to relax' ---")
    user_msg = "I want to relax"
    response = get_response(user_msg, buffer, memory, api_key)
    reply = response.get("reply", "")
    print(f"Reply length: {len(reply)}")
    
    if len(reply) > 500:
        print("PASS: 'I want to relax' triggered a long session.")
    else:
        print("FAIL: 'I want to relax' triggered a short response.")

if __name__ == "__main__":
    test_greeting_logic()
