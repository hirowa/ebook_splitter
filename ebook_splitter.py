#!/usr/bin/env python3
import os, re, json, csv, argparse
from ebooklib import epub
from bs4 import BeautifulSoup
from collections import defaultdict
import openai

AVG_CHARS_PER_PAGE = 2000

def parse_args():
    p = argparse.ArgumentParser(description="Extract chapters from EPUB(s) into quoted CSV(s)")
    p.add_argument("input_path", help="An .epub file or a folder of EPUBs")
    p.add_argument("--preview-pages", type=int, default=15, help="Pages to send to LLM if no TOC")
    p.add_argument("--output-dir", default=".", help="Output CSV directory")
    return p.parse_args()

def flatten_and_clean_html(item):
    soup = BeautifulSoup(item.get_content(), "lxml")
    for tag in soup.select("nav, header, footer, script, style"):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()

def normalize(s):
    s = s.replace('’', "'").replace('“','"').replace('”','"')
    return re.sub(r"\s+", " ", s).strip().lower()

def get_native_toc(book):
    out = []
    try:
        def recurse(entries):
            for e in entries or []:
                if hasattr(e, 'href') and hasattr(e, 'title'):
                    out.append((e.title, e.href))
                elif isinstance(e, tuple) and len(e) == 2:
                    link, sub = e
                    out.append((link.title, link.href))
                    recurse(sub)
        recurse(book.toc)
    except Exception:
        return []
    return out

def fallback_titles(snippet):
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role":"system","content":"Output strict JSON array of {\"title\":\"...\"} objects only."},
            {"role":"user","content":(
                "You’re given the first pages of an ebook. "
                "Return ONLY a JSON array of objects with a single field title, listing each chapter heading in order.\n\n"
                f"Ebook excerpt:\n\"\"\"\n{snippet}\n\"\"\""
            )},
        ],
    )
    arr = json.loads(resp.choices[0].message.content)
    return [o["title"] for o in arr]

def spine_docs(book):
    return [book.get_item_with_id(idref) for idref, _ in book.spine if isinstance(book.get_item_with_id(idref), epub.EpubHtml)]

def find_offset(full_norm, norm_title, last):
    pos = full_norm.find(norm_title, last)
    if pos >= 0:
        return pos
    words = norm_title.split()
    for L in range(len(words), 0, -1):
        prefix = " ".join(words[:L])
        p = full_norm.find(prefix, last)
        if p >= 0:
            return p
    return None

def extract_chapter_from_anchor(soup, anchor_id, next_anchor_id=None):
    if not soup or not anchor_id:
        return None
    start_tag = soup.find(id=anchor_id)
    if not start_tag:
        # Try best-effort fallback: heading containing anchor_id in text
        start_tag = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'a'] and anchor_id.lower() in tag.get_text(strip=True).lower())
    if not start_tag:
        return None

    # Instead of next_sibling, walk all forward elements
    content = []
    current = start_tag.find_next()
    while current:
        if current.name in ['h1', 'h2', 'h3', 'a'] and current.get('id') == next_anchor_id:
            break
        if next_anchor_id and getattr(current, 'get', lambda k: None)('id') == next_anchor_id:
            break
        content.append(current.get_text(strip=True))
        current = current.find_next()
    return '\n'.join(content).strip()

def extract_headings_and_sections(book):
    docs = spine_docs(book)
    chapters = []
    for doc in docs:
        soup = BeautifulSoup(doc.get_content(), "lxml")
        headings = soup.find_all(re.compile("^h[1-3]$"))
        for i, h in enumerate(headings):
            title = h.get_text()
            content = []
            for sibling in h.next_siblings:
                if sibling.name and re.match("^h[1-3]$", sibling.name):
                    break
                if isinstance(sibling, str):
                    content.append(sibling.strip())
                else:
                    content.append(sibling.get_text(separator=" ").strip())
            txt = re.sub(r"\s+", " ", " ".join(content)).strip()
            if txt:
                chapters.append((title, txt))
    return chapters

def process_epub(epub_path, preview_pages, out_dir):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Please set OPENAI_API_KEY in your environment")

    book = epub.read_epub(epub_path)
    base = os.path.splitext(os.path.basename(epub_path))[0]
    csv_path = os.path.join(out_dir, f"{base}.csv")

    chapters = []
    toc = get_native_toc(book)
    if toc:
        print(f"[{base}] Using native TOC ({len(toc)} entries)")
        for i, (title, href) in enumerate(toc):
            parts = href.split("#")
            base_file = parts[0]
            anchor = parts[1] if len(parts) > 1 else None

            item = book.get_item_with_href(base_file)
            if not item:
                continue

            soup = BeautifulSoup(item.get_content(), "lxml")
            next_anchor = None
            if i + 1 < len(toc):
                next_href = toc[i + 1][1]
                if next_href.startswith(base_file + "#"):
                    next_anchor = next_href.split("#")[1]

            if anchor:
                txt = extract_chapter_from_anchor(soup, anchor, next_anchor)
            else:
                txt = flatten_and_clean_html(item)

            if txt:
                chapters.append((title, txt))
            else:
                print(f"[{base}] Empty content for chapter '{title}' (anchor: {anchor})")

    # fallback to heading detection
    if not chapters:
        print(f"[{base}] No usable native TOC, trying heading detection fallback...")
        chapters = extract_headings_and_sections(book)

    # fallback: GPT title-based offsets
    if not chapters:
        print(f"[{base}] Falling back to LLM + offset slicing")
        docs = spine_docs(book)
        cleaned = [flatten_and_clean_html(d) for d in docs]
        full = " ".join(cleaned)
        full = re.sub(r"\s+", " ", full)
        snippet = full[: preview_pages * AVG_CHARS_PER_PAGE]

        try:
            titles = fallback_titles(snippet)
        except Exception as e:
            print(f"[{base}] LLM fallback failed: {e}")
            return

        full_norm = normalize(full)
        offsets = []
        last = 0
        unmatched = []
        for t in titles:
            nt = normalize(t)
            pos = find_offset(full_norm, nt, last)
            if pos is None:
                unmatched.append(t)
            else:
                offsets.append((t, pos))
                last = pos + len(nt)

        if unmatched:
            print(f"[{base}] WARNING: {len(unmatched)} titles unmatched")

        for i, (t, s) in enumerate(offsets):
            e = offsets[i+1][1] if i+1 < len(offsets) else len(full)
            chunk = full[s:e].strip()
            chapters.append((t, chunk))

    if len(chapters) < 2:
        print(f"[{base}] Only {len(chapters)} chapters extracted, skipping.")
        return

    # de-duplication
    dedup = defaultdict(list)
    for t, c in chapters:
        dedup[c].append(t)
    collisions = [grp for grp in dedup.values() if len(grp) > 1]
    if collisions:
        print(f"[{base}] Duplicate chapter content found. Removing duplicates.")
        unique_chapters = []
        seen = set()
        for t, c in chapters:
            if c not in seen:
                seen.add(c)
                unique_chapters.append((t, c))
        chapters = unique_chapters

    os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        w = csv.writer(cf, quoting=csv.QUOTE_ALL)
        w.writerow(["chapter", "content"])
        for title, content in chapters:
            w.writerow([title, content])

    print(f"[{base}] ✔ Wrote {len(chapters)} chapters → {csv_path}\n")

def main():
    args = parse_args()
    if os.path.isdir(args.input_path):
        inputs = [os.path.join(args.input_path, f) for f in os.listdir(args.input_path) if f.lower().endswith(".epub")]
        if not inputs:
            print("No EPUB files found in folder:", args.input_path)
            return
    elif args.input_path.lower().endswith(".epub") and os.path.isfile(args.input_path):
        inputs = [args.input_path]
    else:
        print("Please provide a valid EPUB file or folder.")
        return

    for epub_file in inputs:
        try:
            process_epub(epub_file, args.preview_pages, args.output_dir)
        except Exception as e:
            name = os.path.basename(epub_file)
            print(f"[{name}] ERROR processing: {e}\n")

if __name__ == "__main__":
    main()
