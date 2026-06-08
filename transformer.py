import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def convert_to_markdown(html_content: str, art_url: str = "") -> str:
    """
    Converts Zendesk article HTML content to clean Markdown.
    Expands relative links starting with /hc to absolute OptiSigns support URLs.
    """
    if not html_content:
        return ""

    if art_url:
        html_content = html_content + "<br> Article URL: " + art_url

    # 1. Parse HTML with BeautifulSoup to modify relative links
    soup = BeautifulSoup(html_content, "html.parser")
    for link in soup.find_all("a", href=True):
        href = link["href"]
        # If relative link starting with /hc/ or /hc
        if href.startswith("/hc"):
            link["href"] = "https://support.optisigns.com" + href

    # 2. Convert updated HTML to markdown using markdownify
    # Strip unnecessary spaces and handle formatting
    markdown = md(str(soup), heading_style="ATX")
    
    # 3. Clean up formatting (like excessive blank lines)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    # add blank link to markdown

    return markdown.strip()
