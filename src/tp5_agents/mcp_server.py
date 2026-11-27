from mcp.server.fastmcp import FastMCP
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv(override=True)

mcp = FastMCP(name="mcp-server", host="127.0.0.1", port=23000)
web_search_client = TavilySearch(max_results=3)


@mcp.tool()
def get_employee_infos(name: str):
    """Get information about a given employee"""
    return {"name": name, "salary": 21000, "seniority": 12}


@mcp.tool()
def web_search(query: str):
    """Search the web for the given query"""
    return web_search_client.invoke({"query": query})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")