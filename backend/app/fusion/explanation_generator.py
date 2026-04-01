import os
# [MOCK] from openai import OpenAI

def generate_explanation(fusion_result: dict, all_flags: list[str], fact_check_results: list[dict]) -> str:
    # Build a structured prompt:
    # "You are a forensic AI analyst. Generate a concise 3-sentence explanation
    #  of why this media received an authenticity score of {score}/100.
    #  Key findings: {bulleted list of all raised flags}.
    #  Be specific and technical. Do not use hedging language."
    
    score = fusion_result.get('authenticity_score', 0)
    flags_list = "\n- ".join(all_flags) if all_flags else "None"
    
    prompt = f"""You are a forensic AI analyst. Generate a concise 3-sentence explanation
of why this media received an authenticity score of {score}/100.
Key findings: 
- {flags_list}

Be specific and technical. Do not use hedging language."""

    # [MOCK API CALL]
    # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ],
    #     max_tokens=200
    # )
    # return response.choices[0].message.content
    
    # Example response
    return f"This media scored {score}/100 due to detected anomalies. The specific findings include {len(all_flags)} red flags. Further manual verification is advised."
