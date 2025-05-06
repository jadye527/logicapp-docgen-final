
def build_logic_app_flow_dot(workflow_structure, run_after):
    # Cluster and node assignment based on ARM roles (dynamically mapped)
    cluster_definitions = {
        "cluster_lifecycle": {
            "label": "Lifecycle Workflow",
            "color": "#3399ff",
            "style": "dashed",
            "nodes": [],
        },
        "cluster_logicapp": {
            "label": "Azure Logic App",
            "color": "#666666",
            "style": "dashed",
            "nodes": [],
        },
        "cluster_automation": {
            "label": "Azure Automation (via Logic App)",
            "color": "#00cc44",
            "style": "dashed",
            "nodes": [],
        },
        "cluster_o365": {
            "label": "Error Handling & O365 Email",
            "color": "#cc0000",
            "style": "dashed",
            "nodes": [],
        }
    }

    node_styles = {
        "Start": ("Lifecycle Workflow\nInitiates Logic App", "box", "#e6f2ff", "cluster_lifecycle"),
        "FailureCallback": ("HTTP POST\nFailure Callback", "box", "#ffcccc", "cluster_lifecycle"),
        "SuccessCallback": ("HTTP POST\nSuccess Callback", "box", "#ccffcc", "cluster_lifecycle"),
        "HTTPTrigger": ("Manual Trigger\nHTTP Request", "box", "#d0e0f0", "cluster_logicapp"),
        "ParseJSON": ("Parse JSON Result", "box", "#ffedcc", "cluster_logicapp"),
        "Condition": ("Delegation Successful?", "diamond", "#ffeeee", "cluster_logicapp"),
        "CreateJob": ("Create Job\nAzure Automation", "box", "#b3e6b3", "cluster_automation"),
        "Runbook": ("DelegateMailbox Runbook\nCheck mailbox\nDelegate to manager\nConvert to shared", "box", "#e6ccff", "cluster_automation"),
        "GetStatus": ("Get Job Status\nHTTP GET", "box", "#b3e6b3", "cluster_automation"),
        "ComposeEmail": ("Compose_1\nHTML Email Body", "box", "#fff2cc", "cluster_o365"),
        "SendEmail": ("Send Email\nOffice 365 Shared Mailbox", "box", "#ffd699", "cluster_o365"),
    }

    # Assign nodes to clusters
    for node_id, (label, shape, fill, cluster_key) in node_styles.items():
        line = f'{node_id} [label="{label}", shape={shape}, fillcolor="{fill}"]'
        cluster_definitions[cluster_key]["nodes"].append(line)

    # DOT header
    dot = [
        "digraph LogicAppFlow {",
        '    compound=true fontname="Segoe UI" fontsize=11 rankdir=TB',
        '    node [fontname="Segoe UI" fontsize=10 shape=box style=filled]'
    ]

    # Add clusters and nodes
    for cid, cdata in cluster_definitions.items():
        dot.append(f'    subgraph {cid} {{')
        dot.append(f'        color="{cdata["color"]}" fontcolor=black label="{cdata["label"]}" style={cdata["style"]}')
        for node_line in cdata["nodes"]:
            dot.append(f"        {node_line}")
        dot.append("    }")

    # Edges with labels for condition flow
    edges = [
        ("Start", "HTTPTrigger", None),
        ("HTTPTrigger", "CreateJob", None),
        ("CreateJob", "Runbook", None),
        ("Runbook", "GetStatus", None),
        ("GetStatus", "ParseJSON", None),
        ("ParseJSON", "Condition", None),
        ("Condition", "ComposeEmail", "Failure"),
        ("ComposeEmail", "SendEmail", None),
        ("SendEmail", "FailureCallback", None),
        ("Condition", "SuccessCallback", "Success")
    ]

    for src, dst, label in edges:
        if label:
            dot.append(f'    {src} -> {dst} [label={label}]')
        else:
            dot.append(f'    {src} -> {dst}')

    dot.append("}")
    return "\n".join(dot)
