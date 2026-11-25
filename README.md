# Agentic AI et MCP : TP5

Agents IA avec LangChain et LangGraph, RAG agentique, serveur MCP et orchestration multi-agents.
LLM local : Ollama (qwen3:4b, qwen3:1.7b) · Embeddings : nomic-embed-text

## Progression
### A. LangChain
- [x] Étape 0 : Initialisation
- [x] Étape 1 : Agent simple + mémoire
- [ ] Étape 2 : Tools personnalisés
- [ ] Étape 3 : Tools prédéfinis (DuckDuckGo, Tavily, PythonREPL)
- [ ] Étape 4 : Middlewares
- [ ] Étape 5 : Chatbot RAG agentique

### B. LangGraph
- [ ] Étape 6 : Bases de LangGraph
- [ ] Étape 7 : Chatbot Agentic RAG
- [ ] Étape 8 : LangGraph Studio
- [ ] Étape 9 : Interface Streamlit

### C. MCP
- [ ] Étape 10 : Serveur MCP (2 tools) + Inspector
- [ ] Étape 11 : Agent LangChain client MCP (streamable-http)
- [ ] Étape 12 : Agent n8n client MCP

### D. Synthèse
- [ ] Étape 13 : SAV multi-agents

## Installation
    uv sync
    ollama pull qwen3:4b
    ollama pull qwen3:1.7b
    ollama pull nomic-embed-text