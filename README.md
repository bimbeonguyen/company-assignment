# OptiBot Mini-Clone Sync Job

An automated, delta-only scraper and sync pipeline that retrieves support articles from Zendesk (`support.optisigns.com`) and updates an OpenAI Vector Store.

---

## Features
- **Scraper**: Paginates through Zendesk Help Center API until all public articles are indexed.
- **HTML-to-Markdown**: Converts article body markup using `markdownify` and expands relative URLs to absolute links.
- **Delta Sync**: Lists existing files in the OpenAI Vector Store, parses filenames (`optibot_<article_id>_<unix_timestamp>.md`), compares updates, and only uploads new/updated files while deleting stale ones.

---

## Chunking Strategy

This project leverages OpenAI's native **`"auto"` chunking strategy** inside the Vector Store File Search tool. 

By uploading clean Markdown documents, OpenAI automatically parses and splits the files. It leverages Markdown structural syntax (e.g., headings, list tags, and paragraph breaks) to keep related instructions together, preventing code blocks or step-by-step instructions from being fragmented across separate chunks.

---

## Setup & Local Running

1. **Install Python dependencies**:
   ```bash
   cd packages/scrapebot/app
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Create a `.env` file at the root (use `.env.sample` as a template):
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_VECTOR_STORE_ID=your_openai_vector_store_id
   ```

3. **Run local tests**:
   ```bash
   $env:PYTHONPATH="packages/scrapebot/app"; python -m pytest
   ```

4. **Execute the sync script**:
   ```bash
   python packages/scrapebot/app/__main__.py
   ```

---

## Docker Running

Build and run the container locally:
```bash
docker build -t bot-sync .
docker run -e OPENAI_API_KEY="your_api_key" -e OPENAI_VECTOR_STORE_ID="your_vs_id" bot-sync
```

---

## Bot logs URL: https://stream-logs.vercel.app/

## Playground Sanity Check Screenshot

*("How do I add a YouTube video?")*

![Playground Answer Screenshot](playground_verification.png)
