from flask import Flask, render_template, request
import math
import re
import json
from collections import defaultdict, Counter
from nltk.stem import PorterStemmer

app = Flask(__name__)

#config
FILES = {
    "dict": "dictionary.txt",
    "postings": "postings.txt",
    "meta": "meta.json",
    "pagerank": "pagerank.json",
    "urls": "urls.txt",
    "titles": "titles.txt"
}

W1 = 0.7  #Cosine weight
W2 = 0.3  #pagerank weight

index_data = {
    "inverted_index": defaultdict(lambda: defaultdict(list)),
    "df": {},
    "pagerank": {},
    "urls": {},
    "titles": {},
    "N": 0,
    "doc_norms": defaultdict(float)
}

#1 storing position
def load_data():
    print("Loading Search Engine Data with Positions...")
    with open(FILES["meta"], "r", encoding="utf-8") as f:
        meta = json.load(f)
        index_data["N"] = meta["N"]
    with open(FILES["pagerank"], "r", encoding="utf-8") as f:
        pr_raw = json.load(f)
        index_data["pagerank"] = {int(k): v for k,v in pr_raw.items()}
    with open(FILES["urls"], "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                index_data["urls"][int(parts[0])] = parts[1]
    with open(FILES["titles"], "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                index_data["titles"][int(parts[0])] = parts[1]
    with open(FILES["dict"], "r", encoding="utf-8") as f:
        for line in f:
            term, freq = line.strip().split()
            index_data["df"][term] = int(freq)
    with open(FILES["postings"], "r", encoding="utf-8") as f:
        for line in f:
            term, rest = line.split(" -> ")
            postings = rest.strip().split(" ; ")
            for entry in postings:
                #formet: doc_id:tf:pos1,pos2,pos3..
                parts = entry.split(":")
                doc_id = int(parts[0])
                tf = int(parts[1])
                
                #Parse positionslist needed for phrase search
                positions = [int(p) for p in parts[2].split(",")]
                
                # Store oosition in index not just tf
                index_data["inverted_index"][term][doc_id] = positions
                
                if term in index_data["df"]:
                    idf = math.log10(index_data["N"] / index_data["df"][term])
                    weight = tf * idf
                    index_data["doc_norms"][doc_id] += weight ** 2

    for doc_id in index_data["doc_norms"]:
        index_data["doc_norms"][doc_id] = math.sqrt(index_data["doc_norms"][doc_id])

    print("Data Load Complete!")

#2 Helper functions
def preprocess_query(text):
    tokens = re.findall(r"[a-zA-Z]+(?:-[a-zA-Z]+)*", text.lower())
    ps = PorterStemmer()
    stopwords = {"the", "and", "is", "in", "it", "to", "of", "for", "on", "a"} 
    return [ps.stem(t) for t in tokens if t not in stopwords]

def get_phrase_docs(query_terms):
    """
    Returns a set of DocIDs that contain the EXACT PHRASE.
    Logic: term2 position must be term1 position + 1
    """
    #1 Start with docs that contain all terms
    common_docs = set(index_data["inverted_index"][query_terms[0]].keys())
    for term in query_terms[1:]:
        if term in index_data["inverted_index"]:
            common_docs &= set(index_data["inverted_index"][term].keys())
        else:
            return set() #Term not found

    valid_phrase_docs = set()

    #2 Check positions for each doc
    for doc_id in common_docs:
        # Get position list for first term
        current_positions = index_data["inverted_index"][query_terms[0]][doc_id]
        
        for pos in current_positions:
            match_found = True
            expected_next = pos + 1    
            # check subsequent terms
            for term in query_terms[1:]:
                term_positions = index_data["inverted_index"][term][doc_id]
                if expected_next not in term_positions:
                    match_found = False
                    break
                expected_next += 1
            
            if match_found:
                valid_phrase_docs.add(doc_id)
                break 
    
    return valid_phrase_docs

def calculate_cosine(query_terms, limit_docs=None):
    """
    limit_docs: If provided (for phrase search), only score these docs.
    """
    scores = defaultdict(float)
    query_tf = Counter(query_terms)
    query_norm = 0.0

    for term, tf in query_tf.items():
        if term in index_data["df"]:
            idf = math.log10(index_data["N"] / index_data["df"][term])
            w = tf * idf
            query_norm += w ** 2
            if term in index_data["inverted_index"]:
                # loop docs for this term
                for doc_id, positions in index_data["inverted_index"][term].items():
                    
                    # If doing Phrase Search then skip docs 
                    if limit_docs is not None and doc_id not in limit_docs:
                        continue
                        
                    doc_tf = len(positions) # recal. tf from list length
                    doc_weight = doc_tf * idf
                    scores[doc_id] += w * doc_weight
    
    query_norm = math.sqrt(query_norm)

    final_cosine = {}
    for doc_id, dot_product in scores.items():
        denom = (query_norm * index_data["doc_norms"][doc_id])
        if denom > 0:
            final_cosine[doc_id] = dot_product / denom          
    return final_cosine

#3 main search
@app.route('/', methods=['GET', 'POST'])
def search():
    results = []
    query = ""
    is_phrase_search = False
    if request.method == 'POST':
        query = request.form.get('query', '')
        if '"' in query:
            is_phrase_search = True
            clean_query = query.replace('"', '') 
        else:
            clean_query = query
        if clean_query:
            q_terms = preprocess_query(clean_query)
            limit_docs = None
            if is_phrase_search and len(q_terms) > 1:
                limit_docs = get_phrase_docs(q_terms)
                if not limit_docs:
                    limit_docs = set()

            #ranking 
            cos_scores = calculate_cosine(q_terms, limit_docs=limit_docs)
            combined_scores = []            
            for doc_id, cos_val in cos_scores.items():
                pr_val = index_data["pagerank"].get(doc_id, 0.0)
                final_score = (W1 * cos_val) + (W2 * pr_val)
                url = index_data["urls"].get(doc_id, "#")
                title = index_data["titles"].get(doc_id, "No Title")
                
                combined_scores.append({"doc_id": doc_id, "title": title, "url": url, "score": round(final_score, 4), "cosine": round(cos_val, 4), "pagerank": round(pr_val, 4)})
            
            results = sorted(combined_scores, key=lambda x: x['score'], reverse=True)[:20]
    return render_template('index.html', results=results, query=query)

if __name__ == '__main__':
    load_data()
    app.run(debug=True)