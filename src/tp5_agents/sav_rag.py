"""RAG multimodal (texte + images) sur les manuels PDF du SAV."""
import base64
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(override=True)

RACINE = Path(__file__).resolve().parents[2]
MANUELS = RACINE / "sav" / "manuels"
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


if __name__ == "__main__":
    indexer()