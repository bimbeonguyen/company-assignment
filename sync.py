import re
import os
import logging
from datetime import datetime
from openai import OpenAI
from transformer import convert_to_markdown

logger = logging.getLogger(__name__)
FILENAME_REGEX = re.compile(r"^optibot_(\d+)_(\d+)\.md$")

def iso_to_timestamp(iso_str: str) -> int:
    """
    Converts ISO 8601 UTC string (e.g., '2026-06-08T12:00:00Z') to integer Unix timestamp.
    """
    if not iso_str:
        return 0
    clean_str = iso_str.replace("Z", "+00:00")
    return int(datetime.fromisoformat(clean_str).timestamp())

def parse_remote_filename(filename: str):
    """
    Parses remote filename and returns (article_id, timestamp) or (None, None) if format doesn't match.
    """
    match = FILENAME_REGEX.match(filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def calculate_deltas(remote_files, active_articles):
    """
    Compares remote files in OpenAI with active articles from Zendesk.
    Returns delta categorization dict: {"add": [], "update": [], "delete": [], "skip": []}
    """
    deltas = {
        "add": [],
        "update": [],
        "delete": [],
        "skip": []
    }

    # Map remote files by article ID: {article_id: {"id": file_id, "filename": filename, "timestamp": timestamp}}
    remote_map = {}
    for f in remote_files:
        article_id, timestamp = parse_remote_filename(f["filename"])
        if article_id is not None:
            remote_map[article_id] = {
                "id": f["id"],
                "filename": f["filename"],
                "timestamp": timestamp
            }

    # Keep track of which remote files are active (meaning we matched them to active articles)
    matched_remote_ids = set()

    for article in active_articles:
        art_id = article["id"]
        art_ts = iso_to_timestamp(article["updated_at"])

        if art_id not in remote_map:
            # New article
            deltas["add"].append(article)
        else:
            remote = remote_map[art_id]
            matched_remote_ids.add(art_id)
            if art_ts > remote["timestamp"]:
                # Updated article: needs old file deleted and new file uploaded
                deltas["update"].append((article, remote["id"], remote["filename"]))
            else:
                # Unchanged
                deltas["skip"].append(article)

    # Any remote file belonging to our naming scheme that was NOT matched is stale (deleted in Zendesk)
    for art_id, remote in remote_map.items():
        if art_id not in matched_remote_ids:
            deltas["delete"].append({"id": remote["id"], "filename": remote["filename"]})

    return deltas

def get_vector_stores_client(client: OpenAI):
    """
    Returns the vector_stores client. In newer OpenAI SDK versions, vector_stores is
    at client.vector_stores. In older versions, it's at client.beta.vector_stores.
    """
    if hasattr(client, "vector_stores"):
        return client.vector_stores
    return client.beta.vector_stores
def get_vector_store_files(client: OpenAI, vs_id: str):
    """
    Retrieves all files inside the Vector Store and maps their filenames.
    Uses auto-paginating generators to list all files.
    """
    logger.info(f"Listing all files in OpenAI account...")
    file_id_to_name = {}
    for f in client.files.list(purpose="assistants"):
        file_id_to_name[f.id] = f.filename

    logger.info(f"Listing files in Vector Store {vs_id}...")
    vs_client = get_vector_stores_client(client)
    
    matched_files = []
    for vs_file in vs_client.files.list(vector_store_id=vs_id):
        filename = file_id_to_name.get(vs_file.id)
        if filename:
            matched_files.append({"id": vs_file.id, "filename": filename})
        else:
            # If filename is not in list, retrieve details directly
            try:
                file_details = client.files.retrieve(vs_file.id)
                matched_files.append({"id": vs_file.id, "filename": file_details.filename})
            except Exception as e:
                logger.warning(f"Could not retrieve details for file {vs_file.id}: {e}")
                
    return matched_files

def sync_vector_store(client: OpenAI, vs_id: str, active_articles, temp_dir: str):
    """
    Synchronizes the Zendesk active articles to the OpenAI Vector Store.
    """
    remote_files = get_vector_store_files(client, vs_id)
    deltas = calculate_deltas(remote_files, active_articles)

    logger.info(f"Sync Deltas calculated:")
    logger.info(f"  To Add: {len(deltas['add'])}")
    logger.info(f"  To Update: {len(deltas['update'])}")
    logger.info(f"  To Delete: {len(deltas['delete'])}")
    logger.info(f"  To Skip: {len(deltas['skip'])}")

    os.makedirs(temp_dir, exist_ok=True)

    # 1. Handle Deletions (Stale & Outdated files)
    files_to_delete = deltas["delete"] + [{"id": file_id, "filename": name} for _, file_id, name in deltas["update"]]
    for f in files_to_delete:
        logger.info(f"Deleting remote file: {f['filename']} (ID: {f['id']})")
        try:
            # Deleting the file automatically detaches it from any vector stores
            client.files.delete(f["id"])
        except Exception as e:
            logger.error(f"Failed to delete file {f['id']}: {e}")

    # 2. Handle Additions and Updates
    articles_to_upload = deltas["add"] + [art for art, _, _ in deltas["update"]]
    uploaded_count = 0
    vs_client = get_vector_stores_client(client)

    for article in articles_to_upload:
        title = article["title"]
        body_html = article.get("body") or ""
        art_id = article["id"]
        art_ts = iso_to_timestamp(article["updated_at"])
        
        # Ensure url uses the public support.optisigns.com domain
        html_url = article.get("html_url") or ""
        if "optisigns.zendesk.com" in html_url:
            html_url = html_url.replace("optisigns.zendesk.com", "support.optisigns.com")

        # Convert to Markdown (this appends Article URL: <url> at the end of the document body)
        markdown_content = convert_to_markdown(body_html, html_url)
        # Prepend Title header to the markdown body
        full_content = f"# {title}\n\n{markdown_content}"

        # Write to temporary file
        filename = f"optibot_{art_id}_{art_ts}.md"
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as file_out:
            file_out.write(full_content)

        logger.info(f"Uploading file: {filename}...")
        try:
            # Upload file
            with open(filepath, "rb") as file_in:
                uploaded_file = client.files.create(file=file_in, purpose="assistants")
            
            # Attach to Vector Store
            vs_client.files.create(
                vector_store_id=vs_id,
                file_id=uploaded_file.id
            )
            uploaded_count += 1
        except Exception as e:
            logger.error(f"Failed to upload/attach file {filename}: {e}")
        finally:
            # Clean up temporary local file
            if os.path.exists(filepath):
                os.remove(filepath)

    return {
        "added": len(deltas["add"]),
        "updated": len(deltas["update"]),
        "deleted": len(deltas["delete"]),
        "skipped": len(deltas["skip"]),
        "total_active": len(active_articles),
        "uploaded_successfully": uploaded_count
    }
