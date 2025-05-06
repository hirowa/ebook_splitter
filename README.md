## EPUB Splitter

**EPUB Splitter** is a command-line tool that extracts clean, structured chapter data from `.epub` files and exports them to CSV. It intelligently handles both well-structured and messy ebooks using native metadata, HTML headings, or GPT-powered fallback when needed. Ideal for data processing, research, digital archiving, or AI workflows.

---

### Features

- **Multi-level EPUB parsing**: Extracts chapter content from EPUBs using native Table of Contents (TOC), detected headings, or AI-based predictions when metadata is insufficient.
- **TOC and Heading Fallbacks**: Uses heading tags (`<h1>`, `<h2>`, etc.) when a native TOC is unavailable or unreliable.
- **LLM-powered Chapter Extraction**: If TOC and headings fail, it leverages OpenAI's GPT to infer chapter titles from the ebook's opening pages.
- **Smart Content Slicing**: Dynamically identifies chapter text based on offset positions of headings, even without internal anchors.
- **De-duplication Logic**: Automatically detects and removes duplicate chapter content, ensuring a clean final dataset.
- **Batch EPUB Support**: Can process a single EPUB file or a directory full of EPUBs in one go.
- **CSV Output**: Outputs the extracted chapters in a clean CSV format, with one chapter per row.

---

### Common Use Cases

- **Academic research**: Extract chapters from ebooks for citation, analysis, or text mining.
- **Content repurposing**: Convert book content into blog series, lesson plans, or course modules.
- **Digital archiving**: Reformat and preserve ebooks in structured datasets.
- **Reading apps or tools**: Prepare book content for segmentation, annotation, or interactive use.
- **AI workflows**: Preprocess content for summarization, Q\&A, or LLM fine-tuning.

---

### How to Use

1. **Install dependencies**:

   ```bash
   pip install ebooklib beautifulsoup4 openai lxml
   ```

2. **Set your OpenAI API key** (optional, only needed for GPT fallback):

   - Windows: `set OPENAI_API_KEY=your_key`
   - macOS/Linux: `export OPENAI_API_KEY=your_key`

3. **Run the script**:

   ```bash
   python ebook_splitter.py path/to/your/book.epub
   ```

---

### Windows Launcher

A `.bat` launcher is included. Just double-click it, paste or type the path to your EPUB file or folder when prompted, and the script will run — no command-line typing required.

---

### Handling of Edge Cases

- **Missing TOC**: Falls back to scanning heading tags (like `<h1>`, `<h2>`).
- **Absent or ambiguous headings**: Sends the first N pages to GPT for chapter title prediction (`--preview-pages` configurable).
- **Broken anchors**: Attempts ID-based fallbacks and uses tag text to locate content.
- **Duplicate content**: Compares chapter texts and removes duplicates while preserving unique titles.
- **Unmatched chapter titles** (from GPT): Logs warnings but continues processing with best-effort matching.
