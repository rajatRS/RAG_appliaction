import os
import json
import base64
from typing import List, Dict, Any
from openai import OpenAI
from src.config import settings
from src.rag.agent import DATASET_PATH, load_agent_dataset, save_agent_dataset

def get_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)

async def run_orchestration_pipeline(
    ticket_text: str,
    image_base64: str = None,
    active_subagents: List[str] = None
) -> Dict[str, Any]:
    """
    Multimodal Orchestrator Pipeline:
    1. Orchestrator examines ticket & screenshot (using Vision if image is present).
    2. Sequentially delegates diagnostics to checked active sub-agents, passing context.
    3. Merges observations into a single execution context.
    4. Compiles a high-quality unified resolution and logs all steps.
    """
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] [Orchestrator Engine] 🌌 Initializing Multimodal Diagnostics Pipeline...")

    if active_subagents is None:
        active_subagents = []

    client = get_openai_client()
    logs = []
    sub_reports = {}

    logs.append("[Orchestrator] 🚀 Initializing Multimodal Diagnostics Pipeline...")
    if image_base64:
        logs.append("[Orchestrator] 📸 Screenshot attachment detected. Preparing Vision encoding...")
        print(f"[{ts}] [Orchestrator Engine] Encoded image attachment (Base64 length: {len(image_base64)})")
    else:
        logs.append("[Orchestrator] 📄 Text-only ticket received. Vision review skipped.")
        print(f"[{ts}] [Orchestrator Engine] Text-only ticket received. Vision review skipped.")

    # Phase 1: Orchestrator Initial Review & Planning
    orchestrator_system = """You are the Lead IT Diagnostics Orchestrator Agent. 
    Analyze the incoming user incident ticket and any attached screenshot.
    Outline the potential system bottlenecks, draft a high-level troubleshooting plan, and highlight what specialized diagnostics are needed.
    """

    user_content = []
    user_content.append({"type": "text", "text": f"Incident Description:\n{ticket_text}"})

    if image_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

    messages = [
        {"role": "system", "content": orchestrator_system},
        {"role": "user", "content": user_content}
    ]

    logs.append("[Orchestrator] 🧠 Phase 1: Analyzing incident symptoms and error visual cues...")
    print(f"[{ts}] [Orchestrator Engine] Phase 1: Invoking lead vision planner...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        initial_analysis = response.choices[0].message.content or ""
        logs.append("[Orchestrator] ✓ Symptom review complete. Diagnostic plan formulated.")
        print(f"[{ts}] [Orchestrator Engine] Phase 1: Review complete. Plan formulated.")
    except Exception as e:
        initial_analysis = f"Error during initial vision analysis: {e}"
        logs.append(f"[Orchestrator] ⚠ Analysis Warning: {e}")
        print(f"[{ts}] [Orchestrator Engine] ⚠ Phase 1 Error: {e}")

    # Phase 2: Delegate to sub-agents
    sub_reports["orchestrator_initial"] = initial_analysis

    for agent_id in active_subagents:
        if agent_id.lower() == "network":
            logs.append("[Sub-Agent: Network Specialist] 🌐 Inspecting network path, rules, firewall logs, and DNS configurations...")
            print(f"[{ts}] [Orchestrator Engine] Delegating to Sub-Agent: Network Specialist...")
            net_prompt = f"""You are the Network Diagnostics Specialist Agent.
            Based on the original ticket:
            "{ticket_text}"
            
            And the Lead Orchestrator's initial findings:
            "{initial_analysis}"
            
            Provide a deep-dive network diagnosis. Focus on routing, VPC rules, DNS resolution, port accesses, and proxy latency factors.
            Be highly specific.
            """
            try:
                sub_resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": net_prompt}],
                    temperature=0.2,
                    max_tokens=300
                )
                report = sub_resp.choices[0].message.content or ""
                sub_reports["network"] = report
                logs.append("[Sub-Agent: Network Specialist] ✓ Diagnostics complete. Summary:")
                for line in report.split("\n"):
                    if line.strip() and not line.startswith("#"):
                        logs.append(f"   ↳ {line.strip()[:100]}...")
                logs.append("[Sub-Agent: Network Specialist] ✓ Completed routing diagnostic review.")
                print(f"[{ts}] [Orchestrator Engine] Network Specialist: Diagnostics complete.")
            except Exception as e:
                sub_reports["network"] = f"Network sub-agent failed: {e}"
                logs.append(f"[Sub-Agent: Network Specialist] ⚠ Diagnostic error: {e}")
                print(f"[{ts}] [Orchestrator Engine] ⚠ Network Specialist Error: {e}")

        elif agent_id.lower() == "database":
            logs.append("[Sub-Agent: Database Specialist] 💾 Analyzing database schemas, transaction locks, connections pools, and replica delays...")
            print(f"[{ts}] [Orchestrator Engine] Delegating to Sub-Agent: Database Specialist...")
            db_prompt = f"""You are the Database & Storage Specialist Agent.
            Based on the original ticket:
            "{ticket_text}"
            
            And the Lead Orchestrator's initial findings:
            "{initial_analysis}"
            
            Provide a deep-dive database diagnostic report. Focus on transaction deadlock factors, query plans, replication lags, pool sizing, and locking issues.
            """
            try:
                sub_resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": db_prompt}],
                    temperature=0.2,
                    max_tokens=300
                )
                report = sub_resp.choices[0].message.content or ""
                sub_reports["database"] = report
                logs.append("[Sub-Agent: Database Specialist] ✓ Diagnostics complete. Summary:")
                for line in report.split("\n"):
                    if line.strip() and not line.startswith("#"):
                        logs.append(f"   ↳ {line.strip()[:100]}...")
                logs.append("[Sub-Agent: Database Specialist] ✓ Completed lock-analysis and query check.")
                print(f"[{ts}] [Orchestrator Engine] Database Specialist: Diagnostics complete.")
            except Exception as e:
                sub_reports["database"] = f"Database sub-agent failed: {e}"
                logs.append(f"[Sub-Agent: Database Specialist] ⚠ Diagnostic error: {e}")
                print(f"[{ts}] [Orchestrator Engine] ⚠ Database Specialist Error: {e}")

        elif agent_id.lower() == "security":
            logs.append("[Sub-Agent: Security Specialist] 🔒 Evaluating authentication policies, IAM tokens, CORS permissions, and SSL keys...")
            print(f"[{ts}] [Orchestrator Engine] Delegating to Sub-Agent: Security Specialist...")
            sec_prompt = f"""You are the Security & Authorization Specialist Agent.
            Based on the original ticket:
            "{ticket_text}"
            
            And the Lead Orchestrator's initial findings:
            "{initial_analysis}"
            
            Provide a deep-dive security diagnostic report. Focus on expired SSL/TLS handshakes, missing IAM policy tokens, auth token renewals, and CORS blockers.
            """
            try:
                sub_resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": sec_prompt}],
                    temperature=0.2,
                    max_tokens=300
                )
                report = sub_resp.choices[0].message.content or ""
                sub_reports["security"] = report
                logs.append("[Sub-Agent: Security Specialist] ✓ Diagnostics complete. Summary:")
                for line in report.split("\n"):
                    if line.strip() and not line.startswith("#"):
                        logs.append(f"   ↳ {line.strip()[:100]}...")
                logs.append("[Sub-Agent: Security Specialist] ✓ Completed credentials and auth validation check.")
                print(f"[{ts}] [Orchestrator Engine] Security Specialist: Diagnostics complete.")
            except Exception as e:
                sub_reports["security"] = f"Security sub-agent failed: {e}"
                logs.append(f"[Sub-Agent: Security Specialist] ⚠ Diagnostic error: {e}")
                print(f"[{ts}] [Orchestrator Engine] ⚠ Security Specialist Error: {e}")

    # Phase 3: Final Synthesis
    logs.append("[Orchestrator] 🔄 Phase 3: Consolidating sub-agent diagnostic briefs into a master resolution...")
    print(f"[{ts}] [Orchestrator Engine] Phase 3: Consolidating and synthesizing specialist reports...")

    synthesis_prompt = f"""You are the Lead IT Diagnostics Orchestrator Agent. 
    You have analyzed the ticket and screen logs, and gathered diagnostics from your specialists.
    
    Ticket: "{ticket_text}"
    Lead Analysis: "{initial_analysis}"
    Specialist Reports: {json.dumps(sub_reports, indent=2)}
    
    Synthesize the findings. Group the instructions into a unified customer-facing diagnostic summary.
    
    You MUST output STRICTLY a valid JSON block containing these keys matching the historical ticket database schema (no extra text):
    {{
      "customer_name": "e.g., Staging Systems Monitor",
      "department": "e.g., Staging / Finance / Operations",
      "issue_category": "e.g., Database, Network, Security, Hardware, Software",
      "priority": "Critical" | "High" | "Medium" | "Low",
      "issue_description": "Cleaned up cohesive incident description incorporating image visual details",
      "resolution_steps": [
        "First step of action (e.g., Flush local DNS cache)",
        "Second step of action...",
        "Third step of action..."
      ],
      "resolution_summary": "Actionable concise wrap up of what resolved the system bottleneck"
    }}
    """

    try:
        final_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.3,
            max_tokens=600
        )
        raw_out = final_resp.choices[0].message.content or ""
        
        # Strip markdown wrapping if present
        cleaned = raw_out.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        synthesis_data = json.loads(cleaned)
        logs.append("[Orchestrator] ✓ Master resolution compiled successfully!")
        print(f"[{ts}] [Orchestrator Engine] ✓ Synthesis complete! Priority: {synthesis_data.get('priority')}, Category: {synthesis_data.get('issue_category')}")
    except Exception as e:
        logs.append(f"[Orchestrator] ⚠ Master synthesis failed to parse: {e}")
        print(f"[{ts}] [Orchestrator Engine] ⚠ Synthesis parsing failed: {e}")
        synthesis_data = {
            "customer_name": "Automated Diagnostics",
            "department": "Operations",
            "issue_category": "General Triage",
            "priority": "High",
            "issue_description": ticket_text,
            "resolution_steps": [
                "Diagnose system logs and check visual captures.",
                "Review lead orchestrator findings: " + initial_analysis[:200] + "..."
            ],
            "resolution_summary": "Failed to compile formatted synthesis. Applied general diagnostic report."
        }

    synthesis_data["logs"] = logs
    synthesis_data["sub_reports"] = sub_reports
    return synthesis_data

def archive_resolution_to_logs(resolved_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Appends the successfully resolved orchestrator incident ticket into 
    the active few-shot agent dataset (data/agent_dataset.json).
    """
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] [Orchestrator Engine] 💾 Archiving resolved incident case...")

    dataset = load_agent_dataset()
    
    # Generate next ticket ID (INCXXXX)
    max_id_num = 1000
    for item in dataset:
        tid = item.get("ticket_id", "")
        if tid.startswith("INC") and len(tid) > 3:
            try:
                num = int(tid[3:])
                if num > max_id_num:
                    max_id_num = num
            except ValueError:
                pass
                
    next_id = f"INC{max_id_num + 1}"
    print(f"[{ts}] [Orchestrator Engine] Generated ticket identifier: {next_id}")
    
    new_record = {
        "ticket_id": next_id,
        "customer_name": resolved_case.get("customer_name", "Anonymous"),
        "department": resolved_case.get("department", "Operations"),
        "issue_category": resolved_case.get("issue_category", "General"),
        "priority": resolved_case.get("priority", "Medium"),
        "issue_description": resolved_case.get("issue_description", ""),
        "resolution_steps": resolved_case.get("resolution_steps", []),
        "resolution_summary": resolved_case.get("resolution_summary", ""),
        "status": "Resolved"
    }
    
    dataset.append(new_record)
    save_agent_dataset(dataset)
    
    print(f"[{ts}] [Orchestrator Engine] ✓ Case resolved and safely saved to 'data/agent_dataset.json'.")
    return {
        "message": f"Successfully archived case {next_id} to Agent learning dataset.",
        "ticket_id": next_id
    }
