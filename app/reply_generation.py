import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_draft_reply(queue: str, ticket_type: str, priority: str,
                         retrieved_docs: list, subject: str) -> str:
    """
    Generates a grounded draft reply using the config templates and retrieved KB snippets.
    """
    config = load_config()
    templates = config.get("reply_templates", {})
    company_name = config.get("company_name", "Our Company")

    # Opening based on priority
    if priority == "high":
        opening = "Hello,\n\n" + templates.get("high_priority_greeting", "We recognize the urgency of this request.") + "\n"
    elif priority == "medium":
        opening = "Hello,\n\n" + templates.get("medium_priority_greeting", "We have logged this issue and are looking into it.") + "\n"
    else:
        opening = "Hello,\n\n" + templates.get("low_priority_greeting", "We appreciate you reaching out.") + "\n"

    # String format the opening
    opening = opening.format(subject=subject, ticket_type=ticket_type, queue=queue)

    # Professional grounding
    if retrieved_docs:
        best = retrieved_docs[0]
        # Professional conversational response
        kb_section = (
            f"\nBased on the information available, {best['snippet']}"
        )
    else:
        kb_section = "\n" + templates.get("fallback_request_more_info", "Could you provide more details?")

    # Closing
    closing = "\n\n" + templates.get("closing", "Best regards,\nThe {company_name} Support Team").format(queue=queue, company_name=company_name)

    return opening + kb_section + closing
