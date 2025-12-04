import streamlit as st
import os
from dotenv import load_dotenv
from hypnoguide.core import ConversationBuffer, LongTermMemory, get_response
from gtts import gTTS
import io

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="HypnoGuide",
    page_icon="🌀",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #f0f2f6;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #e8f4f8;
    }
</style>
""", unsafe_allow_html=True)

# Title and Intro
st.title("🌀 HypnoGuide")
st.markdown("Your gentle, safe hypnotherapy fundamentals tutor.")

# Initialize Session State
if "buffer" not in st.session_state:
    st.session_state.buffer = ConversationBuffer()

if "memory" not in st.session_state:
    st.session_state.memory = LongTermMemory()

if "messages" not in st.session_state:
    st.session_state.messages = []

# API Key Check
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    st.error("OPENROUTER_API_KEY not found. Please set it in your .env file or Streamlit secrets.")
    st.stop()

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add to buffer
    st.session_state.buffer.add_turn("user", prompt)

    # Get Response
    with st.spinner("Thinking..."):
        response_data = get_response(
            user_message=prompt,
            buffer=st.session_state.buffer,
            memory=st.session_state.memory,
            api_key=api_key
        )

    # Process Response
    reply_text = response_data.get("reply", "I'm sorry, I encountered an error.")
    actions = response_data.get("actions", [])
    memory_update = response_data.get("memory_update", {})

    # Update Memory if needed
    if memory_update.get("type") == "longterm":
        content = memory_update.get("content")
        # Content might be a JSON string or a dict depending on how the LLM formatted it inside the JSON structure.
        # The prompt asks for "content": "..." which implies string, but if it's a dict structure for preferences, we need to handle it.
        # Let's assume the LLM might send a JSON string or a direct object.
        if isinstance(content, str):
            try:
                content_dict = json.loads(content)
                st.session_state.memory.update_from_dict(content_dict)
            except:
                pass # Or log error
        elif isinstance(content, dict):
             st.session_state.memory.update_from_dict(content)
    
    elif memory_update.get("type") == "buffer":
        # Buffer is auto-updated with full text, but if the LLM wants to summarize explicitly, we could use this.
        # For now, we stick to the simple buffer logic of storing turns.
        pass

    # Add assistant message to UI
    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)
        
        # Generate and play audio
        try:
            # Pre-process text for gTTS (replace (pause) with punctuation for breaks)
            tts_text = reply_text.replace("(pause)", "...")
            
            # Standard speed (removed slow=True)
            tts = gTTS(text=tts_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp, format='audio/mp3')
        except Exception as e:
            st.error(f"TTS Error: {e}")
    
    # Add to buffer
    st.session_state.buffer.add_turn("assistant", reply_text)

    # Handle Actions (Optional UI enhancements)
    if actions:
        # We could add buttons or expanders here based on actions
        pass

# Sidebar for Debug/Preferences
with st.sidebar:
    st.header("Session Info")
    if st.checkbox("Show Memory Debug"):
        st.subheader("Long-Term Memory")
        st.json(st.session_state.memory.get_summary())
        st.subheader("Conversation Buffer")
        st.json(st.session_state.buffer.get_summary())
