import json
from dataclasses import dataclass

# [MOCK]
# import spacy
# from openai import OpenAI
# import os

@dataclass
class ClaimResult:
    claims: list[str]
    named_entities: list[str]

def extract_claims(text: str) -> ClaimResult:
    # Input: raw text (caption, article snippet, overlay text from image OCR)
    if not text.strip():
        return ClaimResult(claims=[], named_entities=[])
        
    # Use spaCy en_core_web_sm for NER — extract named entities (persons, orgs, dates, locations)
    # [MOCK]
    # nlp = spacy.load("en_core_web_sm")
    # doc = nlp(text)
    # entities = [ent.text for ent in doc.ents]
    entities = ["Example Entity"]
    
    # Use a prompt to GPT-4/Mistral to extract verifiable factual claims:
    # "Extract all verifiable factual claims from this text as a JSON list of strings"
    
    # [MOCK]
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "system", "content": "Extract all verifiable factual claims from this text as a JSON list of strings."},
    #         {"role": "user", "content": text}
    #     ]
    # )
    # claims = json.loads(response.choices[0].message.content)
    
    claims = ["Example verifiable claim extracted from text."]
    
    return ClaimResult(claims=claims, named_entities=entities)
