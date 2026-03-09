def generate_draft_reply(queue: str, ticket_type: str, priority: str,
                         retrieved_docs: list, subject: str) -> str:
    """
    Generates a grounded draft reply using the ticket metadata and retrieved KB snippets.
    """
    # Opening based on priority
    if priority == "high":
        opening = (
            f"Hello,\n\nThank you for reaching out. We recognize the urgency of your request "
            f"regarding '{subject}' and we are treating this as a **high-priority** matter.\n"
        )
    elif priority == "medium":
        opening = (
            f"Hello,\n\nThank you for contacting us about '{subject}'. "
            f"We have logged this as a **{ticket_type}** and are actively looking into it.\n"
        )
    else:
        opening = (
            f"Hello,\n\nThank you for your message regarding '{subject}'. "
            f"We appreciate you reaching out to our **{queue}** team.\n"
        )

    # Professional grounding
    if retrieved_docs:
        best = retrieved_docs[0]
        # Professional conversational response
        kb_section = (
            f"\nBased on the information available, {best['snippet']}"
        )
    else:
        kb_section = (
            "\nCould you please provide more details so we can assist you better? For example: device details, error messages received, or the steps you already tried."
        )

    # Closing
    closing = (
        f"\n\nOur **{queue}** team will review your request and follow up shortly."
        f"\n\nBest regards,\nCustomer Support Team"
    )

    return opening + kb_section + closing
