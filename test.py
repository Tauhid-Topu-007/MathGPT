import streamlit as st

st.sidebar.title("SIDEBAR TEST")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password")
st.write("Main page OK")
st.write("Key:", "✅ set" if groq_api_key else "❌ empty")