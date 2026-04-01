import json
from dataclasses import dataclass
from typing import List, Dict

from app.rag.retriever import retrieve_for_claim

FACT_CHECK_PROMPT = """
You are a forensic fact-checking analyst. Your task is to determine the veracity of a claim
based strictly on the provided context documents. Do not use any prior knowledge.

Claim: {claim}

Context Documents:
{context}

Respond ONLY with a JSON object in this exact format:
{{
  "verdict": "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIABLE",
  "confidence": <float 0.0-1.0>,
  "justification": "<one sentence, max 30 words>",
  "source_urls": ["<url1>", "<url2>"]
}}
"""

@dataclass
class FactCheckResult:
    claim: str
    verdict: str
    confidence: float
    justification: str
    source_urls: List[str]

@dataclass
class TextVerificationResult:
    fact_check_results: List[FactCheckResult]
    text_credibility_score: float
    flags: List[str]

def call_llm(prompt: str) -> str:
    # Model: GPT-4o with temperature=0.0 (deterministic)
    # [MOCK LLM Call]
    return json.dumps({
        "verdict": "TRUE",
        "confidence": 0.88,
        "justification": "The context documents support the claim directly.",
        "source_urls": ["https://example.com"]
    })

def parse_verdict(verdict_json: str) -> dict:
    # Parse response: strip markdown fences, json.loads()
    cleaned = verdict_json.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:-3]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:-3]
    return json.loads(cleaned)

def extract_flags(results: List[FactCheckResult]) -> List[str]:
    flags = set()
    for r in results:
        if r.verdict == "FALSE":
            flags.add("false_claim_detected")
        elif r.verdict == "MISLEADING":
            flags.add("misleading_framing")
    return list(flags)

def compute_credibility_score(results: List[FactCheckResult]) -> float:
    # Aggregate across all claims:
    #   all TRUE/UNVERIFIABLE → text_credibility_score = 0.85
    #   any MISLEADING → text_credibility_score = 0.50, flag "misleading_framing"
    #   any FALSE → text_credibility_score = 0.20, flag "false_claim_detected"
    #   multiple FALSE → text_credibility_score = 0.05
    false_count = sum(1 for r in results if r.verdict == "FALSE")
    misleading_count = sum(1 for r in results if r.verdict == "MISLEADING")
    
    if false_count > 1:
        return 0.05
    if false_count > 0:
        return 0.20
    if misleading_count > 0:
        return 0.50
    return 0.85

def verify_claims(claims: List[str]) -> TextVerificationResult:
    results = []
    for claim in claims[:5]:  # cap at 5 claims per analysis to control latency + cost
        docs = retrieve_for_claim(claim)
        
        if not docs:
            results.append(FactCheckResult(claim, "UNVERIFIABLE", 0.0, "No relevant sources found.", []))
            continue
            
        context_str = "\n\n".join([f"[{d.source}] {d.text}" for d in docs])
        verdict_json = call_llm(FACT_CHECK_PROMPT.format(claim=claim, context=context_str))
        
        try:
            data = parse_verdict(verdict_json)
        except Exception:
            # On parse failure: retry once, then return UNVERIFIABLE with confidence=0.0
            try:
                # retry once
                verdict_json = call_llm(FACT_CHECK_PROMPT.format(claim=claim, context=context_str))
                data = parse_verdict(verdict_json)
            except Exception:
                data = {
                    "verdict": "UNVERIFIABLE",
                    "confidence": 0.0,
                    "justification": "Failed to parse LLM response.",
                    "source_urls": []
                }
                
        results.append(FactCheckResult(
            claim=claim,
            verdict=data.get("verdict", "UNVERIFIABLE"),
            confidence=float(data.get("confidence", 0.0)),
            justification=data.get("justification", ""),
            source_urls=data.get("source_urls", [])
        ))
        
    flags = extract_flags(results)
    score = compute_credibility_score(results)
    
    return TextVerificationResult(
        fact_check_results=results,
        text_credibility_score=score,
        flags=flags,
    )
