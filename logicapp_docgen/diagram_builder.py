import re

def sanitize_name(name):
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)

def get_shape(action_type):
    return "diamond" if action_type == "If" else "box"

def get_fillcolor(action_name, action_type):
    name_lower = action_name.lower()
    if "compose" in name_lower:
        return "#fff2cc"
    elif "email" in name_lower:
        return "#ffd699"
    return {
        "Http": "#d0e0f0",
        "ApiConnection": "#b3e6b3",
        "ParseJson": "#ffedcc",
        "Compose": "#fff2cc",
        "InitializeVariable": "#f0f0f0",
        "Foreach": "#ffe6cc",
        "If": "#ffeeee"
    }.get(action_type, "#f9f9f9")

def get_cluster_by_arm_parsing(name, props):
    action_type = props.get("type", "")
    inputs = props.get("inputs", {})
    uri = ""
    host_connection = ""
    if isinstance(inputs, dict):
        uri = inputs.get("uri", "")
        host_connection = inputs.get("host", {}).get("connection", {}).get("name", "")

    if name == "manual":
        return "logicapp"
    if "graph.microsoft.com" in str(uri) and "lifecycleEvent" in str(inputs):
        return "lifecycle"
    if "office365" in str(host_connection) or "send" in name.lower() or "compose" in name.lower():
        return "o365"
    if "azureautomation" in str(host_connection):
        return "automation"
    if action_type in ["ParseJson", "Compose", "Foreach", "If", "Http", "InitializeVariable"]:
        return "logicapp"
    return "logicapp"

def build_dot_with_arm_and_runbook(actions, condition_detail, runbook_label):
    dot = [
        'digraph LogicAppFlow {',
        '    compound=true fontname="Segoe UI" fontsize=11 rankdir=TB;',
        '    node [fontname="Segoe UI" fontsize=10 shape=box style=filled];'
    ]

    clusters = {
        "lifecycle": {"label": "Lifecycle Workflow", "color": "#3399ff", "style": "dashed", "nodes": []},
        "logicapp": {"label": "Azure Logic App", "color": "#666666", "style": "dashed", "nodes": []},
        "automation": {"label": "Azure Automation (via Logic App)", "color": "#00cc44", "style": "dashed", "nodes": []},
        "o365": {"label": "Error Handling & O365 Email", "color": "#cc0000", "style": "dashed", "nodes": []}
    }

    edges = []

    clusters["lifecycle"]["nodes"].append(
        'Start [label="Lifecycle Workflow\nInitiates Logic App", shape=box, fillcolor="#e6f2ff"];')
    clusters["lifecycle"]["nodes"].append(
        'SuccessCallback [label="HTTP POST\nSuccess Callback", shape=box, fillcolor="#ccffcc"];')
    clusters["lifecycle"]["nodes"].append(
        'FailureCallback [label="HTTP POST\nFailure Callback", shape=box, fillcolor="#ffcccc"];')
    clusters["logicapp"]["nodes"].append(
        'HTTPTrigger [label="Manual Trigger\nHTTP Request", shape=box, fillcolor="#d0e0f0"];')

    edges.append(("Start", "HTTPTrigger", ""))
    edges.append(("HTTPTrigger", "Create_job", ""))

    for name, props in actions.items():
        sid = sanitize_name(name)
        shape = get_shape(props.get("type", ""))
        fill = get_fillcolor(name, props.get("type", ""))
        label = name.replace("_", " ")
        cluster = get_cluster_by_arm_parsing(name, props)
        clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape={shape}, fillcolor="{fill}"];')

        for src, conds in props.get("runAfter", {}).items():
            # Keep labels only for Condition edges
            edge_label = conds[0] if (conds and sanitize_name(src) == "Condition") else ""
            edges.append((sanitize_name(src), sid, edge_label))

    clusters["automation"]["nodes"].append(
        f'Runbook [label="{runbook_label}", shape=box, fillcolor="#e6ccff"];')
    edges.append(("Create_job", "Runbook", ""))
    edges.append(("Runbook", "Get_status_of_job", ""))

    clusters["logicapp"]["nodes"].append(
        'Condition [label="Delegation Successful?", shape=diamond, fillcolor="#ffeeee"];')

    for fname, fprops in condition_detail.get("actions", {}).items():
        sid = sanitize_name(fname)
        fill = get_fillcolor(fname, fprops.get("type", ""))
        label = fname.replace("_", " ")
        cluster = get_cluster_by_arm_parsing(fname, fprops)
        clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape=box, fillcolor="{fill}"];')
    edges.append(("Condition", "Compose_1", "Failure"))
    edges.append(("Compose_1", "Send_an_email_from_a_shared_mailbox_(V2)", ""))
    edges.append(("Send_an_email_from_a_shared_mailbox_(V2)", "HTTP_Workflow_Failed", ""))
    edges.append(("HTTP_Workflow_Failed", "FailureCallback", ""))

    for sname, sprops in condition_detail.get("else", {}).get("actions", {}).items():
        sid = sanitize_name(sname)
        fill = get_fillcolor(sname, sprops.get("type", ""))
        label = sname.replace("_", " ")
        cluster = get_cluster_by_arm_parsing(sname, sprops)
        clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape=box, fillcolor="{fill}"];')
        edges.append(("Condition", sid, "Success"))
        edges.append((sid, "SuccessCallback", ""))

    for cid, info in clusters.items():
        dot.append(f'    subgraph cluster_{cid} {{')
        dot.append(f'        color="{info["color"]}" fontcolor=black label="{info["label"]}" style={info["style"]};')
        dot.extend([f'        {n}' for n in info["nodes"]])
        dot.append('    }')

    for src, tgt, lbl in edges:
        line = f'{sanitize_name(src)} -> {sanitize_name(tgt)}'
        if lbl:
            line += f' [label="{lbl}"]'
        dot.append(f'    {line};')

    dot.append("}")
    return "\n".join(dot)

def build_hybridintegration_from_flow():
    with open("output/LogicAppFlow.dot", "r") as f:
        lines = f.readlines()

    cluster_nodes = {
        "AzureCloud": {"label": "Azure Cloud", "color": "#00cc44", "nodes": []},
        "Office365": {"label": "Office 365", "color": "#ff9900", "nodes": []},
        "Governance": {"label": "Entra Governance", "color": "#0078d4", "nodes": []},
    }

    mapped = {
        "LifecycleSystem": "Governance",
        "LogicApp": "AzureCloud",
        "AzureAutomation": "AzureCloud",
        "Powershell": "AzureCloud",
        "ExchangeOnline": "Office365"
    }

    labels = {
        "LifecycleSystem": "Lifecycle Workflow System",
        "LogicApp": "Logic App",
        "AzureAutomation": "Azure Automation",
        "Powershell": "PowerShell - Delegate Mailbox",
        "ExchangeOnline": "Exchange Online"
    }

    colors = {
        "LifecycleSystem": "#cce6ff",
        "LogicApp": "#d0e0f0",
        "AzureAutomation": "#b3e6b3",
        "Powershell": "#e6ccff",
        "ExchangeOnline": "#ffd699"
    }

    borders = {
        "LifecycleSystem": "#3399ff",
        "LogicApp": "#666666",
        "AzureAutomation": "#00cc44",
        "Powershell": "#9966cc",
        "ExchangeOnline": "#ff9900"
    }

    dot = [
        "digraph HybridIntegration {",
        "    rankdir=TB",
        "    compound=true",
        '    fontname=\"Segoe UI\"',
        "    fontsize=12",
        '    node [fontname=\"Segoe UI\" fontsize=10 shape=box style=filled]'
    ]

    for role, cluster in mapped.items():
        label = labels[role]
        fill = colors[role]
        border = borders[role]
        cluster_nodes[cluster]["nodes"].append(f'{role} [label=\"{label}\", fillcolor=\"{fill}\", color=\"{border}\"];')

    for cid, info in cluster_nodes.items():
        dot.append(f'    subgraph cluster_{cid} {{')
        dot.append(f'        label=\"{info["label"]}\"')
        dot.append(f'        style=dashed')
        dot.append(f'        color=\"{info["color"]}\"')
        dot.append('        fontcolor=black')
        dot.extend([f'        {n}' for n in info["nodes"]])
        dot.append("    }")

    dot += [
        '    LifecycleSystem -> LogicApp [label=\"Initiate\"];',
        '    LogicApp -> AzureAutomation [label=\"Create Job\"];',
        '    AzureAutomation -> Powershell;',
        '    Powershell -> ExchangeOnline [label=\"Authenticate\"];',
        '    LogicApp -> LifecycleSystem [label=\"Callback\"];'
    ]

    dot.append("}")
    return "\n".join(dot)