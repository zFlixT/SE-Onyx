import os
from typing import List

def summarize_reasons(name: str, reasons: List[str]) -> str:
    # Simula una breve explicación "tipo LLM"
    bullet = "; ".join(reasons[:4])
    return f"{name}: {bullet}."