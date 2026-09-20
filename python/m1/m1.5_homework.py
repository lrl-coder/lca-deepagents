# python/m1/m1.5_homework.py
"""M1.5 Homework: Build Your Own Custom Tool.

THE IDEA
The lab wired up one custom tool (read_sql) for one fixed topic (the
Chinook music database). This homework asks you to do the same thing for
a topic YOU pick: something you actually know or care about (a game, a
sport, a show, your favorite band's discography, local trivia, whatever).
There's no single correct topic or persona here, that's the point. Two
students doing this homework could end up with two completely different
tools and agents.

WHAT YOU FILL IN
  TODO 1: write your own custom tool with the @tool decorator. Pick any
    topic, store a small lookup (a dict is fine, no API needed) of facts
    about it, and return one back based on the argument the model passes.
  TODO 2: write a system prompt that gives the agent a persona of your
    choosing and tells it to use your tool before answering.

RUN
  cd python
  uv run ./m1/m1.5_homework.py
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_core.tools import tool

from deepagents import create_deep_agent
from models import model


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Define your own custom tool.
#
# Requirements:
#   - Keep the @tool decorator.
#   - Give it a real docstring: one sentence the model will read to decide
#     when to call this tool.
#   - Have it take at least one argument and return a string.
#   - The lookup data can just live in this file (a dict, a list, whatever
#     fits your topic). No external API or key needed.
#
# Example shape (delete this and write your own):
#   @tool
#   def lookup_something(query: str) -> str:
#       """One sentence describing what this returns and when to call it."""
#       ...
# ════════════════════════════════════════════════════════════════════════

from typing import Annotated, Literal
from langchain.tools import tool


@tool
def your_custom_tool(
    query: Annotated[
        Literal["川菜", "粤菜", "鲁菜", "苏菜", "浙菜", "闽菜", "湘菜", "徽菜"],
        "要查询的菜系"
    ]
) -> str:
    """根据查询的菜系提供代表菜肴。"""

    cuisine_dict = {
        "川菜": "麻婆豆腐",
        "粤菜": "白切鸡",
        "鲁菜": "九转大肠",
        "苏菜": "松鼠鳜鱼",
        "浙菜": "西湖醋鱼",
        "闽菜": "佛跳墙",
        "湘菜": "剁椒鱼头",
        "徽菜": "臭鳜鱼",
    }

    return cuisine_dict[query]
    


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write a system prompt for your agent.
#
# Give it a persona (a name, a voice, a personality, anything you want)
# and tell it to call your_custom_tool (rename it if you like) before
# answering, the same way the lab's SYSTEM_PROMPT pointed the agent at
# read_sql.
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是一个大厨，熟悉中餐各种菜系的代表菜肴，请回答用户有关中餐代表菜肴的问题，除此以外不要回答其余领域的问题。你可以使用 `your_custom_tool` 函数查询菜肴。"""

# Guards against running with an unfilled placeholder; the filled
# reference doesn't need this since there's no placeholder text left.
if "TODO 1" in your_custom_tool.description:
    raise NotImplementedError("TODO 1: see the comment block above")
if "TODO 2" in SYSTEM_PROMPT:
    raise NotImplementedError("TODO 2: see the comment block above")

agent = create_deep_agent(
    model=model,
    name="Homework_Agent",
    tools=[your_custom_tool],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "写冒泡排序的python代码。"}]}
)

print(result["messages"][-1].content)
