"""RAG multimodal (texte + images) sur les manuels PDF du SAV."""
import base64
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(override=True)

RACINE = Path(__file__).resolve().parents[2]
MANUELS = RACINE / "sav" / "manuels"
IMAGES = RACINE / "sav" / "images"
IMAGES_EXTRAITES = RACINE / "sav" / "images_extraites"
CHROMA_DIR = RACINE / "chroma_sav"
COLLECTION = "manuels_sav"

embeddings = OllamaEmbeddings(model="nomic-embed-text")
llm_vision = ChatOllama(model="qwen2.5vl:3b", temperature=0)

CONSIGNE = (
    "Décris précisément cette image tirée d'un manuel d'imprimante, en français : "
    "forme, couleurs, symboles, voyants allumés ou éteints, texte visible. "
    "Sois factuel et concis (3 phrases maximum)."
)

PROMPT_PHOTO = (
    "Sur cette photo d'une imprimante, décris UNIQUEMENT le pictogramme affiché "
    "sur l'écran du panneau : sa forme, ses couleurs et les symboles qu'il contient "
    "(par exemple une feuille, une croix, une goutte, un triangle). "
    "Ne nomme aucun voyant et n'invente rien. Réponds en une ou deux phrases en français."
)

PROMPT_RAG = (
    "Tu es un agent de documentation technique du SAV. "
    "Utilise l'outil chercher_manuel pour trouver les passages et les figures "
    "pertinents (tu peux l'appeler plusieurs fois avec des reformulations). "
    "Réponds en français UNIQUEMENT à partir des extraits trouvés. "
    "La description de la photo du client est générée automatiquement et peut "
    "contenir des erreurs (par exemple sur le nom d'un voyant) : en cas de "
    "contradiction, fie-toi au manuel et ne reprends pas le détail douteux. "
    "Termine toujours par une ligne 'Sources :' listant le manuel, la page et, "
    "pour une figure, le fichier image. "
    "Si la réponse n'est pas dans les manuels, dis-le clairement."
)


def get_store() -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )


def decrire_image(chemin: Path, consigne: str = CONSIGNE) -> str:
    ext = chemin.suffix.lstrip(".").lower().replace("jpg", "jpeg")
    b64 = base64.b64encode(chemin.read_bytes()).decode()
    msg = HumanMessage(
        content=[
            {"type": "text", "text": consigne},
            {"type": "image_url", "image_url": f"data:image/{ext};base64,{b64}"},
        ]
    )
    return llm_vision.invoke([msg]).content.strip()


def indexer() -> None:
    import pymupdf as fitz

    IMAGES_EXTRAITES.mkdir(parents=True, exist_ok=True)
    try:
        get_store().delete_collection()  # repartir d'un index propre
    except Exception:
        pass
    store = get_store()

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    docs: list[Document] = []

    for pdf in sorted(MANUELS.glob("*.pdf")):
        with fitz.open(pdf) as doc:
            for num, page in enumerate(doc, start=1):
                texte = page.get_text().strip()
                titre = texte.splitlines()[0] if texte else ""
                for morceau in splitter.split_text(texte):
                    docs.append(Document(
                        page_content=morceau,
                        metadata={"type": "texte", "source": pdf.name, "page": num},
                    ))
                for i, info in enumerate(page.get_images(full=True), start=1):
                    img = doc.extract_image(info[0])
                    chemin = IMAGES_EXTRAITES / f"{pdf.stem}_p{num}_{i}.{img['ext']}"
                    chemin.write_bytes(img["image"])
                    print(f"Description de {chemin.name} ...", flush=True)
                    description = decrire_image(chemin)
                    print("  ->", description, flush=True)
                    docs.append(Document(
                        page_content=f"[Image, page {num}, section « {titre} »] {description}",
                        metadata={"type": "image", "source": pdf.name, "page": num,
                                  "image_path": str(chemin)},
                    ))

    store.add_documents(docs)
    n_img = sum(1 for d in docs if d.metadata["type"] == "image")
    print(f"Index créé : {len(docs)} éléments ({n_img} images, {len(docs) - n_img} textes)")


def rechercher(question: str, k: int = 4) -> list[Document]:
    return get_store().similarity_search(question, k=k)


@tool
def chercher_manuel(requete: str) -> str:
    """Cherche dans les manuels d'imprimante des passages de texte et des figures.
    Renvoie les extraits avec leur source (manuel, page)."""
    lignes = []
    for d in rechercher(requete, k=6):
        m = d.metadata
        if m["type"] == "image":
            etiquette = f"figure | {m['source']} | page {m['page']} | fichier {Path(m['image_path']).name}"
        else:
            etiquette = f"texte | {m['source']} | page {m['page']}"
        lignes.append(f"[{etiquette}]\n{d.page_content}")
    return "\n\n".join(lignes)


def repondre_multimodal(question: str, image_ref: str | None = None) -> str:
    """Pipeline RAG multimodal : photo -> description -> agent RAG -> réponse sourcée."""
    contexte = question
    if image_ref:
        chemin = next(IMAGES.glob(f"{image_ref}.*"), None)
        if chemin is None:
            contexte += f"\n(La photo '{image_ref}' est introuvable.)"
        else:
            desc = decrire_image(chemin, PROMPT_PHOTO)
            contexte += f"\n\nDescription automatique de la photo jointe ({image_ref}) : {desc}"
    llm = ChatOllama(model="qwen3:4b", temperature=0, reasoning=True)
    agent = create_agent(model=llm, tools=[chercher_manuel],
                         system_prompt=PROMPT_RAG, name="agent_rag")
    res = agent.invoke({"messages": [HumanMessage(contexte)]})
    return res["messages"][-1].content


if __name__ == "__main__":
    indexer()