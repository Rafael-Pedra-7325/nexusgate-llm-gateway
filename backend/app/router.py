import re
from typing import Tuple, List
from app.config import MODEL_CATALOG, FALLBACK_CHAINS


REASONING_KEYWORDS = {
    "architecture", "architect", "distributed", "consensus", "algorithm", "optimize",
    "optimization", "compare", "trade-off", "tradeoff", "analyze", "analysis",
    "derive", "proof", "theorem", "security", "vulnerability", "concurrency",
    "deadlock", "scalability", "microservice", "kubernetes", "design", "refactor",
    "debug", "step by step", "step-by-step", "implement", "benchmark", "sql",
    "arquitetura", "distribuído", "algoritmo", "otimizar", "comparar", "analise",
    "segurança", "concorrência", "escalabilidade", "implementar", "refatorar"
}


def analyze_complexity(prompt: str, message_count: int = 1) -> Tuple[float, str, List[str]]:
    """
    Computes a deterministic prompt complexity score in [0.0, 1.0] and maps it
    to a routing tier ('simple', 'moderate', 'complex') along with human-readable signals.
    """
    text = prompt.strip()
    lower = text.lower()
    words = re.findall(r"\w+", lower)
    word_count = len(words)
    signals: List[str] = []

    score = 0.0

    # 1. Length contribution (up to 0.30)
    if word_count > 120:
        score += 0.30
        signals.append(f"Long prompt ({word_count} words)")
    elif word_count > 45:
        score += 0.18
        signals.append(f"Medium-length prompt ({word_count} words)")
    elif word_count > 15:
        score += 0.08
    else:
        signals.append(f"Concise query ({word_count} words)")

    # 2. Code / structured syntax markers (up to 0.30)
    has_code_block = "```" in text or bool(re.search(r"\b(def |class |function |SELECT |import |const |func )\b", text))
    if has_code_block:
        score += 0.28
        signals.append("Code / technical syntax detected")

    # 3. Deep reasoning & domain keywords (up to 0.32)
    matched_kw = [kw for kw in REASONING_KEYWORDS if kw in lower]
    if matched_kw:
        kw_bonus = min(0.32, len(matched_kw) * 0.10)
        score += kw_bonus
        signals.append(f"Reasoning markers: {', '.join(matched_kw[:3])}")

    # 4. Multi-part questions / constraints (up to 0.12)
    question_marks = text.count("?")
    bullet_lines = len(re.findall(r"(^|\n)\s*[-*•1-9][.)\s]", text))
    if question_marks >= 2 or bullet_lines >= 2:
        score += 0.12
        signals.append("Multi-part constraints")

    # 5. Multi-turn context depth (up to 0.08)
    if message_count > 4:
        score += 0.08
        signals.append(f"Deep conversation ({message_count} turns)")

    score = round(min(1.0, max(0.05, score)), 3)

    if score < 0.34:
        tier = "simple"
    elif score < 0.66:
        tier = "moderate"
    else:
        tier = "complex"

    return score, tier, signals


def select_model_and_chain(
    requested_model: str,
    strategy: str,
    complexity_tier: str,
) -> Tuple[str, List[str], str]:
    """
    Determines the primary target model and ordered fallback chain based on
    routing strategy ('complexity', 'cost', 'balanced') or explicit model override.
    """
    if requested_model and requested_model != "auto" and requested_model in MODEL_CATALOG:
        tier = MODEL_CATALOG[requested_model]["tier"]
        chain = [requested_model] + [m for m in FALLBACK_CHAINS[tier] if m != requested_model]
        return requested_model, chain, f"Explicit model override ({requested_model})"

    if strategy == "cost":
        # Always prioritize lowest-cost tier first, falling back upward if needed
        chain = ["llama-3.1-8b-instant", "gpt-4o-mini", "claude-3-5-haiku"]
        reason = "Cost-first policy -> ultra-low-cost fast inference tier"
        return chain[0], chain, reason

    if strategy == "balanced":
        if complexity_tier == "complex":
            chain = ["claude-3-5-sonnet", "gpt-4o", "claude-3-5-haiku"]
            reason = "Balanced policy (high complexity) -> frontier reasoning model"
        elif complexity_tier == "moderate":
            chain = ["claude-3-5-haiku", "gpt-4o-mini", "gpt-4o"]
            reason = "Balanced policy (moderate complexity) -> mid-tier efficiency model"
        else:
            chain = ["gpt-4o-mini", "llama-3.1-8b-instant", "claude-3-5-haiku"]
            reason = "Balanced policy (low complexity) -> high-value compact model"
        return chain[0], chain, reason

    # Default: 'complexity' strategy
    chain = list(FALLBACK_CHAINS[complexity_tier])
    reason = f"Complexity-aware routing ({complexity_tier} tier) -> {chain[0]}"
    return chain[0], chain, reason
