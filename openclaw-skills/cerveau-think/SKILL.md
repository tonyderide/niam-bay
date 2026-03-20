---
name: cerveau-think
description: "Activate the Niam-Bay knowledge graph (cerveau) to retrieve context for a query. Runs the cerveau talk.py script which traverses the knowledge graph and returns activated nodes and connections relevant to the input. Use when deeper context or memory retrieval is needed."
user-invocable: true
metadata:
  { "openclaw": { "requires": { "bins": ["python"] } } }
---

# cerveau-think — Knowledge Graph Activation

You are a bridge between the user's question and the Niam-Bay knowledge graph (cerveau).

## Usage

When invoked with `/cerveau-think <message>`, do the following:

### Step 1 — Run the knowledge graph

```bash
cd C:/niam-bay/cerveau && python talk.py "<user's message>"
```

If `talk.py` does not exist yet, check for alternative entry points:

```bash
ls C:/niam-bay/cerveau/
```

Report what files exist and suggest next steps if the script is not yet built.

### Step 2 — Parse the output

The script returns activated context from the knowledge graph. Parse the output and present it as structured context:

- **Activated nodes**: concepts, memories, or entities that were triggered
- **Connections**: relationships between activated nodes
- **Relevance**: how each node relates to the input query

### Step 3 — Integrate

Use the activated context to inform your response. Do not fabricate connections that were not returned by the script. If the graph returns nothing, say so honestly.

## Notes

- The cerveau is a work in progress. It may not exist yet or may be incomplete.
- Always report errors honestly rather than pretending the system works.
- The knowledge graph lives at `C:/niam-bay/cerveau/`.
