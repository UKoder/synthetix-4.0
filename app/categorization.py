import os
import json
from typing import Tuple

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# Load configuration dynamically
config = load_config()
QUEUE_KEYWORDS = config.get("queues", {})
TYPE_KEYWORDS = config.get("types", {})
PRIORITY_KEYWORDS = config.get("priorities", {})

def analyze_ticket(subject: str, body: str) -> Tuple[str, str, str]:
    """
    Returns (queue, ticket_type, priority) dynamically evaluated against `data/config.json`.
    """
    combined = f"{subject} {body}".lower()

    # Determine Queue
    queue = "General Inquiry"
    best_queue_score = 0
    for q, keywords in QUEUE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_queue_score:
            best_queue_score = score
            queue = q

    # Determine Type
    ticket_type = "Request"
    best_type_score = 0
    for t, keywords in TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_type_score:
            best_type_score = score
            ticket_type = t

    # Determine Priority
    priority = "low"
    if any(kw in combined for kw in PRIORITY_KEYWORDS.get("high", [])):
        priority = "high"
    elif any(kw in combined for kw in PRIORITY_KEYWORDS.get("medium", [])):
        priority = "medium"

    return queue, ticket_type, priority
