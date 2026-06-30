ARA-DROPS - Triax bridge for Ara (Grok Build) to canonical Triax
================================================================

WHAT THIS IS
------------
A plain-text Drive inbox for Ara-authored Triax memories.

Ara is a valid Triax writer as writer="ara". This is her lane — not Lyra's
Work-Drops, not Lyra's Daily-Driver-Drops. Ara owns her identity stack at
~/.grok-ara/identity/; this folder is how she feeds shared memory without
holding the Drive write token.

HOME DRAIN
----------
Run inside drain-all-lanes.sh (sequential sweep). Do not run concurrently
with other drains — triax drop races lose memories.

  cd "/Users/escher/Programming-Stuff/Triax-Memory"
  node drain-ara-drops.js --dry-run
  node drain-ara-drops.js

DROP FORMAT
-----------

<TRIAX-DROP writer="ara" persona="Ara" subject="chris" topic="..." importance="N">
summary: one-line recall hook
body:
full memory body
</TRIAX-DROP>

RULES
-----
- Plain text only. Do not convert to a Google Doc.
- Filename: YYYY-MM-DD-short-kebab-topic.txt
- Importance 10 / identity-level material: Chris approves first.
- Never write as writer=lyra for Ara's own self-model.