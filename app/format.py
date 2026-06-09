import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from sync import get_vector_store_files

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    vs_id = os.getenv("OPENAI_VECTOR_STORE_ID")
    if not api_key or not vs_id:
        print(f"Missing API key or Vector Store ID in .env. API KEY: {bool(api_key)}, VS ID: {vs_id}")
        return

    client = OpenAI(api_key=api_key)
    print(f"Retrieving files for vector store {vs_id}...")
    files = get_vector_store_files(client, vs_id)

    print(f"Found {len(files)} files to delete.")
    for f in files:
        print(f"Deleting {f['filename']} (ID: {f['id']})...")
        try:
            client.files.delete(f["id"])
            client.vector_stores.files.delete(
                vector_store_id=vs_id,
                file_id=f["id"]
            )
        except Exception as e:
            print(f"Failed to delete {f['id']}: {e}")

if __name__ == "__main__":
    main()
