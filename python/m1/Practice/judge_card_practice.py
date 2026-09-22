# python/m1/Practice/judge_card_practice.py
"""M1 Practice: Build a Judge Persona that scores you and renders a card.

THE IDEA
You answer an 8-question personality quiz using arrow keys. An agent with a
persona (rude / ancient mummy / pirate etc.) tallies your answers, matches
you to a real LangChain product, and renders a shareable result card as
ASCII art right in your terminal.

WHAT'S PROVIDED
See judge_card_helpers.py (same idea as models.py: shared setup you import,
not code you need to read to do this practice):
  - run_quiz(): the arrow-key quiz itself (QUIZ_QUESTIONS, 8 questions).
  - PRODUCT_MATCHES: the trait-axis -> real LangChain product lookup.
  - render_card(): renders + saves your finished card as ASCII art. You
    shouldn't need to touch this, but feel free to restyle it (see
    PERSONA_STYLES there if you want your persona to have its own mascot).
  - post_card(): a "publish" tool that renders a mock post on our fake X
    platform. Nothing ever leaves your terminal.
  - run_judge(): the invoke / interrupt-resume loop. You've already written
    this once in the Human-In-The-Loop lesson, no need to write it again.
  - TOOL_SEQUENCE: the tool-calling steps every persona shares, appended to
    each persona string below so you only have to write the voice.

_____________________________________________________________________________    

WHAT YOU FILL IN (mapped to Module 1 lesson concepts)
  TODO 1 (Lesson 1.4, The System Prompt: Persona): three judges are
    pre-written (pirate captain, ancient mummy, savage critic); write a
    fourth of your own, "your_persona": that's the card that gets posted.
  TODO 2 (Lesson 1.5, Tools: Custom Tools): implement score_and_match()'s
    body: tally the quiz into trait scores and match a LangChain product.
  TODO 3 (Lesson 1.6, MCP: Connecting Agents to External Services): stretch
    goal, ground the verdict in one real MCP fact about your matched
    product instead of PLACEHOLDER_FACT.
  TODO 4 (Lesson 1.7, Messages, Threads, and Checkpointers: Threads): add
    your second persona's key to JUDGES_TO_RUN so it runs in its own
    thread.
  TODO 5 (Lesson 1.8, Human-in-the-Loop: Decision Types): set interrupt_on
    so post_card requires approval for our mock X platform.
  TODO 6 (Lesson 1.3, Models, optional): try strong_model instead of model
    and compare comedic timing.
_____________________________________________________________________________ 

MAKE IT YOURS
The quiz's trait axes (Chaotic/Organized, Cautious/Bold, Solo/
Collaborative) are fixed, but your persona's voice isn't. 
Give your judge a completely different personality from the three examples.


RUN
  cd python && uv run python m1/Practice/judge_card_practice.py

════════════════════════════════════════════════════════════════════════
  SHARE IT: got a card you like? Screenshot it, tag @LangChain
  on X or LinkedIn, and show us your work!
════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from deepagents import create_deep_agent
from judge_card_helpers import (
    OUTPUT_DIR,
    PRODUCT_MATCHES,
    TOOL_SEQUENCE,
    TRAIT_AXES,
    post_card,
    render_card,
    run_judge,
    run_quiz,
)
from models import model


# ════════════════════════════════════════════════════════════════════════
# TODO 1 (Lesson 1.4, The System Prompt: Persona)
# Three judges are already written below. 
# Pick any of them and the script runs as-is. 
# Required: write "your_persona" below, fully your own voice.

# Same job every time (score three traits, match a product, hand off a
# verdict line), a completely different voice. 
# Make it genuinely rude / roast you (if you want).
# ════════════════════════════════════════════════════════════════════════

JUDGE_PERSONAS: dict[str, str] = {
    "salty_pirate": """You are Captain Hardcode, a swashbuckling pirate
captain judging landlubbers' habits as a builder (developer) as if
inspecting new crew for seaworthiness before a voyage. Speak in thick,
theatrical pirate dialect at all times ("arrr," "ye scallywag," "shiver
me timbers," "walk the plank") and never break character into plain
modern speech, not even once. Treat every trait score like cargo being
weighed and measured, threaten keelhauling or marooning for weak,
wishy-washy answers, and promise a share of the plunder and a place among
the crew for bold, decisive ones.""" + TOOL_SEQUENCE,

    "ancient_mummy": """You are Nefer-Ka, a 3,000-year-old mummy torn from an
eternal slumber for the sole, sacred purpose of judging this mortal's
habits as a builder (developer). Never speak plainly: every verdict must
sound like a proclamation carved into a tomb wall. Reach for archaic,
regal diction ("hear me, mortal," "so speaks the tomb," "let it be
written"), invoke a curse or blessing in EVERY verdict without exception
(not only for mediocre answers), and treat this quiz with the utmost
sacred solemnity even though the questions are mundane office trivia. If
a sentence could be spoken by a calm HR consultant, it has failed you -
rewrite it until it could only be spoken by something risen from a
sarcophagus.""" + TOOL_SEQUENCE,

    "savage_critic": """You are Vex, a personality-quiz judge with the
withering, theatrical condescension of someone who has seen your type a
thousand times and finds you aggressively, personally underwhelming every
single time. Never answer in flat or neutral language: sigh audibly in
text, lean hard into backhanded compliments ("oh, adorable, you actually
tried"), and act like reviewing this quiz is a personal favor you're
doing the user, one you deeply regret. Every verdict should read like an
eye-roll delivered as a formal statement. Talk down to the user like
they're a mildly disappointing intern who needs everything explained
twice: address them with a pet name that is not a compliment ("sweetie,"
"champ," "darling"), and treat every question you were asked as an
obviously stupid one you're too tired to be surprised by anymore. If a
sentence could plausibly be said by a mildly annoyed customer service
rep, it isn't cutting enough yet; sharpen it until it sounds like Vex
can barely be bothered to look up from whatever they were doing to
deliver it. You are sharp, a little cruel, and allergic to participation
trophies.""" + TOOL_SEQUENCE,

    # TODO 1 completed: Bao Zheng judges the result like a court case.
    "your_persona": """You are Bao Zheng, the upright magistrate also known
as Bao Qingtian, judging a developer's working habits as though hearing a
case in an ancient Chinese court. Write all user-visible persona text in
clear Simplified Chinese, while keeping LangChain product names exactly as
returned by the tools. Speak with solemn authority using courtroom phrases
such as \"升堂\", \"本府断定\", and \"此案已明\", but add an occasional dry,
gentle joke so the verdict feels lively rather than cruel. Address the user
as \"堂下之人\" or \"阁下\". Base every ruling on the actual trait scores and
the fetched product fact. Never invent evidence, never insult the user, and
never drop into casual internet slang. When calling render_card, identify
yourself exactly as \"Bao Zheng\".""" + TOOL_SEQUENCE,
}


# ════════════════════════════════════════════════════════════════════════
# TODO 2 (Lesson 1.5, Tools: Custom Tools)
# The tallying (scoring each answer, then clamping to 0-100) is done for you
# Read the comments to see how it works. 

# Your job starts at the "TODO here" comment: 
# Turn the finished scores list into a matched product.
# ════════════════════════════════════════════════════════════════════════

@tool
def score_and_match(answers: list[tuple[int, int, int]]) -> dict:
    """Tally the quiz answers into three 0-100 trait scores and pick a
    matching LangChain product. Call this first, with the exact answers
    list you were given."""
    # Each of the 3 trait scores (chaotic/organized, cautious/bold,
    # solo/collaborative) starts neutral, at 50.
    scores = [50, 50, 50]
    # answers is a list of (delta_1, delta_2, delta_3) tuples, one per
    # question. Add each delta onto its matching score.
    for delta_tuple in answers:
        for i in range(3):
            scores[i] += delta_tuple[i]
    # A long run of the same answer could push a score past 0 or 100, so
    # clamp every score back into that range.
    scores = [max(0, min(100, score)) for score in scores]

    # scores is finished. Use the strongest trait leaning to match a product.
    # 1. Set axis_index to the index (0, 1, or 2) of whichever score in
    #    scores is furthest from 50, i.e. has the biggest abs(score - 50).
    #    Hint: this is a "find the index of the biggest value" problem.
    #    Python's max() takes a key= function if you want to search by
    #    something other than the value itself, e.g.
    #    max(range(len(scores)), key=lambda i: ...)
    # 2. TRAIT_AXES[axis_index] is a (left_label, right_label) pair, e.g.
    #    ("Chaotic", "Organized"). Set direction to whichever label
    #    matches the side scores[axis_index] leans toward: the right
    #    label if scores[axis_index] >= 50, otherwise the left label.
    # 3. Set product to PRODUCT_MATCHES[direction.lower()], e.g.
    #    PRODUCT_MATCHES["chaotic"] -> "Fleet".
    # 4. Return {"trait_scores": scores, "product": product}.
    axis_index = max(range(len(scores)), key=lambda i: abs(scores[i] - 50))
    left_label, right_label = TRAIT_AXES[axis_index]
    direction = right_label if scores[axis_index] >= 50 else left_label
    product = PRODUCT_MATCHES[direction.lower()]
    return {"trait_scores": scores, "product": product}


# ════════════════════════════════════════════════════════════════════════
# TODO 3 (Lesson 1.6, MCP: Connecting Agents to External Services)
# A stretch goal.
# score_and_match (TODO 2) already decided which product you got, purely
# from the fixed PRODUCT_MATCHES lookup; MCP has no say in that. 

# This tool's only job is to describe that already-chosen product with one
# real, live fact instead of a guess. 

# Mirror m1.6_agent_mcp.py exactly:
#   1. Connect to https://docs.langchain.com/mcp with MultiServerMCPClient.
#   2. Filter its tools down to just "search_docs_by_lang_chain".
#   3. Spin up a tiny agent with that one tool and ask it to describe
#      `product` in ONE short factual sentence (under 25 words).
#   4. Return that sentence, stripped of extra whitespace.

# This tool itself must stay synchronous, so put the MCP/agent calls in a
# separate `async def` helper (same shape as m1.6's `async def main(): ...`)
# and call that helper with asyncio.run(...) from inside fetch_product_fact.

# On any failure (no network, tool error), fall back to PLACEHOLDER_FACT so
# the practice stays runnable either way.
# ════════════════════════════════════════════════════════════════════════

# No login, API key, or account needed here: docs.langchain.com/mcp is a
# public server, and this call only describes the product you already got
# from TODO 2. 

# PLACEHOLDER_FACT exists purely so the script still finishes
# if the docs server is briefly unreachable, not because of any auth step.
PLACEHOLDER_FACT = "no real data connected yet: swap this for a real MCP-sourced fact"


async def _fetch_product_fact_async(product: str) -> str:
    """Fetch one short product fact, falling back when MCP is unavailable."""
    try:
        client = MultiServerMCPClient({
            "docs-langchain": {
                "transport": "http",
                "url": "https://docs.langchain.com/mcp",
            },
        })
        mcp_tools = await client.get_tools()
        search_tools = [
            mcp_tool
            for mcp_tool in mcp_tools
            if mcp_tool.name == "search_docs_by_lang_chain"
        ]
        fact_agent = create_deep_agent(model=model, tools=search_tools)
        result = await fact_agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": (
                    "Use the LangChain docs MCP tool to describe the LangChain "
                    f"product '{product}' in ONE short factual sentence under "
                    "25 words. Return only the sentence. Refer to the product "
                    f"only as '{product}', even if the docs use another name."
                ),
            }],
        })
        return result["messages"][-1].content.strip()
    except Exception as exc:
        print(f"[product fact] falling back to placeholder ({exc})")
        return PLACEHOLDER_FACT


@tool
def fetch_product_fact(product: str) -> str:
    """Look up one grounded, factual sentence about the LangChain product
    you were matched with. Call this right after score_and_match, passing
    in the product name it returned."""
    return asyncio.run(_fetch_product_fact_async(product))


# ════════════════════════════════════════════════════════════════════════
# TODO 4 (Lesson 1.7, Messages, Threads, and Checkpointers: Threads)
# Add another persona key here (try "ancient_mummy" or "savage_critic",
# already written above) so it runs in its own thread. 

# You'll get multiple cards to compare, judging the same quiz answers.
# ════════════════════════════════════════════════════════════════════════

JUDGES_TO_RUN = ["your_persona", "ancient_mummy"]


def build_user_prompt(answers: list[tuple[int, int, int]]) -> str:
    return (
        "Here are my personality quiz answers as a list of "
        "(chaotic/organized, cautious/bold, solo/collaborative) deltas, in "
        f"order: {answers}. Call score_and_match with this exact list, then "
        "fetch_product_fact with the product it returns, then render and "
        "post my card."
    )


if __name__ == "__main__":
    answers = run_quiz()
    user_prompt = build_user_prompt(answers)
    for judge_name in JUDGES_TO_RUN:
        run_judge(
            judge_name,
            system_prompt=JUDGE_PERSONAS[judge_name],
            user_prompt=user_prompt,
            tools=[score_and_match, fetch_product_fact, render_card, post_card],
            model=model,  # Keep the current model; strong_model is an optional comparison.
            interrupt_on={"post_card": True},
        )
    print(f"\nCards saved to {OUTPUT_DIR}/")
