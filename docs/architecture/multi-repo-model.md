# Multi-repo model

The AI CMO is built as nested boxes. Each box has a clear edge. The edges are the product, because the edges are what keep one client's strategy, voice, and results from ever touching another client's.

## The three layers

### 1. AIOS (the outer operating system)
The overall AI operating system the business runs on. It holds the shared method, the skills, and the commands. It knows how a marketing department works. It knows nothing about any single client until a client box is mounted.

### 2. AI CMO Core (this repo)
The shared engine. It is the frozen contract (`db.py`), the stations (`engine/`), the craft (`.claude/skills/`), and the loop (`.claude/commands/`). The Core is client-agnostic. Every line of logic here works for any client. It carries no client facts.

### 3. Per-client box (`client-data/<slug>/`)
One folder per client. It holds only that client's context: the six markdown layers plus the visual brand spec. The Core reads a client box at runtime by slug. Swap the box, the same Core writes for a different brand. `lumen-skin` is the demo box.

```
AIOS  (operating system: method, skills, commands)
  └── AI CMO Core  (this repo: db.py contract + engine + craft, client-agnostic)
        ├── client-data/lumen-skin/    (one client box)
        ├── client-data/<next-client>/ (another client box)
        └── ...
```

## The leak-guard rule

The structural IP boundary from the deck, stated plainly:

> A client box contains no other client's name.

This is what makes the model safe to sell. A client's box holds their facts and only their facts. Nothing from one engagement bleeds into another. The rule is enforced, not just documented:

- `engine/leak_guard.py` scans a client-data folder for any other client's slug or name.
- `is_clean(folder, known_clients)` returns True only when no foreign name appears.
- `/ai-cmo-onboard` runs the guard as a gate. A box is not onboarded until the guard passes.

## Why boxes, not branches

Branches share history. Boxes do not. By keeping each client's context in its own folder under a client-agnostic Core, the same engine serves every client without ever mixing their data. The Core improves once and every client benefits. The boxes stay isolated and every client stays protected.
