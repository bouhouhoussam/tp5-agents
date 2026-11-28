# Agentic AI et MCP : TP5

Agents IA avec LangChain et LangGraph, RAG agentique, serveur MCP et orchestration multi-agents.
LLM local : Ollama (qwen3:4b, qwen3:1.7b) · Embeddings : nomic-embed-text

## Progression
### A. LangChain
- [x] Étape 0 : Initialisation
- [x] Étape 1 : Agent simple + mémoire
- [x] Étape 2 : Tools personnalisés
- [x] Étape 3 : Tools prédéfinis (DuckDuckGo, Tavily, PythonREPL)
- [x] Étape 4 : Middlewares
- [x] Étape 5 : Chatbot RAG agentique

### B. LangGraph
- [x] Étape 6 : Bases de LangGraph
- [x] Étape 7 : Chatbot Agentic RAG
- [x] Étape 8 : LangGraph Studio
- [x] Étape 9 : Interface Streamlit

### C. MCP
- [x] Étape 10 : Serveur MCP (2 tools) + Inspector
- [x] Étape 11 : Agent LangChain client MCP (streamable-http)
- [x] Étape 12 : Agent n8n client MCP

### D. Synthèse
- [ ] Étape 13 : SAV multi-agents
- [x] 13a : agent_garantie + outil local consulter_garantie
- [x] 13b : orchestrateur LangGraph (routage documentation / garantie)
- [x] 13c : RAG multimodal (texte + images du PDF dans ChromaDB)

## Installation
    uv sync
    ollama pull qwen3:4b
    ollama pull qwen3:1.7b
    ollama pull nomic-embed-text
## LangGraph Studio

    uv run langgraph dev

![Graphe](docs/studio_graph.png)
![Chat](docs/studio_chat.png)
## Interface Streamlit

    uv run streamlit run src/tp5_agents/app_streamlit.py

![Streamlit](docs/streamlit.png)
## Étape 10 : serveur MCP et test avec l'Inspector

Serveur FastMCP (`src/tp5_agents/mcp_server.py`) exposé en streamable-http sur `http://localhost:23000/mcp`, avec deux outils : `get_employee_infos` et `web_search` (Tavily).

Lancement :

    uv run python src/tp5_agents/mcp_server.py
    npx @modelcontextprotocol/inspector

![Inspector](docs/inspector.png)
## Étape 11 : agent LangChain client MCP

Agent `create_agent` qui découvre ses outils (`get_employee_infos`, `web_search`) via `MultiServerMCPClient` en `streamable_http` sur `http://localhost:23000/mcp`. Les outils MCP étant asynchrones, l'agent est appelé avec `ainvoke`.
## Étape 12 : agent n8n client MCP

Workflow n8n (Chat Trigger, AI Agent, Ollama Chat Model `qwen3:4b`, MCP Client Tool en HTTP Streamable sur `http://127.0.0.1:23000/mcp`).
Le workflow exporté est dans `docs/n8n_workflow.json`.

![Workflow n8n](docs/n8n_workflow.png)
![Chat n8n](docs/n8n_chat.png)
