from mcp.server.fastmcp import FastMCP

from tp5_agents.sav_rag import repondre_multimodal

mcp = FastMCP(name="mcp-sav", host="127.0.0.1", port=23001)


@mcp.tool()
def rag_multimodal(question: str, image_ref: str = "") -> str:
    """Répond à une question technique sur une imprimante à partir des manuels PDF
    (passages de texte et figures). Si le client a joint une photo, passe sa
    référence dans image_ref (ex: img_px200_01). Renvoie une réponse avec ses sources."""
    return repondre_multimodal(question, image_ref or None)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")