## EPUB Splitter

**EPUB Splitter** is a command-line tool designed to extract and organize chapters from EPUB ebook files into structured CSV files. It supports multiple EPUB parsing strategies, includes intelligent fallbacks, and can handle a wide variety of edge cases using both native metadata and AI assistance via the OpenAI API.

---

### Features

* **Multi-level EPUB parsing**: Extracts chapter content from EPUBs using native Table of Contents (TOC), detected headings, or AI-based predictions when metadata is insufficient.
* **TOC and Heading Fallbacks**: Uses heading tags (`<h1>`, `<h2>`, etc.) when a native TOC is unavailable or unreliable.
* **LLM-powered Chapter Extraction**: If TOC and headings fail, it leverages OpenAI's GPT to infer chapter titles from the ebook's opening pages.
* **Smart Content Slicing**: Dynamically identifies chapter text based on offset positions of headings, even without internal anchors.
* **De-duplication Logic**: Automatically detects and removes duplicate chapter content, ensuring a clean final dataset.
* **Batch EPUB Support**: Can process a single EPUB file or a directory full of EPUBs in one go.
* **CSV Output**: Outputs the extracted chapters in a clean CSV format, with one chapter per row.

---

### How to use?

1. **Install dependencies** (see below).
2. Ensure the `OPENAI_API_KEY` is set in your environment.
3. Run the script from the command line:

   ```bash
   python ebook_splitter.py path/to/book.epub --output-dir path/to/output
   ```
4. Alternatively, process a folder of EPUBs:

   ```bash
   python ebook_splitter.py path/to/folder --preview-pages 10
   ```
5. Extracted chapter content will be saved as `.csv` files in the output directory.

---

### Handling of Edge Cases

* **Missing TOC**: Falls back to scanning heading tags (like `<h1>`, `<h2>`).
* **Absent or ambiguous headings**: Sends the first N pages to GPT for chapter title prediction (`--preview-pages` configurable).
* **Broken anchors**: Attempts ID-based fallbacks and uses tag text to locate content.
* **Duplicate content**: Compares chapter texts and removes duplicates while preserving unique titles.
* **Unmatched chapter titles** (from GPT): Logs warnings but continues processing with best-effort matching.

---

### Special Requirements

* **Environment Variable**: You must set the `OPENAI_API_KEY` in your environment for GPT fallback functionality.
* **Python 3.x** with the following packages:

  * `ebooklib`
  * `beautifulsoup4` (`bs4`)
  * `openai`
  * `lxml`

Install via pip:

```bash
pip install ebooklib beautifulsoup4 openai lxml
```