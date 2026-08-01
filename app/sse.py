def sse_event(event: str, html: str) -> str:
    """Format a Server-Sent Event, splitting multi-line HTML across `data:` lines per spec."""
    data_lines = "\n".join(f"data: {line}" for line in html.splitlines()) or "data:"
    return f"event: {event}\n{data_lines}\n\n"
