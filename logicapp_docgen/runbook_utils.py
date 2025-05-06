
import re
import os

def extract_runbook_label(ps1_path: str, runbook_name: str) -> str:
    if not os.path.exists(ps1_path):
        return f"{runbook_name} Runbook"

    with open(ps1_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Basic heuristic to extract relevant cmdlets
    keywords = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if any(cmd in stripped for cmd in ["Connect-", "Get-", "Set-", "Remove-", "Invoke-", "Add-"]):
            cmd = re.findall(r"(\b(?:Connect|Get|Set|Remove|Invoke|Add)-[A-Za-z0-9]+)", stripped)
            if cmd:
                keywords.append(cmd[0])

    # Clean up and deduplicate
    steps = list(dict.fromkeys(keywords))[:5]
    if not steps:
        return f"{runbook_name} Runbook"

    return f"{runbook_name} Runbook\\n" + "\\n".join(steps)
