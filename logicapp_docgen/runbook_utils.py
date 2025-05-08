import os
import re

def extract_runbook_label(ps1_path: str, runbook_name: str) -> str:
    if not os.path.exists(ps1_path):
        return f"{runbook_name} Runbook"

    with open(ps1_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    matched_steps = []

    # Step 1: Capture all lines like '# Step 1: Do Something'
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            match = re.match(r"#\s*Step\s*\d+:\s*(.+)", stripped, re.IGNORECASE)
            if match:
                matched_steps.append(match.group(1).strip())

    matched_steps = list(dict.fromkeys(matched_steps))  # deduplicate

    # Step 2: If less than 5 steps, pad with PowerShell cmdlets (Connect-, Get-, etc.)
    if len(matched_steps) < 5:
        keywords = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if any(cmd in stripped for cmd in ["Connect-", "Get-", "Set-", "Remove-", "Invoke-", "Add-"]):
                cmd = re.findall(r"(\b(?:Connect|Get|Set|Remove|Invoke|Add)-[A-Za-z0-9]+)", stripped)
                if cmd:
                    keywords.extend(cmd)
        fallback_cmdlets = list(dict.fromkeys(keywords))
        for cmd in fallback_cmdlets:
            if cmd not in matched_steps:
                matched_steps.append(cmd)
            if len(matched_steps) >= 5:
                break

    if not matched_steps:
        return f"{runbook_name} Runbook"

    return f"{runbook_name} Runbook\n" + "\n".join(matched_steps)
