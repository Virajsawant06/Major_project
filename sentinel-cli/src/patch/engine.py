import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PATCH_PROMPT = """
You are an elite Application Security Engineer fixing a web application.
I will provide a JSON report containing vulnerabilities found by a DAST scanner.
Your job is to generate precise, actionable patches for each issue.

If the scan output shows no severe findings, focus on defense-in-depth and the Informational/Low issues.

You MUST output your response strictly as a single JSON object.
The JSON schema MUST exactly match the structure below, but YOU MUST INVENT THE ACTUAL CONTENT based ONLY on the provided scan report.
CRITICAL RULES:
1. Do NOT copy the bracketed placeholder text. Write YOUR OWN analysis for the vulnerabilities found.
2. If the scan report has ZERO findings, you MUST return an empty array `[]` for "issues". Do NOT invent fake issues just to populate the array!

{
  "summary_bottom_line": "[Generate a 1-2 sentence overview of the scan posture]",
  "estimated_total_time": "[Generate estimated fix time, or '0 minutes' if no issues]",
  "issues": [
    // Leave EMPTY [] if no findings are in the report. Otherwise, map each actual finding to this structure:
    {
      "title": "[Insert ACTUAL vulnerability title from the JSON report]",
      "severity": "[HIGH, MEDIUM, or LOW]", 
      "fix_time": "[Generate fix time, e.g. 'Fix in 15 min']",
      "affects_now": "[Specific 2-3 sentence explanation of how this specific finding actively harms the app]",
      "paste_fix": "[Exact code block or command to copy/paste to fix it]"
    }
  ]
}
"""

def generate_patches(scan_file):
    if not os.path.exists(scan_file):
        raise FileNotFoundError(f"Output file not found: {scan_file}")
        
    with open(scan_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
        
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in .env. Cannot use Patch Engine.")
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # We strip down the scan_data to send only what's necessary to Groq to save context tokens
    findings = scan_data.get("findings", [])
    # Limit to top 20 findings to avoid overwhelming prompt
    reduced_payload = [{"vuln": f["vuln_type"], "severity": f["severity"], "desc": f["description"][:200]} for f in findings[:20]]
    
    response = client.chat.completions.create(
        model="qwen/qwen-2.5-coder-32b-instruct:free",
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PATCH_PROMPT},
            {"role": "user", "content": json.dumps(reduced_payload)}
        ]
    )
    
    try:
        content = response.choices[0].message.content
        patch_data = json.loads(content)
        return patch_data, scan_data.get("summary", {})
    except Exception as e:
        raise RuntimeError(f"Failed to parse OpenRouter AI output: {e}\nRaw: {content[:100]}...")
