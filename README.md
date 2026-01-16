# turkish-pdf-rag-assistant
# RAG-based Turkish PDF Assistant (Demo)

A lightweight Streamlit demo that enables **question answering over Turkish academic PDFs** using a **Retrieval-Augmented Generation (RAG)** pipeline.

- **Code + documentation:** English  
- **User interface + example questions:** Turkish (better UX for Turkish PDFs)  
- The assistant is instructed to answer **only using the provided PDFs**. If the answer is not present, it replies with:  
  **`PDF’lerde bu bilgi bulunamadı.`**

## Features
- Drop-in usage: place PDFs under `data/` (no upload needed)
- One-click indexing to a vector store
- Simple Q&A chat interface
- Basic hallucination control via strict system rules

## Project Structure
```
.
├─ app.py # Streamlit UI + RAG pipeline
├─ requirements.txt # Python dependencies
├─ .env # API key (not committed)
├─ data/ # Put your PDFs here (PDFs not committed)
└─ app_state.json # Local state (vector store id, etc.; not committed)
``` 
> Add your own PDFs under `data/` to test the app.

---

## Requirements
- Python 3.10+ recommended
- An OpenAI API key

---

## Installation

1) Create a virtual environment (recommended)
```
python -m venv .venv
```
2) Install dependencies
```
pip install -r requirements.txt
```
3) Add your API key
Create a .env file in the project root:
```
OPENAI_API_KEY=sk-...
```
4) Run
```
streamlit run app.py
```
If PowerShell blocks venv activation, you can run Streamlit via the venv python directly:
```
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## How to Use
1. Put **text-selectable** (non-scanned) PDFs into the `data/` folder.
2. Open the app and click **“PDF’leri indeksle”** once.
3. Ask a question in Turkish (or pick a quick question from the sidebar).

## Example Questions (Turkish)
- “Bu makalenin temel katkısı nedir? 5 maddede özetle.”
- “Önerilen yöntemi adım adım açıkla. Varsayımlar neler?”
- “Deneylerde hangi veri setleri/metrikler kullanılmış? Sonuçları özetle.”
- “Kısıtlar (limitations) ve gelecek çalışmalar kısmı ne diyor?”

## Notes / Limitations
- Scanned (image-only) PDFs may not work well without **OCR**.
- If you replace your PDFs and want a clean re-index, delete `app_state.json` and index again.
- This is a demo project: no formal benchmarking or evaluation metrics are included.
