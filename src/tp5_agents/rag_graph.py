from pathlib import Path
from typing import Annotated, List
from typing_extensions import TypedDict

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.tools import tool
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Base ChromaDB créée à l'étape 5 (à la racine du projet)
CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"

llm = ChatOllama(model="qwen3:4b", temperature=0, reasoning=True)
embeddings = OllamaEmbeddings(model="nomic-embed-text")

vectorstore = Chroma(
    collection_name="cours_agentic",
    embedding_function=embeddings,
    persist_directory=str(CHROMA_DIR),
)


@tool
def rechercher_cours(question: str) -> str:
    """Recherche dans le support de cours (Agentic AI, LangChain, LangGraph, MCP)
    et renvoie les passages pertinents avec leur numéro de page."""
    docs = vectorstore.similarity_search(question, k=6)
    return "\n\n".join(
        f"[page {d.metadata.get('page', 0) + 1}] {d.page_content}" for d in docs
    )


tools = [rechercher_cours]
llm_with_tools = llm.bind_tools(tools)

SYSTEM = (
    "Tu es un assistant pédagogique. Pour toute question sur le cours "
    "(Agentic AI, LangChain, LangGraph, MCP), utilise l'outil rechercher_cours "
    "et réponds UNIQUEMENT à partir des passages trouvés, en citant les pages. "
    "Si l'information n'est pas dans le cours, dis-le clairement. "
    "Pour une simple salutation, réponds sans chercher. Réponds en français."
)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


def assistant(state: AgentState) -> AgentState:
    response = llm_with_tools.invoke([SystemMessage(SYSTEM)] + state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState):
    return "continue" if state["messages"][-1].tool_calls else "end"


workflow = StateGraph(AgentState)
workflow.add_node("assistant", assistant)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "assistant")
workflow.add_conditional_edges("assistant", should_continue, {"continue": "tools", "end": END})
workflow.add_edge("tools", "assistant")

# Pas de checkpointer ici : LangGraph Studio gère lui-même la persistance
graph = workflow.compile()