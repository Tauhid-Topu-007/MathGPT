import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.callbacks import StreamlitCallbackHandler
import time

# ------------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------------
st.set_page_config(
    page_title="MathMind AI",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# SIDEBAR — API KEY IS THE FIRST INPUT
# ------------------------------------------------------------------
with st.sidebar:
    st.title("🧮 MathMind AI")
    st.caption("Premium Math & Reasoning Assistant")
    st.markdown("---")

    groq_api_key = st.text_input(
        "🔑 Enter your Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get a free key at https://console.groq.com/keys",
    )

    st.markdown("---")
    st.subheader("⚙️ Settings")
    model_choice = st.selectbox(
        "Model",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
    )
    temperature = st.slider("Creativity", 0.0, 1.0, 0.2, 0.05)
    verbose_mode = st.toggle("Show agent thoughts", value=False)

    st.markdown("---")
    st.subheader("🧰 Tools")
    st.write("🧠 Reasoning")

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm MathMind — ask me any math, logic, or data question."}
        ]
        st.rerun()

# ------------------------------------------------------------------
# HERO
# ------------------------------------------------------------------
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 15% 10%, #1a1f3a 0%, #0b0e1a 45%, #06080f 100%); color: #e7ecff; }
.hero {
    background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(168,85,247,0.12));
    border: 1px solid rgba(139,148,255,0.25); border-radius: 24px;
    padding: 2rem 2.4rem; margin-bottom: 1.4rem;
}
.hero h1 {
    font-size: 2.4rem; font-weight: 800;
    background: linear-gradient(90deg, #ffffff, #c7d2fe, #a5b4fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
}
.hero p { color: #a5b4fc; margin-top: 0.6rem; }
</style>
<div class="hero">
    <h1>🧮 Text → Math Problem Solver</h1>
    <p>Enter your <b>Groq API key</b> in the sidebar, then type your math question below.</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm MathMind — ask me any math, logic, or data question."}
    ]

# ------------------------------------------------------------------
# INPUT AREA — ALWAYS VISIBLE
# ------------------------------------------------------------------
st.markdown("### ✍️ Ask your question")

default_q = (
    "I have 5 bananas and 7 grapes. I eat 2 bananas and give away 3 grapes. "
    "Then I buy a dozen apples and 2 packs of blueberries. Each pack has 25 berries. "
    "How many total pieces of fruit do I have at the end?"
)
question = st.text_area(
    "Question",
    value=default_q,
    height=130,
    label_visibility="collapsed",
    placeholder="Type your math, logic, or research question…",
)

col1, col2 = st.columns([3, 1])
with col1:
    solve = st.button("🚀 Solve My Problem", use_container_width=True)
with col2:
    st.caption(f"Model: **{model_choice}**")

# ------------------------------------------------------------------
# CHAT HISTORY
# ------------------------------------------------------------------
st.markdown("---")
st.markdown("### 💬 Conversation")
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🧮"
    st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

# ------------------------------------------------------------------
# BUILD AGENT (only when needed)
# ------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def build_agent(api_key: str, model: str, temp: float, verbose: bool):
    llm = ChatGroq(model=model, groq_api_key=api_key, temperature=temp)

    prompt = PromptTemplate(
        input_variables=["question"],
        template="""
You are an expert math and logic tutor. Solve the user's question by reasoning step-by-step.
Present the final answer clearly with a bullet-point explanation.

Question: {question}
Answer:
""",
    )
    reasoning_chain = LLMChain(llm=llm, prompt=prompt)
    reasoning_tool = Tool(
        name="Reasoning tool",
        func=reasoning_chain.run,
        description="Answer math, logic, and reasoning questions step-by-step.",
    )

    return initialize_agent(
        tools=[reasoning_tool],
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=3,
    )

# ------------------------------------------------------------------
# HANDLE SUBMIT
# ------------------------------------------------------------------
if solve:
    if not groq_api_key:
        st.warning("🔐 Please enter your **Groq API key** in the sidebar first.")
    elif not question.strip():
        st.warning("⚠️ Please enter a question first.")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user", avatar="🧑‍💻").write(question)

        with st.chat_message("assistant", avatar="🧮"):
            status = st.status("🧠 Thinking…", expanded=True)
            st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
            try:
                assistant_agent = build_agent(groq_api_key, model_choice, temperature, verbose_mode)
                t0 = time.time()
                response = assistant_agent.run(question, callbacks=[st_cb])
                status.update(label=f"✅ Solved in {time.time()-t0:.1f}s", state="complete", expanded=False)
                st.success(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                status.update(label="❌ Error", state="error")
                st.error(f"Something went wrong: {e}")