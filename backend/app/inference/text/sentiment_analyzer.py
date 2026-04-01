import json
from dataclasses import dataclass

# [MOCK]
# from openai import OpenAI
# import os

@dataclass
class SentimentResult:
    manipulation_score: float
    detected_techniques: list[str]

def analyze_sentiment(text: str) -> SentimentResult:
    # Detect manipulative framing and emotional manipulation patterns
    if not text.strip():
        return SentimentResult(manipulation_score=0.0, detected_techniques=[])
        
    # Use a prompt: "Analyze this text for emotional manipulation, fear-mongering,
    # or deliberate framing bias. Return JSON: {manipulation_score: 0-1, techniques: []}"
    
    # [MOCK]
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "system", "content": "Analyze this text for emotional manipulation, fear-mongering, or deliberate framing bias. Return JSON: {\"manipulation_score\": 0.5, \"techniques\": [\"fear-mongering\"]}"},
    #         {"role": "user", "content": text}
    #     ]
    # )
    # res_json = json.loads(response.choices[0].message.content)
    # score = res_json.get("manipulation_score", 0.0)
    # techniques = res_json.get("techniques", [])
    
    score = 0.2
    techniques = ["mocked_technique"]
    
    return SentimentResult(
        manipulation_score=score,
        detected_techniques=techniques
    )
