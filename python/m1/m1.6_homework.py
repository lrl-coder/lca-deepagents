# python/m1/m1.6_homework.py
"""M1.6 Homework: Connect to a Different MCP Server.

THE IDEA
Lab 1 connected to the LangChain docs MCP server and filtered its tools
down to just search_docs_by_lang_chain. This homework asks you to connect
to a different public MCP server entirely, one that requires no auth
beyond what your labs already use, and put one of its tools to work.

Don't know where to look? A few free, no-auth public servers to try:
  - DeepWiki (https://mcp.deepwiki.com/mcp): ask questions about any
    public GitHub repo's code and docs.
  - X Docs (https://docs.x.com/mcp): search and retrieve X's public API
    documentation.
Or find your own!

WHAT YOU FILL IN
  TODO 1: build and return the filtered list of MCP tools to use from a
    server and filter of your own choosing.
  TODO 2: write a question suited to your chosen server's own domain,
    not Lab 1's "what is MCP..." question, which won't make sense to
    ask a server about GitHub repos, API docs, or whatever you picked.

RUN
  cd python
  uv run ./m1/m1.6_homework.py
"""

import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from models import model

# ════════════════════════════════════════════════════════════════════════
# TODO 1: Build your MCP client and return its filtered tool list.
#
# Requirements:
#   - Point "url" at a different public MCP server than Lab 1's
#     docs-langchain server (no auth/API key required beyond what your
#     labs already use). See the module docstring for two ready-to-use
#     options.
#   - Fetch tools with client.get_tools() and filter them the same way
#     Lab 1 did, with an ALLOWED set.
#
# Example shape (delete this and write your own):
#   async def build_tools():
#       client = MultiServerMCPClient({
#           "my-server": {"transport": "http", "url": "https://..."}
#       })
#       tools = await client.get_tools()
#       ALLOWED = {"some_tool_name"}
#       return [t for t in tools if t.name in ALLOWED]
# ════════════════════════════════════════════════════════════════════════


async def build_tools():
    """TODO 1: build a MultiServerMCPClient, fetch its tools, filter them,
    and return the filtered list."""
    client = MultiServerMCPClient(
        {"deepwiki-server": {"transport": "http", "url": "https://mcp.deepwiki.com/mcp"}}
    )
    tools = await client.get_tools()
    resources = await client.get_resources()
    # MultiServerMCPClient exposes get_prompt() for fetching one named prompt,
    # so use the underlying session to list all prompts exposed by this server.
    async with client.session("deepwiki-server") as session:
        prompts = (await session.list_prompts()).prompts
    """
    [StructuredTool(name='ask_question', description='Ask any question about a GitHub repository and get an AI-powered, context-grounded response.', args_schema={'properties': {'repoName': {'anyOf': [{'type': 'string'}, {'items': {'type': 'string'}, 'type': 'array'}], 'description': 'GitHub repository or list of repositories (max 10) in owner/repo format.'}, 'question': {'description': 'The question to ask about the repository.', 'type': 'string'}}, 'required': ['repoName', 'question'], 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, handle_tool_error=<function _handle_mcp_tool_error at 0x000002543F3B6DE0>, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x00000254429F04A0>), StructuredTool(name='read_wiki_contents', description='View documentation about a GitHub repository.', args_schema={'properties': {'repoName': {'description': 'GitHub repository in owner/repo format (e.g. "facebook/react").', 'type': 'string'}}, 'required': ['repoName'], 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, handle_tool_error=<function _handle_mcp_tool_error at 0x000002543F3B6DE0>, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x00000254429F02C0>), StructuredTool(name='read_wiki_structure', description='Get a list of documentation topics for a GitHub repository.', args_schema={'properties': {'repoName': {'description': 'GitHub repository in owner/repo format (e.g. "facebook/react").', 'type': 'string'}}, 'required': ['repoName'], 'type': 'object'}, metadata={'_meta': {'_fastmcp': {'tags': []}}}, handle_tool_error=<function _handle_mcp_tool_error at 0x000002543F3B6DE0>, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x0000025442A5BF60>)]
    """
    ALLOWED = {"ask_question"}
    return [t for t in tools if t.name in ALLOWED]


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write a question suited to your chosen server's own domain,
# not Lab 1's "what is MCP..." question.
# ════════════════════════════════════════════════════════════════════════

QUESTION = (
    "请使用 DeepWiki 查询 GitHub 仓库 `langchain-ai/deepagents`："
    "这个项目是做什么的，它支持哪些文件系统后端？"
)

async def main():
    tools = await build_tools()
    agent = create_deep_agent(model=model, tools=tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": QUESTION}]})
    print(result["messages"][-1].text)


asyncio.run(main())

# https://smith.langchain.com/public/bbef2934-5b1a-4c20-b67d-d9ff67412634/r/01a0c23d-09c1-7eb1-b8ef-453fd5112e71?start_time=2026-09-21T04%3A32%3A55.233397Z