import os
import streamlit as st

# Check MiniMax configuration
minimax_key = os.getenv("MINIMAX_API_KEY")
minimax_group = os.getenv("MINIMAX_GROUP_ID")
openai_key = os.getenv("OPENAI_API_KEY")

st.sidebar.subheader("🤖 LLM Configuration")

if minimax_key and minimax_group:
    st.sidebar.success("✅ MiniMax-M3 Configured")
    st.sidebar.caption("Model: abab6.5s-chat")
elif openai_key:
    st.sidebar.success("✅ OpenAI GPT-4 Configured")
else:
    st.sidebar.warning("⚠️ No LLM API configured")
    st.sidebar.info("Full mode will use keyword detection")

print("MiniMax display code ready")
