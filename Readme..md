# 🔍 Full-Stack Search Engine (Python & Flask)

A **full-stack information retrieval system** built from scratch using Python and Flask.  
This search engine crawls Wikipedia pages, indexes documents using a **Positional Inverted Index**, computes **PageRank** for link authority, and serves ranked search results through a web interface using a **hybrid ranking model** (TF-IDF Cosine Similarity + PageRank).

The project demonstrates the core building blocks of modern search engines, including crawling, indexing, ranking, and query processing.

---

##  Key Features

- **Web Crawler**
  - Crawls **1,000+ Wikipedia pages** using **Breadth-First Search (BFS)**
  - Extracts clean textual content and hyperlinks using `BeautifulSoup`
  - Builds a directed link graph for ranking analysis

- **Positional Inverted Index**
  - Stores term frequencies and **exact word positions**
  - Supports **exact phrase search** (e.g., `"computer science"`)
  - Enables efficient multi term query processing

- **Vector Space Retrieval Model**
  - Implements **TF-IDF weighting**
  - Uses **Cosine Similarity** to measure document relevance
  - Ranks documents based on content similarity to user queries

- **PageRank Algorithm**
  - Computes global document authority using **Power Iteration**
  - Uses a damping factor of **0.85**
  - Incorporates link structure into ranking decisions

- **Hybrid Ranking Strategy**
  - Combines content relevance with link authority
    Final Score = 0.7 × Cosine Similarity + 0.3 × PageRank

- **Web-Based Search Interface**
  - Built using **Flask**
  - Clean and responsive UI for submitting queries and viewing ranked results

---

## 🧠 System Architecture

The system follows a standard **Information Retrieval (IR) pipeline**:

1. **Crawler (`crawler.py`)**
   - Downloads web pages
   - Extracts text and outgoing links
   - Constructs the document link graph

2. **Indexer (`index_web.py`)**
   - Tokenizes text
   - Removes stopwords
   - Applies **Porter Stemming**
   - Builds a positional inverted index

3. **Ranker (`pagerank.py`)**
   - Analyzes the link graph
   - Computes PageRank scores using power iteration

4. **Search Engine (`app.py`)**
   - Handles user queries
   - Supports keyword and phrase search
   - Ranks results using the hybrid scoring model
   - Serves results via Flask

---

## Tech Stack

- **Programming Language:** Python  
- **Web Framework:** Flask  
- **Web Crawling:** BeautifulSoup  
- **Information Retrieval:** TF-IDF, Cosine Similarity, Positional Inverted Index  
- **Ranking Algorithm:** PageRank (Power Iteration)  
- **Frontend:** HTML, CSS (Flask templates)

---

##  Installation & Usage

### 1. Clone the Repository
```bash
git clone https://github.com/alfacluze/search-engine-project.git
cd search-engine-project
