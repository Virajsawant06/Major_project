import json
import os
from openai import OpenAI
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from src.config import manager as cfg
from src.intelligence.models import CHAT_MODEL

console = Console()

def interactive_chat(scan_dir):
    """Start an interactive session with AI about a specific scan."""
    findings_file = scan_dir / "findings.json"
    if not findings_file.exists():
        console.print("[red]Findings file missing.[/red]")
        return
        
    with open(findings_file, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
        
    # Prepare context
    findings = scan_data.get("findings", [])
    vulns = [f for f in findings if "vuln_type" in f]
    context = json.dumps(vulns[:20]) # Limit context
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Missing OPENROUTER_API_KEY.[/red]")
        return
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    history_file = cfg.SENTINEL_HOME / ".chat_history"
    session = PromptSession(history=FileHistory(str(history_file)))
    
    messages = [
        {"role": "system", "content": f"You are Sentinel AI, a cybersecurity assistant. You are chatting about this scan of {scan_data.get('target_url')}. Findings context: {context}"},
        {"role": "assistant", "content": "Hello! I've analyzed the scan results. What would you like to know about these vulnerabilities or how to fix them?"}
    ]
    
    console.print(Panel(f"[bold green]Sentinel AI Chat Mode[/bold green]\nTarget: {scan_data.get('target_url')}\nType 'exit' or 'quit' to return to shell.", border_style="green"))
    console.print(f"\n[bold cyan]AI:[/bold cyan] {messages[-1]['content']}")
    
    while True:
        try:
            user_input = session.prompt("\n[bold white]You:[/bold white] ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue
                
            messages.append({"role": "user", "content": user_input})
            
            with console.status("[bold cyan]AI is thinking...[/bold cyan]"):
                response = client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=messages,
                    temperature=0.7
                )
                ai_msg = response.choices[0].message.content
                
            messages.append({"role": "assistant", "content": ai_msg})
            console.print(f"\n[bold cyan]AI:[/bold cyan]")
            console.print(Markdown(ai_msg))
            
        except KeyboardInterrupt:
            continue
        except Exception as e:
            console.print(f"[red]Chat Error: {e}[/red]")
            break
