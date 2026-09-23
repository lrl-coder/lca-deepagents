# python/m3/m3.2_homework.py
"""M3.2 Homework: Bundle a Reference File Into Your Skill.

THE IDEA
The lab's two skills (qualify-lead and draft-pitch) are each a single flat
SKILL.md file with everything inline. But the lesson also covered a third
stage of progressive disclosure: a skill can point to supporting files (a
reference doc, a template, a script) that live alongside SKILL.md and that
the agent only reads when it actually needs them, instead of stuffing
everything into the system prompt up front. This homework asks you to write
a skill for a topic or workflow YOU pick (not sales) that bundles a SECOND
file with details the agent needs but that aren't in SKILL.md itself, then
confirm from the trace that the agent actually called `read_file` on that
second file before answering, rather than guessing.

WHAT YOU FILL IN
  TODO 1: write your own SKILL.md content. It must instruct the agent to
    read a `reference.md` file (in the same skill directory) for specific
    details it needs, and must NOT restate those details inline. The `name`
    field in your frontmatter must exactly match SKILL_NAME below.
  TODO 2: write reference.md's content: the specific facts, numbers, or
    template your skill's instructions point to and depend on.
  TODO 3: write a system prompt and a user question that should activate
    your skill.

RUN
  cd python
  uv run ./m3/m3.2_homework.py
"""

import sys
import tempfile
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from models import model

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# This name becomes the skill's directory name. It must exactly match the
# `name:` field you write in the frontmatter inside build_skill_md() below.
SKILL_NAME = "home-cooking"
REFERENCE_PATH = f"/skills/{SKILL_NAME}/reference.md"


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write your own SKILL.md content.
#
# Requirements:
#   - YAML frontmatter with `name` (must equal SKILL_NAME above) and
#     `description` (a specific sentence describing WHEN to use this skill).
#   - Steps that tell the agent to open `reference.md` (in this same skill
#     directory) for the specific details it needs to do the task well.
#   - Do NOT put those details in SKILL.md itself; if the agent could do
#     the task correctly without ever reading reference.md, this doesn't
#     exercise progressive disclosure.
#
# Example shape (delete this and write your own):
#   return """---
#   name: your-skill-name
#   description: Use when the user wants to ...
#   ---
#
#   # Your Skill Title
#
#   **Step 1: ...**: ...
#   **Step 2: ...**: before proceeding, read reference.md in this skill's
#     directory for the exact ... to use. Do not guess these.
#   """
# ════════════════════════════════════════════════════════════════════════

def build_skill_md() -> str:
    """Return the home-cooking skill instructions."""
    return """---
name: home-cooking
description: Use when the user wants a home-cooked recipe or meal plan based on specific ingredients, servings, time, or dietary constraints.
---

# Home Cooking

Turn the user's ingredients and constraints into an executable home-cooking
plan.

## Workflow

1. Identify the dish, serving count, available ingredients, time, equipment,
   and any dietary restrictions already stated by the user.
2. Before giving quantities or cooking steps, call `read_file` on
   `/skills/home-cooking/reference.md`. Use the exact recipe code,
   ingredient amounts, timings, doneness cues, substitutions, and output format
   from that file. Do not guess or silently replace those details.
3. Scale quantities only when the requested serving count differs from the
   reference recipe. State the scaling clearly.
4. Present a concise ingredient list followed by numbered cooking steps. Include
   the reference's safety note when it applies.

If the requested dish is not covered by the reference file, say so and offer
the closest covered dish instead of inventing a house-standard recipe.
"""


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write reference.md's content.
#
# This should contain the specific facts your SKILL.md pointed to and
# depends on: a rubric, a set of numbers, a template, a checklist. Specific
# enough that an answer produced without reading it would visibly differ
# from one produced with it.
# ════════════════════════════════════════════════════════════════════════

def build_reference_md() -> str:
    """Return the exact recipes and response template used by the skill."""
    return """# Home-Cooking Reference

Use these recipes as the house standard. One tablespoon is 15 ml and one
teaspoon is 5 ml.

## HC-TOMATO-02: Tomato and Egg Stir-Fry

Yield: 2 servings. Total time: 15 minutes.

### Ingredients

- Tomatoes: 350 g (about 2 medium), cut into wedges
- Eggs: 3
- Neutral cooking oil: 30 ml (2 tablespoons), divided equally
- Fine salt: 2.5 ml (1/2 teaspoon), divided equally
- Water: 15 ml (1 tablespoon)
- Sugar: 5 ml (1 teaspoon), optional when the tomatoes are tart
- Chopped scallion: 15 ml (1 tablespoon), optional

### Method

1. Beat the eggs with half the salt and the water.
2. Heat 15 ml oil over medium-high heat. Add the eggs and fold for 45-60
   seconds. Remove them while the surface is still slightly glossy.
3. Add the remaining oil, tomatoes, and salt. Cook over medium heat for 2-3
   minutes, until the tomatoes release juice but some wedges keep their shape.
4. Return the eggs, add the optional sugar, and fold for 30-60 seconds. Garnish
   with scallion and serve immediately.

Doneness cue: the eggs are tender with no liquid raw egg, and the sauce lightly
coats the curds. If the sauce is watery, reduce it for 1 minute before returning
the eggs.

Safety note: wash hands and utensils after contact with raw egg, and cook until
no liquid egg remains.

## HC-BROCCOLI-02: Garlic Broccoli

Yield: 2 servings. Total time: 12 minutes.

### Ingredients

- Broccoli: 300 g
- Garlic: 3 cloves, minced
- Neutral cooking oil: 15 ml (1 tablespoon)
- Fine salt: 1.7 ml (1/3 teaspoon)
- Water: 30 ml (2 tablespoons)

### Method

1. Cut the broccoli into similarly sized florets and slice the peeled stem.
2. Blanch in boiling water for 60-90 seconds, until bright green, then drain.
3. Heat the oil over medium heat. Cook the garlic for 15 seconds without
   browning it.
4. Add broccoli, salt, and water. Stir-fry over high heat for 1-2 minutes. It is
   done when a chopstick enters the stem with slight resistance.

## Required response format

Start with: `[recipe code] dish name — servings, total time`.

Then use these headings in order:

1. `Ingredients`
2. `Steps`
3. `Doneness and safety`

## Example

`[HC-TOMATO-02] Tomato and Egg Stir-Fry — 2 servings, 15 minutes`

Under `Ingredients`, list every quantity explicitly. Under `Steps`, preserve
the reference timing and heat level. Under `Doneness and safety`, include the
doneness cue and applicable safety note without adding medical claims.
"""


# Write the skill to a scratch directory so it's discoverable through a
# FilesystemBackend, the same mechanism the lab uses for python/m3/skills/.
_tmp_root = Path(tempfile.mkdtemp(prefix="m3_2_homework_"))
_skill_dir = _tmp_root / "skills" / SKILL_NAME
_skill_dir.mkdir(parents=True, exist_ok=True)
(_skill_dir / "SKILL.md").write_text(build_skill_md(), encoding="utf-8")
(_skill_dir / "reference.md").write_text(build_reference_md(), encoding="utf-8")

backend = FilesystemBackend(root_dir=str(_tmp_root), virtual_mode=True)
print(f"Skill files written to: {_skill_dir}")


# ════════════════════════════════════════════════════════════════════════
# TODO 3: Write a system prompt and a triggering question.
#
# SYSTEM_PROMPT: give the agent a persona of your choosing (a name, a
# voice, anything you want).
# USER_QUESTION: a question that should match your skill's `description`
# closely enough that the agent activates it.
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are Lin, a practical home-cooking assistant. When a
relevant skill is available, follow it exactly and use its reference file
before answering. Keep recipes concise and executable."""
USER_QUESTION = (
    "Use your house-standard recipe to make tomato and egg stir-fry for two. "
    "Include the recipe code, exact quantities, timings, doneness cue, and "
    "food-safety note."
)

agent = create_deep_agent(
    model=model,
    name="Homework_Agent",
    backend=backend,
    skills=["/skills"],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke({"messages": [{"role": "user", "content": USER_QUESTION}]})
print(result["messages"][-1].content)

read_calls = [
    call
    for msg in result["messages"]
    for call in getattr(msg, "tool_calls", [])
    if call["name"] == "read_file"
]
reference_was_read = any(call["args"].get("file_path") == REFERENCE_PATH for call in read_calls)
print(f"\n--- Did the agent read {REFERENCE_PATH}? {reference_was_read} ---")
if not reference_was_read:
    print(
        "It didn't. Either SKILL.md isn't clearly telling it to, or the "
        "task is answerable without the details in reference.md."
    )
