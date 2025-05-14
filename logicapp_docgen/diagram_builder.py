import re,os

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
    name_lower = name.lower()
    inputs = props.get("inputs", {})
    uri = inputs.get("uri", "") if isinstance(inputs, dict) else ""
    body = inputs.get("body", {}) if isinstance(inputs, dict) else {}

    # Try to extract host connection name if available
    connection_name = ""
    if isinstance(inputs, dict):
        host = inputs.get("host", {})
        if isinstance(host, dict):
            connection = host.get("connection", {})
            if isinstance(connection, dict):
                connection_name = connection.get("name", "").lower()

    # Priority: connection name
    if "office365" in connection_name or "sharedmailbox" in connection_name:
        return "o365"
    if "azureautomation" in connection_name or "automation" in connection_name:
        return "automation"
    if "graph" in connection_name:
        return "graph"

    # Secondary: uri pattern
    if "graph.microsoft.com" in uri:
        return "graph"

    # Lifecycle-specific callback targets only
    if name_lower in ["successcallback", "failurecallback"] or "lifecyclecallback" in name_lower:
        return "lifecycle"

    # Fallback on action name pattern
    if "sendemail" in name_lower or "sharedmailbox" in name_lower:
        return "o365"
    if "runbook" in name_lower:
        return "automation"

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
        "o365": {"label": "Error Handling & O365 Email", "color": "#cc0000", "style": "dashed", "nodes": []},
        "graph": {"label": "Microsoft Graph", "color": "#99ccff", "style": "dashed", "nodes": []}
    }

    edges = []

    for name, props in actions.items():
        cluster = get_cluster_by_arm_parsing(name, props)
        if cluster not in clusters:
            clusters[cluster] = {
                "label": cluster.capitalize(),
                "color": "#cccccc",
                "style": "dashed",
                "nodes": []
            }

        sid = sanitize_name(name)
        shape = get_shape(props.get("type", ""))
        fill = get_fillcolor(name, props.get("type", ""))
        label = name.replace("_", " ")
        clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape={shape}, fillcolor="{fill}"];')

        for src, conds in props.get("runAfter", {}).items():
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
        if cluster not in clusters:
            clusters[cluster] = {
                "label": cluster.capitalize(),
                "color": "#cccccc",
                "style": "dashed",
                "nodes": []
            }
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
        if cluster not in clusters:
            clusters[cluster] = {
                "label": cluster.capitalize(),
                "color": "#cccccc",
                "style": "dashed",
                "nodes": []
            }
        clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape=box, fillcolor="{fill}"];')
        edges.append(("Condition", sid, "Success"))
        edges.append((sid, "SuccessCallback", ""))

    clusters["lifecycle"]["nodes"].append(
        'Start [label="Lifecycle Workflow Initiates Logic App", shape=box, fillcolor="#e6f2ff"];')
    clusters["lifecycle"]["nodes"].append(
        'SuccessCallback [label="HTTP POST Success Callback", shape=box, fillcolor="#ccffcc"];')
    clusters["lifecycle"]["nodes"].append(
        'FailureCallback [label="HTTP POST Failure Callback", shape=box, fillcolor="#ffcccc"];')
    clusters["logicapp"]["nodes"].append(
        'HTTPTrigger [label="Manual Trigger HTTP Request", shape=box, fillcolor="#d0e0f0"];')
    edges.append(("Start", "HTTPTrigger", ""))
    edges.append(("HTTPTrigger", "Create_job", ""))

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

def build_simple_dot_from_arm(actions, triggers, condition_detail):
    dot = [
        'digraph LogicAppFlow {',
        '    compound=true fontname="Segoe UI" fontsize=11 rankdir=TB;',
        '    node [fontname="Segoe UI" fontsize=10 shape=box style=filled];'
    ]

    clusters = {
        "lifecycle": {"label": "Lifecycle Workflow", "color": "#3399ff", "style": "dashed", "nodes": []},
        "logicapp": {"label": "Azure Logic App", "color": "#666666", "style": "dashed", "nodes": []},
        "o365": {"label": "Office 365", "color": "#ff9900", "style": "dashed", "nodes": []},
        "graph": {"label": "Microsoft Graph", "color": "#9966cc", "style": "dashed", "nodes": []}
    }

    edges = []
    clusters["lifecycle"]["nodes"].append(
        'Start [label="Lifecycle Workflow\nInitiates Logic App", shape=box, fillcolor="#e6f2ff"];')

    for tname, tprops in triggers.items():
        fill = get_fillcolor(tname, tprops.get("type", ""))
        sid = sanitize_name(tname)
        clusters["logicapp"]["nodes"].append(f'{sid} [label="{tname}", shape=box, fillcolor="{fill}"];')
        edges.append(("Start", sid, ""))

    top_level_actions = [k for k, v in actions.items() if not v.get("runAfter")]
    for tname in triggers:
        for action in top_level_actions:
            edges.append((sanitize_name(tname), sanitize_name(action), ""))

    for name, props in actions.items():
        cluster = get_cluster_by_arm_parsing(name, props)
        if cluster not in clusters:
            clusters[cluster] = {
                "label": cluster.capitalize(),
                "color": "#cccccc",
                "style": "dashed",
                "nodes": []
            }
        sid = sanitize_name(name)
        fill = get_fillcolor(name, props.get("type", ""))
        label = name.replace("_", " ")
        cluster = get_cluster_by_arm_parsing(name, props)
        shape = get_shape(props.get("type", ""))
        clusters.setdefault(cluster, {"label": cluster, "color": "#cccccc", "style": "dashed", "nodes": []})
        clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape={shape}, fillcolor="{fill}"];')

        for src, conds in props.get("runAfter", {}).items():
            edge_label = conds[0] if (conds and sanitize_name(src) == "Condition") else ""
            edges.append((sanitize_name(src), sid, edge_label))

    if "actions" in condition_detail:
        for fname, fprops in list(condition_detail["actions"].items())[:1]:
            sid = sanitize_name(fname)
            fill = get_fillcolor(fname, fprops.get("type", ""))
            label = fname.replace("_", " ")
            shape = get_shape(fprops.get("type", ""))
            cluster = get_cluster_by_arm_parsing(fname, fprops)
            clusters.setdefault(cluster, {"label": cluster, "color": "#cccccc", "style": "dashed", "nodes": []})
            clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape={shape}, fillcolor="{fill}"];')
            edges.append(("Condition", sid, "Failure"))

    if "else" in condition_detail and "actions" in condition_detail["else"]:
        for sname, sprops in list(condition_detail["else"]["actions"].items())[:1]:
            sid = sanitize_name(sname)
            fill = get_fillcolor(sname, sprops.get("type", ""))
            label = sname.replace("_", " ")
            shape = get_shape(sprops.get("type", ""))
            cluster = get_cluster_by_arm_parsing(sname, sprops)
            clusters.setdefault(cluster, {"label": cluster, "color": "#cccccc", "style": "dashed", "nodes": []})
            clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape={shape}, fillcolor="{fill}"];')
            edges.append(("Condition", sid, "Success"))

    for cid, info in clusters.items():
        if info["nodes"]:
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

def render_flow_diagram_from_arm(actions, triggers, condition, runbook_label=None):
    if "Create_job" in actions or "Runbook" in actions:
        return build_dot_with_arm_and_runbook(actions, condition, runbook_label)
    else:
        return build_simple_dot_from_arm(actions, triggers, condition)

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
        '    fontname="Segoe UI"',
        "    fontsize=12",
        '    node [fontname="Segoe UI" fontsize=10 shape=box style=filled]'
    ]

    for role, cluster in mapped.items():
        label = labels[role]
        fill = colors[role]
        border = borders[role]
        cluster_nodes[cluster]["nodes"].append(f'{role} [label="{label}", fillcolor="{fill}", color="{border}"];')

    for cid, info in cluster_nodes.items():
        dot.append(f'    subgraph cluster_{cid} {{')
        dot.append(f'        label="{info["label"]}"')
        dot.append(f'        style=dashed')
        dot.append(f'        color="{info["color"]}"')
        dot.append('        fontcolor=black')
        dot.extend([f'        {n}' for n in info["nodes"]])
        dot.append("    }")

    dot += [
        '    LifecycleSystem -> LogicApp [label="Initiate"];',
        '    LogicApp -> AzureAutomation [label="Create Job"];',
        '    AzureAutomation -> Powershell;',
        '    Powershell -> ExchangeOnline [label="Authenticate"];',
        '    LogicApp -> LifecycleSystem [label="Callback"];'
    ]

    dot.append("}")
    return "\n".join(dot)

# --- Final version of the simple diagram builder ---
def build_simple_dot_from_arm_final(actions, triggers, condition_detail):
    dot = [
        'digraph LogicAppFlow {',
        '    compound=true fontname="Segoe UI" fontsize=11 rankdir=TB;',
        '    node [fontname="Segoe UI" fontsize=10 shape=box style=filled];'
    ]

    clusters = {}
    edges = []
    added_nodes = set()

    trigger_name = next(iter(triggers.keys()), "manual")
    trigger_sid = sanitize_name(trigger_name)

    # Inject Start and Trigger
    clusters.setdefault("lifecycle", {
        "label": "Lifecycle Workflow", "color": "#3399ff", "style": "dashed", "nodes": []
    })
    clusters.setdefault("logicapp", {
        "label": "Azure Logic App", "color": "#666666", "style": "dashed", "nodes": []
    })

    clusters["lifecycle"]["nodes"].append(
        'Start [label="Lifecycle Workflow\\nInitiates Logic App", shape=box, fillcolor="#e6f2ff"];')
    clusters["logicapp"]["nodes"].append(
        f'{trigger_sid} [label="Manual Trigger\\nHTTP Request", shape=box, fillcolor="#d0e0f0"];')
    edges.append(("Start", trigger_sid, ""))

    # Track runAfter map to determine real flow
    run_after_map = {}
    all_nodes = set()

    # Iterate over actions
    for name, props in actions.items():
        cluster = get_cluster_by_arm_parsing(name, props)
        if cluster not in clusters:
            clusters[cluster] = {
                "label": cluster.capitalize(),
                "color": "#cccccc",
                "style": "dashed",
                "nodes": []
            }
        sid = sanitize_name(name)
        action_type = props.get("type", "")
        shape = get_shape(action_type)
        fill = get_fillcolor(name, action_type)

        # Enhanced labels
        label = name.replace("_", " ")
        if action_type == "ParseJson":
            label = "Parse JSON Result"
        elif action_type == "Http":
            method = props.get("inputs", {}).get("method", "").upper()
            label = f"{label}\nHTTP {method}" if method else label
        elif "Compose" in name:
            label = "HTML Email Body"
        elif "Send" in name and "Email" in name:
            label = "Send Email\nOffice 365 Shared Mailbox"

        # Determine cluster
        cluster = get_cluster_by_arm_parsing(name, props)
        clusters.setdefault(cluster, {
            "label": {
                "logicapp": "Azure Logic App",
                "lifecycle": "Lifecycle Workflow",
                "automation": "Azure Automation (via Logic App)",
                "o365": "Error Handling & O365 Email",
                "graph": "Microsoft Graph"
            }.get(cluster, cluster.capitalize()),
            "color": {
                "logicapp": "#666666",
                "lifecycle": "#3399ff",
                "automation": "#00cc44",
                "o365": "#cc0000",
                "graph": "#99ccff"
            }.get(cluster, "#cccccc"),
            "style": "dashed",
            "nodes": []
        })

        clusters[cluster]["nodes"].append(f'{sid} [label="{label}", shape={shape}, fillcolor="{fill}"];')
        all_nodes.add(sid)

        # runAfter edges
        for src, conds in props.get("runAfter", {}).items():
            label = conds[0] if conds and sanitize_name(src) == "Condition" else ""
            edges.append((sanitize_name(src), sid, label))
            run_after_map[sid] = run_after_map.get(sid, set()) | {sanitize_name(src)}

        # Detect lifecycle callback status
        body = props.get("inputs", {}).get("body", {})
        if isinstance(body, dict) and body.get("type") == "lifecycleEvent":
            operation = body.get("data", {}).get("operationStatus", "")
            if operation == "Completed":
                clusters["lifecycle"]["nodes"].append(
                    'SuccessStatus [label="HTTP POST\\nSuccess Callback", shape=box, fillcolor="#ccffcc"];')
                edges.append((sid, "SuccessStatus", ""))
            elif operation == "Failed":
                clusters["lifecycle"]["nodes"].append(
                    'FailureStatus [label="HTTP POST\\nFailure Callback", shape=box, fillcolor="#ffcccc"];')
                edges.append((sid, "FailureStatus", ""))

    # Attach only real entry points to Trigger (no scattered layout)
    for sid in all_nodes:
        if sid not in set(tgt for src, tgt, _ in edges):
            if sid != trigger_sid:
                edges.append((trigger_sid, sid, ""))

    # Emit clusters
    for cid, info in clusters.items():
        dot.append(f'    subgraph cluster_{cid} {{')
        dot.append(f'        color="{info["color"]}" fontcolor=black label="{info["label"]}" style={info["style"]};')
        dot.extend(f'        {n}' for n in info["nodes"])
        dot.append('    }')

    # Emit edges in order
    for src, tgt, lbl in edges:
        line = f'{src} -> {tgt}'
        if lbl:
            line += f' [label="{lbl}"]'
        dot.append(f'    {line};')

    dot.append("}")
    return "\n".join(dot)

def build_hybrid_with_o365_graph(logic_app_name):
    flow_dot_path = f"output/{logic_app_name}_Flow.dot"
    if not os.path.exists(flow_dot_path):
        raise FileNotFoundError(f"Expected flow diagram not found: {flow_dot_path}")

    with open(flow_dot_path, "r") as f:
        dot_text = f.read()

    import re

    # Match the Runbook node and extract the first line of the label after "PowerShell - "
    match = re.search(r'Runbook\s*\[label="(.*?) Runbook\\n', dot_text)
    runbook_filename = match.group(1).strip() + ".ps1" if match else f"{logic_app_name}.ps1"

    services_detected = {
        "LogicApp": "logicapp" in dot_text,
        "AzureAutomation": "automation" in dot_text,
        "Powershell": "Runbook" in dot_text,
        "ExchangeOnline": "o365" in dot_text,
        "MicrosoftGraph": "graph" in dot_text,
        "LifecycleSystem": "lifecycle" in dot_text
    }

    service_map = {
        "LogicApp": ("Logic App", "#d0e0f0", "#666666", "AzureCloud"),
        "AzureAutomation": ("Azure Automation", "#b3e6b3", "#00cc44", "AzureCloud"),
        "Powershell": (runbook_filename, "#e6ccff", "#9966cc", "AzureCloud"),
        "ExchangeOnline": ("Exchange Online", "#ffd699", "#ff9900", "Office365"),
        "MicrosoftGraph": ("Microsoft Graph", "#ccddff", "#9999ff", "AzureCloud"),
        "LifecycleSystem": ("Lifecycle Workflow System", "#cce6ff", "#3399ff", "Governance")
    }

    cluster_nodes = {
        "AzureCloud": {"label": "Azure Cloud", "color": "#00cc44", "nodes": []},
        "Office365": {"label": "Office 365", "color": "#ff9900", "nodes": []},
        "Governance": {"label": "Entra Governance", "color": "#0078d4", "nodes": []},
    }

    for role, present in services_detected.items():
        if present:
            label, fill, border, cluster = service_map[role]
            cluster_nodes[cluster]["nodes"].append(
                f'{role} [label="{label}", fillcolor="{fill}", color="{border}"];'
            )

    edges = []
    if services_detected["LifecycleSystem"] and services_detected["LogicApp"]:
        edges.append(("LifecycleSystem", "LogicApp", ""))
    if services_detected["LogicApp"] and services_detected["AzureAutomation"]:
        edges.append(("LogicApp", "AzureAutomation", "Start Job"))
    if services_detected["AzureAutomation"] and services_detected["Powershell"]:
        edges.append(("AzureAutomation", "Powershell", ""))
    if services_detected["Powershell"] and services_detected["LogicApp"]:
        edges.append(("Powershell", "LogicApp", ""))
    if services_detected["LogicApp"] and services_detected["ExchangeOnline"]:
        edges.append(("LogicApp", "ExchangeOnline", ""))
    if services_detected["LogicApp"] and services_detected["MicrosoftGraph"]:
        edges.append(("LogicApp", "MicrosoftGraph", ""))
    if services_detected["LogicApp"] and services_detected["LifecycleSystem"]:
        edges.append(("LogicApp", "LifecycleSystem", "Completed"))

    dot = [
        "digraph HybridIntegration {",
        "    rankdir=TB",
        "    compound=true",
        '    fontname="Segoe UI"',
        "    fontsize=12",
        '    node [fontname="Segoe UI" fontsize=10 shape=box style=filled]'
    ]

    for cid, info in cluster_nodes.items():
        if info["nodes"]:
            dot.append(f'    subgraph cluster_{cid} {{')
            dot.append(f'        label="{info["label"]}"')
            dot.append(f'        style=dashed')
            dot.append(f'        color="{info["color"]}"')
            dot.append('        fontcolor=black')
            dot.extend([f'        {n}' for n in info["nodes"]])
            dot.append("    }")

    for src, tgt, label in edges:
        line = f'    {src} -> {tgt}'
        if label == "Completed":
            line += f' [label="{label}"]'
        dot.append(line + ";")

    dot.append("}")
    return "\n".join(dot)
