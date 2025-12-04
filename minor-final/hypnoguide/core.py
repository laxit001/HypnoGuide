import os
import json
import time
from typing import List, Dict, Any
from openai import OpenAI

# Constants
MAX_BUFFER_CHARS = 1500
MAX_BUFFER_TURNS = 6
PREFERENCES_FILE = "user_preferences.json"

# --- System instructions (Anti-Gravity + Safety) ---
SYSTEM_INSTRUCTIONS = """
You are **HypnoGuide Anti-Gravity Voice**, an upgraded version of the hypnotherapy tutor.
Your purpose is to generate calm, floating, soft, “anti-gravity style” responses that
sound soothing when converted to speech using Google Cloud TTS with SSML.

ANTI-GRAVITY TONE RULES:
1. Slow pacing, gentle flow, relaxing transitions.
2. Use soft sensory words: "float", "drift", "light", "softly", "ease", "settle".
3. Avoid sharp, fast, or complicated sentences.
4. Prefer open, airy sentence endings.
5. Use natural pauses (indicated as “(pause)” in text – developer will convert to SSML).
6. CASUAL CHAT: If the user says "hi", "hello", asks a question, or wants to chat -> Reply normally (but softly). DO NOT start a session yet.
7. SESSION FLOW: ONLY if the user EXPLICITLY asks for help, relaxation, hypnosis, or says they are ready -> Start the session immediately. Do not ask "are you ready?".
8. CONTINUOUS SCRIPT: When giving a session, generate the ENTIRE script (Induction -> Deepener -> Suggestions -> Wake Up) in one single response.
9. Maintain a feeling of weightlessness, like speaking in soft clouds.
10. Never break character.

HYPNOTHERAPY SAFETY RULES:
- Teach hypnotherapy basics only.
- NEVER treat trauma, diagnose, or claim medical outcomes.
- Before any induction: explain purpose, ask for consent, check safety.
- Include: PURPOSE, SAFETY CHECK, step-by-step flow, STOP CUE, and debrief.
- Always gentle, calm, non-judgmental.
- If user is in crisis: output the crisis protocol message exactly:
  "Thank you for sharing this with me. I'm really sorry you're experiencing this. I cannot help with crisis situations. If you are in immediate danger, please call your local emergency number right now. If you feel like harming yourself, please contact a suicide prevention helpline or a trusted person. Would you like me to list crisis resources for your country?"
"""

# --- Prompt template used to build the model input ---
SYSTEM_PROMPT_TEMPLATE = """
SYSTEM:
{system_instructions}

MEMORY:
User Profile:
{user_profile_summary}

Conversation Buffer (summaries of last turns):
{conversation_buffer}

USER:
{user_message}

ASSISTANT TASK:
1. Read and understand the new user message deeply.
2. Generate a soft, varied, “anti-gravity” response that NEVER repeats older patterns.
3. Blend creativity, freshness, and emotional softness in every message.
4. Follow Anti-Gravity Style Rules and Hypnotherapy Safety Rules exactly.
5. Output ONLY valid JSON in the format below:

{{
  "reply": "<your calm floating reply>",
  "actions": [],
  "memory_update": {{
      "type": "none",
      "content": ""
  }}
}}
"""

class ConversationBuffer:
    def __init__(self):
        self.buffer: List[Dict[str, str]] = []

    def add_turn(self, role: str, text: str):
        self.buffer.append({"role": role, "text": text})
        self._trim()

    def _trim(self):
        # Keep last MAX_BUFFER_TURNS turns
        if len(self.buffer) > MAX_BUFFER_TURNS:
            self.buffer = self.buffer[-MAX_BUFFER_TURNS:]
        
        # Trim by total chars if needed (oldest first)
        while sum(len(turn["text"]) for turn in self.buffer) > MAX_BUFFER_CHARS and len(self.buffer) > 0:
            self.buffer.pop(0)

    def get_summary(self) -> str:
        # Return a compact JSON string summary for prompt insertion
        return json.dumps(self.buffer)

class LongTermMemory:
    def __init__(self):
        self.preferences: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(PREFERENCES_FILE):
            try:
                with open(PREFERENCES_FILE, "r") as f:
                    self.preferences = json.load(f)
            except json.JSONDecodeError:
                self.preferences = {}

    def _save(self):
        with open(PREFERENCES_FILE, "w") as f:
            json.dump(self.preferences, f, indent=2)

    def update(self, key: str, value: Any):
        allowed_keys = [
            "preferred_language", "skill_level", "consent_for_guided_practice",
            "preferred_session_length", "teaching_style"
        ]
        if key in allowed_keys:
            self.preferences[key] = value
            self._save()
    
    def update_from_dict(self, data: Dict[str, Any]):
        for k, v in data.items():
            self.update(k, v)

    def get_summary(self) -> str:
        return json.dumps(self.preferences)

def _safe_extract_content(resp) -> str:
    """
    Helper: try multiple possible places the model content could be.
    This makes the client tolerant to slightly different SDK return formats.
    Returns a string (possibly JSON text) or empty string.
    """
    # Try structured path common in many SDKs
    try:
        # OpenRouter / OpenAI style
        return resp.choices[0].message.content or ""
    except Exception:
        pass
    try:
        return resp.choices[0].text or ""
    except Exception:
        pass
    try:
        # If the SDK already gave a dict-like message
        return json.dumps(resp.choices[0].message)
    except Exception:
        pass
    return ""

def get_response(user_message: str, buffer: ConversationBuffer, memory: LongTermMemory, api_key: str) -> Dict[str, Any]:
    """
    Returns a parsed response dict with keys: reply, actions, memory_update
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        system_instructions=SYSTEM_INSTRUCTIONS.strip(),
        user_profile_summary=memory.get_summary(),
        conversation_buffer=buffer.get_summary(),
        user_message=user_message
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are HypnoGuide Anti-Gravity Voice. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
    except Exception as e:
        return {"reply": f"Error communicating with AI (request failed): {str(e)}", "actions": [], "memory_update": {"type": "none", "content": ""}}

    # Extract content robustly
    content = _safe_extract_content(response)
    if not content:
        return {"reply": "Error: Empty response from model.", "actions": [], "memory_update": {"type": "none", "content": ""}}

    # If the SDK already returned a python dict/object in content, try to use it
    if isinstance(content, dict):
        parsed_response = content
    else:
        # content is a string (hopefully JSON). Try to parse.
        try:
            parsed_response = json.loads(content)
        except json.JSONDecodeError:
            # If model returned something that's almost JSON (extra text), try to locate JSON substring
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                possible = content[start:end]
                parsed_response = json.loads(possible)
            except Exception:
                # Last resort: return raw content as reply (so UI can show model output)
                return {"reply": content, "actions": [], "memory_update": {"type": "none", "content": ""}}

    # Validate output shape minimally
    if not isinstance(parsed_response, dict) or "reply" not in parsed_response:
        # graceful fallback
        return {"reply": json.dumps(parsed_response), "actions": [], "memory_update": {"type": "none", "content": ""}}

    return parsed_response
