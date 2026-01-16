import os
import json
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# configuration & initialization
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("OPENAI_API_KEY bulunamadı. Proje köküne .env koyup OPENAI_API_KEY=sk-... şeklinde ekleyin.")
    st.stop()

client = OpenAI(api_key=API_KEY)

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
STATE_PATH = ROOT / "app_state.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# utility functions
def load_state() -> dict:
    """Load minimal app state (vector store id, indexed files, last index time)."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"vector_store_id": None, "indexed_files": [], "last_index_time": None}


def save_state(state: dict) -> None:
    """Persist state to disk (kept out of git)."""
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def list_local_pdfs() -> list[Path]:
    """List all PDFs under data/."""
    return sorted([p for p in DATA_DIR.glob("*.pdf") if p.is_file()])


def ensure_vector_store(state: dict) -> str:
    """Create (once) or reuse a vector store to back File Search."""
    if state.get("vector_store_id"):
        return state["vector_store_id"]

    vs = client.vector_stores.create(name="tr_pdf_rag_demo")
    state["vector_store_id"] = vs.id
    save_state(state)
    return vs.id


def index_pdfs(vector_store_id: str, pdf_paths: list[Path]) -> str:
    """Upload PDFs and wait until indexing completes."""
    if not pdf_paths:
        return "no_pdfs"

    streams = []
    try:
        for p in pdf_paths:
            streams.append(open(p, "rb"))

        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=streams,
        )
        return str(getattr(batch, "status", "ok"))
    finally:
        for s in streams:
            try:
                s.close()
            except Exception:
                pass


def _sanitize_output(text: str) -> str:
    """Remove internal-looking citation artifacts from the model output (demo polish)."""
    if not text:
        return ""
    for bad in ["", "filecite", "turn0file", "turn1file", "turn2file"]:
        text = text.replace(bad, "")
    return text.strip()


def ask(vector_store_id: str, question: str, model: str) -> str:
    """Run a RAG-style Q&A: retrieve from PDFs, then answer grounded in retrieved text."""
    system_prompt = (
        "You are a Turkish academic PDF reading assistant.\n"
        "Answer ONLY using information retrieved from the provided PDF knowledge base.\n"
        "If the answer is not present in the PDFs, say exactly: 'PDF’lerde bu bilgi bulunamadı.'\n"
        "Keep answers short, clear, and preferably bullet-pointed.\n"
        "Never output internal citation tokens like 'filecite', 'turn0file', or weird symbols.\n"
        "If you mention sources, use plain text only (e.g., 'Kaynak: paper1.pdf').\n"
        "\n"
        "IMPORTANT: Respond in Turkish.\n"
    )

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id],
        }],
        # max_output_tokens=700,
    )
    return _sanitize_output(resp.output_text)


# streamlit UI (Turkish)
st.set_page_config(page_title="Türkçe PDF RAG Demo", layout="wide")
st.title("RAG Tabanlı Türkçe PDF Asistan — Demo")

state = load_state()
vs_id = ensure_vector_store(state)
pdfs = list_local_pdfs()

already_indexed = (
    len(pdfs) > 0
    and set(state.get("indexed_files", [])) == set([p.name for p in pdfs])
)

with st.sidebar:
    st.header("Veri ve İndeks")
    st.caption(f"Vector Store ID: {vs_id}")

    if not pdfs:
        st.warning("data/ klasöründe PDF bulunamadı. PDF’leri data/ içine ekleyin.")
    else:
        st.write("Bulunan PDF’ler:")
        for p in pdfs:
            st.write("•", p.name)

    st.divider()
    st.subheader("Adım 1 — PDF’leri İndeksle")

    if already_indexed:
        st.success("Bu PDF’ler zaten indekslenmiş")

    if st.button("PDF’leri indeksle", type="primary", disabled=(len(pdfs) == 0 or already_indexed)):
        with st.spinner("Yükleniyor ve indeksleniyor..."):
            try:
                status = index_pdfs(vs_id, pdfs)
                state["indexed_files"] = [p.name for p in pdfs]
                state["last_index_time"] = int(time.time())
                save_state(state)
                st.success(f"İndeks tamamlandı. Durum: {status}")
            except Exception as e:
                st.error(f"İndeks hatası: {e}")

    if state.get("last_index_time"):
        st.caption("Son indeks: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state["last_index_time"])))

    st.divider()
    st.subheader("Adım 2 — Model")
    model = st.selectbox("Model seç", ["gpt-5-mini", "gpt-5"], index=0)

    st.divider()
    st.subheader("Adım 3 — Hazır Sorular")
    quick = st.selectbox(
        "Bir soru seç (isteğe bağlı):",
        [
            "",
            "Bu makalenin temel katkısı nedir? 5 maddede özetle.",
            "Önerilen yöntemi adım adım açıkla. Varsayımlar neler?",
            "Deneylerde hangi veri setleri/metrikler kullanılmış? Sonuçları özetle.",
            "Kısıtlar (limitations) ve gelecek çalışmalar kısmı ne diyor?",
        ],
        index=0,
    )

    if st.button("Sohbeti temizle"):
        st.session_state.chat = []


left, right = st.columns([2, 1])

with left:
    st.subheader("Soru-Cevap")

    if state.get("indexed_files"):
        st.info("İndeks hazır: " + ", ".join(state["indexed_files"]))
    else:
        st.warning("Henüz indeks yapılmadı. Sol panelden PDF’leri indeksleyin.")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    question = st.text_area(
        "Sorun",
        value=quick if quick else "",
        height=120,
        placeholder="Örn: Yöntemi 5 maddede açıkla.",
    )

    if st.button("Cevapla"):
        if not question.strip():
            st.warning("Lütfen bir soru yazın.")
        else:
            st.session_state.chat.append(("Sen", question.strip()))
            with st.spinner("Yanıt hazırlanıyor..."):
                try:
                    answer = ask(vs_id, question.strip(), model=model)
                except Exception as e:
                    answer = f"Hata: {e}"
            st.session_state.chat.append(("Asistan", answer))

    for role, msg in st.session_state.chat[::-1]:
        st.markdown(f"**{role}:** {msg}")
        st.markdown("---")

