import uuid
import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from tp5_agents.rag_graph import workflow

st.set_page_config(page_title="Chatbot RAG - Cours Agentic AI", page_icon="🤖")
st.title("🤖 Chatbot RAG agentique")
st.caption("LangGraph · ChromaDB · Ollama (qwen3:4b)")


@st.cache_resource
def get_graph():
    # On recompile le graphe avec une mémoire (Studio gérait la sienne)
    return workflow.compile(checkpointer=InMemorySaver())


graph = get_graph()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.history = []

with st.sidebar:
    st.header("Options")
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.history = []
        st.rerun()

for role, content in st.session_state.history:
    with st.chat_message(role):
        st.markdown(content)

if question := st.chat_input("Posez une question sur le cours..."):
    st.session_state.history.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans le cours..."):
            res = graph.invoke({"messages": [HumanMessage(question)]}, config=config)

        messages = res["messages"]
        dernier_humain = max(i for i, m in enumerate(messages) if m.type == "human")
        outils = [tc["name"] for m in messages[dernier_humain:]
                  for tc in (getattr(m, "tool_calls", None) or [])]

        reponse = messages[-1].content
        st.markdown(reponse)
        if outils:
            st.caption("🔧 Outil utilisé : " + ", ".join(outils))

    st.session_state.history.append(("assistant", reponse))