import os
from openai import OpenAI

key = os.getenv("PHYAGI_API_KEY")
model = "sft_16b_phi4_mathv2code5_otcode_oaif_safe_high32_2"
openai = OpenAI(api_key=key, base_url="https://gateway.phyagi.net/api")

inputs = [
    {
        "role": "user",
        "content": "What is the capital of France?"
    }
]

results = openai.chat.completions.create(
    model=model,
    messages=inputs,
    temperature=0.7,
    max_tokens=100,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
)

print(results)
