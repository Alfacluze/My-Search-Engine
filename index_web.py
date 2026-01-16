import re
import os
import json
from collections import defaultdict
from nltk.stem import PorterStemmer

# stemming and stopword
USE_STOPWORDS = True
USE_STEMMING = True
STOPWORDS_FILE = "stopwords.txt"
INPUT_FILE = "web_collection.all"

def load_stopwords(path=STOPWORDS_FILE):
    s = set()
    if USE_STOPWORDS and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    s.add(w.lower())
    return s

def parse_collection(filePath):
    """
    Parses collection to get:
    1. docs: {doc_id: "title + text"} (for indexing)
    2. titles: {doc_id: "Actual Title"} (for display)
    """
    docs = {}
    titles = {}
    
    if not os.path.exists(filePath):
        print(f"Error: {filePath} not found!")
        return {}, {}

    with open(filePath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_docs = content.split(".I ")[1:]
    for raw_doc in raw_docs:
        lines = raw_doc.split("\n")
        try:
            doc_id = int(lines[0].strip())
        except ValueError:
            continue
            
        text_for_index = ""
        current_title = ""
        
        mode = "" # 'T', 'W', 'X', etc.
        
        for line in lines[1:]:
            if line.startswith(".T"):
                mode = "T"
                continue
            elif line.startswith(".W"):
                mode = "W"
                continue
            elif line.startswith(".X"):
                mode = "X"
                continue
            elif line.startswith((".B", ".A", ".N", ".K", ".C", ".I")):
                mode = "OTHER"
                continue
            
            if mode == "T":
                current_title += line + " "
                text_for_index += line + " " 
            elif mode == "W":
                text_for_index += line + " "

        docs[doc_id] = text_for_index.strip()
        titles[doc_id] = current_title.strip()
        
    return docs, titles

def preprocess_text(text, stopwords, use_stemming=USE_STEMMING):
    tokens = re.findall(r"[a-zA-Z]+(?:-[a-zA-Z]+)*", text.lower())
    ps = PorterStemmer()
    processed = []
    for t in tokens:
        if USE_STOPWORDS and t in stopwords:
            continue
        if use_stemming:
            t = ps.stem(t)
        processed.append(t)
    return processed
def build_index(docs):
    stopwords = load_stopwords()
    inverted_index = defaultdict(lambda: defaultdict(list))
    doc_token_counts = defaultdict(int)

    for doc_id, text in docs.items():
        tokens = preprocess_text(text, stopwords, USE_STEMMING)
        doc_token_counts[doc_id] = len(tokens)
        for pos, token in enumerate(tokens):
            inverted_index[token][doc_id].append(pos)

    return inverted_index, doc_token_counts

def write_index(inverted_index, doc_token_counts, titles, dict_file="dictionary.txt", postings_file="postings.txt", meta_file="meta.json", titles_file="titles.txt"):
    # dictionary
    with open(dict_file, "w", encoding="utf-8") as df:
        for term in sorted(inverted_index.keys()):
            df_count = len(inverted_index[term])
            df.write(f"{term} {df_count}\n")

    # posting
    with open(postings_file, "w", encoding="utf-8") as pf:
        for term in sorted(inverted_index.keys()):
            posting_entries = []
            postings = inverted_index[term]
            for doc_id in sorted(postings.keys()):
                positions = postings[doc_id]
                tf = len(positions)
                pos_str = ",".join(map(str, positions))
                posting_entries.append(f"{doc_id}:{tf}:{pos_str}")
            pf.write(f"{term} -> {' ; '.join(posting_entries)}\n")
    # Meta
    meta = {
        "N": len(doc_token_counts),
        "doc_token_counts": doc_token_counts
    }
    with open(meta_file, "w", encoding="utf-8") as mf:
        json.dump(meta, mf)

    # titles (New)
    with open(titles_file, "w", encoding="utf-8") as tf:
        for doc_id, title in titles.items():
            tf.write(f"{doc_id} {title}\n")

if __name__ == "__main__":
    print(f"Building index from {INPUT_FILE}...")
    docs, titles = parse_collection(INPUT_FILE)
    if docs:
        inverted_index, doc_token_counts = build_index(docs)
        write_index(inverted_index, doc_token_counts, titles)
        print("Indexing complete! Created: dictionary.txt, postings.txt, meta.json, titles.txt")
    else:
        print("No documents found.")