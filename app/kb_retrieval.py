import os
import math
import json
import re
from collections import Counter

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base")
HF_TICKETS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hf_tickets.json")


def tokenize(text: str):
    return re.findall(r'\w+', text.lower())


class KnowledgeBase:
    def __init__(self):
        self.documents = []
        self.doc_freq = Counter()
        self.load_and_index()

    def _add_doc(self, title: str, content: str, source: str, persist: bool = False):
        tokens = tokenize(content)
        self.documents.append({
            "title": title,
            "content": content,
            "tokens": tokens,
            "source": source
        })
        self.doc_freq.update(set(tokens))

        if persist:
            safe_title = "".join(c if c.isalnum() else "_" for c in title)
            if not os.path.exists(KB_DIR):
                os.makedirs(KB_DIR, exist_ok=True)
            filepath = os.path.join(KB_DIR, f"{safe_title}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)


    def load_and_index(self):
        """Load KB from two sources:
        1. Static .txt/.md files in data/knowledge_base/
        2. HuggingFace dataset answers grouped per queue (data/hf_tickets.json)
        """
        # Source 1: static files
        if os.path.exists(KB_DIR):
            for filename in os.listdir(KB_DIR):
                if filename.endswith(".txt") or filename.endswith(".md"):
                    fp = os.path.join(KB_DIR, filename)
                    with open(fp, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    if content:
                        self._add_doc(filename, content, filename)

        # Source 2: HuggingFace dataset — build representative answers per queue
        if os.path.exists(HF_TICKETS_PATH):
            print("Loading HuggingFace KB answers from dataset...")
            with open(HF_TICKETS_PATH, 'r', encoding='utf-8') as f:
                tickets = json.load(f)

            from collections import defaultdict
            queue_answers = defaultdict(list)
            for t in tickets:
                q = t.get("queue", "General")
                a = t.get("answer", "")
                if a and len(a) > 50:
                    queue_answers[q].append(a)

            # Take up to 3 representative answers per queue as single KB article
            for queue, answers in queue_answers.items():
                sample = answers[:3]
                kb_text = f"Queue: {queue}\n\n" + "\n\n---\n\n".join(sample)
                self._add_doc(f"[HF] {queue}", kb_text, f"hf_dataset:{queue}")

        print(f"KB indexed {len(self.documents)} articles.")

    def search(self, query: str, top_k: int = 3) -> list:
        if not self.documents:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        N = len(self.documents)
        scores = []
        for doc in self.documents:
            score = 0
            doc_token_counts = Counter(doc["tokens"])
            for token in query_tokens:
                if token in doc_token_counts:
                    tf = doc_token_counts[token] / len(doc["tokens"])
                    idf = math.log(N / (1 + self.doc_freq[token])) + 1
                    score += tf * idf
            scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scores[:top_k]:
            results.append({
                "score": float(score),
                "title": doc["title"],
                "source": doc["source"],
                "snippet": doc["content"][:400]
            })

        return results


kb = KnowledgeBase()
