import json

# Configuration
LINKS_FILE = "page_links.json"  # Created by crawler
URL_MAP_FILE = "urls.txt"       # Created by crawler
OUTPUT_PR_FILE = "pagerank.json"
DAMPING = 0.85
ITERATIONS = 20

def load_url_map():
    """Create a reverse map: URL -> DocID"""
    url_to_id = {}
    with open(URL_MAP_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                doc_id, url = parts
                url_to_id[url] = int(doc_id)
    return url_to_id

def compute_pagerank():
    #1.Load Data
    print("Loading link data...")
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        raw_links = json.load(f) # { "1": ["http://...", ...], ... }

    url_to_id = load_url_map()
    
    #2. Building adjacency(DocID -> [DocIDs])
    #only care about links that point to pages inside the collection
    adjacency = {}
    all_nodes = set()
    
    for src_id_str, outgoing_urls in raw_links.items():
        src_id = int(src_id_str)
        all_nodes.add(src_id)
        
        valid_links = []
        for url in outgoing_urls:
            if url in url_to_id:
                target_id = url_to_id[url]
                # avoid self loop
                if target_id != src_id:
                    valid_links.append(target_id)
        
        adjacency[src_id] = valid_links
        # Ensure targets are in all_nodes
        for t in valid_links:
            all_nodes.add(t)

    #3 initializing pagerank
    N = len(all_nodes)
    print(f"Calculating PageRank for {N} nodes...")
    
    # Initial score = 1/N
    scores = {node: 1.0 / N for node in all_nodes}
    
    #4 power iteration
    for i in range(ITERATIONS):
        new_scores = {}
        sink_pr = 0
        
        # Calculate nodes with no outgoing links
        for node in all_nodes:
            if node not in adjacency or len(adjacency[node]) == 0:
                sink_pr += scores[node]
        
        for node in all_nodes:
            rank = (1 - DAMPING) / N
            rank += DAMPING * (sink_pr / N)
            for potential_src in all_nodes:
                if potential_src in adjacency and node in adjacency[potential_src]:
                    rank += DAMPING * (scores[potential_src] / len(adjacency[potential_src]))
            
            new_scores[node] = rank
        
        scores = new_scores
    
    #5. min-max normalization for easier combination with Cosine
    # maps scores to range [0, 1]
    min_score = min(scores.values())
    max_score = max(scores.values())
    
    normalized_scores = {}
    for node, sc in scores.items():
        if max_score - min_score == 0:
            normalized_scores[node] = 0
        else:
            normalized_scores[node] = (sc - min_score) / (max_score - min_score)

    #save
    with open(OUTPUT_PR_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized_scores, f)
    
    print(f"PageRank complete. Scores saved to {OUTPUT_PR_FILE}")

if __name__ == "__main__":
    compute_pagerank()