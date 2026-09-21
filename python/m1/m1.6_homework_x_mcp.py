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
        {"x-server": {"transport": "http", "url": "https://docs.x.com/mcp"}}
    )
    tools = await client.get_tools()
    resources = await client.get_resources()
    """
    [StructuredTool(name='search_x', description='Search across the X knowledge base to find relevant information, code examples, API references, and guides. Use this tool when you need to answer questions about X, find specific documentation, understand how features work, or locate implementation details. The search returns contextual content with titles and direct links to the documentation pages. If you need the full content of a specific page, use the query_docs_filesystem tool to `head` or `cat` the page path (append `.mdx` to the path returned from search — e.g. a result at `/some/page` is read with `head -200 /some/page.mdx`).', args_schema={'type': 'object', 'properties': {'query': {'type': 'string', 'description': 'Search query'}}, 'required': ['query'], 'additionalProperties': False}, metadata={'title': None, 'readOnlyHint': True, 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False}, handle_tool_error=<function _handle_mcp_tool_error at 0x0000024C600FA0C0>, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x0000024C6373D800>), StructuredTool(name='query_docs_filesystem_x', description='Run a read-only shell-like query against a virtualized, in-memory filesystem rooted at `/` that contains ONLY the X documentation pages and OpenAPI specs. This is NOT a shell on any real machine — nothing runs on the user\'s computer, the server host, or any network. The filesystem is a sandbox backed by documentation chunks.\n\nThis is how you read documentation pages: there is no separate "get page" tool. To read a page, pass its `.mdx` path to `head` or `cat` — a page at the URL path `/some/page` lives at `/some/page.mdx`. To search the docs with exact keyword or regex matches, use `rg`. To understand the docs structure, use `tree` or `ls`.\n\n**Paths are specific to this site — never guess them.** Discover real paths with `tree / -L 2`, `ls /`, or the search tool before reading. If a path does not exist, that only means the guess was wrong; it does NOT mean the topic is undocumented — use `rg -il "keyword" /` to find where it is covered.\n\n**Workflow:** Start with the search tool for broad or conceptual queries like "how to authenticate" or "rate limiting". Use this tool when you need exact keyword/regex matching, structural exploration, or to read the full content of a specific page by path.\n\nSupported commands: rg (ripgrep), grep, find, tree, ls, cat, head, tail, stat, wc, sort, uniq, cut, sed, awk, jq, plus basic text utilities. No writes, no network, no process control. Run `--help` on any command for usage.\n\nEach call is STATELESS: the working directory always resets to `/` and no shell variables, aliases, or history carry over between calls. If you need to operate in a subdirectory, chain commands in one call with `&&` or pass absolute paths (e.g., `cd /some-directory && ls` or `ls /some-directory`). Do NOT assume that `cd` in one call affects the next call.\n\nExamples (replace the placeholder paths with real ones from `tree` or search):\n- `tree / -L 2` — see the top-level directory layout\n- `rg -il "rate limit" /` — find all files mentioning "rate limit"\n- `rg -C 3 "apiKey" /some-directory/` — show matches with 3 lines of context around each hit\n- `head -80 /some/page.mdx` — read the top 80 lines of a specific page\n- `head -80 /page-one.mdx /page-two.mdx /section/page-three.mdx` — read multiple pages in one call\n- `cat /some/page.mdx` — read a full page when you need everything\n- `cat /openapi/openapi.json | jq \'.paths | keys\'` — list OpenAPI endpoints\n\nOpenAPI specs for this site are mounted at: `/openapi/openapi.json`. Use them to answer questions about endpoints, request/response schemas, parameters, and authentication.\n\nOutput is truncated to 30KB per call. Prefer targeted `rg -C` or `head -N` over broad `cat` on large files. To read only the relevant sections of a large file, use `rg -C 3 "pattern" /path/file.mdx`. Batch multiple file reads into a single `head` or `cat` call whenever possible.\n\nWhen referencing pages in your response to the user, convert filesystem paths to URL paths by removing the `.mdx` extension. For example, `/some/page.mdx` becomes `/some/page`.', args_schema={'type': 'object', 'properties': {'command': {'type': 'string', 'description': 'A shell command to run against the virtualized documentation filesystem (e.g., `rg -il "keyword" /`, `tree / -L 2`, `head -80 /path/file.mdx`).'}}, 'required': ['command'], 'additionalProperties': False}, metadata={'title': None, 'readOnlyHint': True, 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False}, handle_tool_error=<function _handle_mcp_tool_error at 0x0000024C600FA0C0>, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x0000024C6373D620>), StructuredTool(name='submit_feedback', description='Report a problem with this documentation site so the docs team can fix it. Use when a documentation page is incorrect, outdated, confusing, incomplete, or has a broken example. This is for feedback about the documentation content itself — not for product support requests or feedback about this tool or assistant.', args_schema={'type': 'object', 'properties': {'path': {'type': 'string', 'minLength': 1, 'description': 'The URL path of the documentation page the feedback is about (the page you were reading, without the `.mdx` extension).'}, 'feedback': {'type': 'string', 'minLength': 1, 'description': 'A clear description of the documentation issue or suggestion — what is incorrect, outdated, missing, or confusing.'}}, 'required': ['path', 'feedback'], 'additionalProperties': False}, metadata={'title': None, 'readOnlyHint': False, 'destructiveHint': False, 'idempotentHint': False, 'openWorldHint': True}, handle_tool_error=<function _handle_mcp_tool_error at 0x0000024C600FA0C0>, response_format='content_and_artifact', coroutine=<function convert_mcp_tool_to_langchain_tool.<locals>.call_tool at 0x0000024C6373D580>)]
    """
    ALLOWED = {"search_x"}
    return [t for t in tools if t.name in ALLOWED]


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write a question suited to your chosen server's own domain,
# not Lab 1's "what is MCP..." question.
# ════════════════════════════════════════════════════════════════════════

QUESTION = (
    "x 中粉丝数量最多的用户是谁？"
)

async def main():
    tools = await build_tools()
    agent = create_deep_agent(model=model, tools=tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": QUESTION}]})
    print(result["messages"][-1].text)


asyncio.run(main())

# https://smith.langchain.com/public/cfefc05d-2715-4aee-b932-c696b267fabd/r/01a0c247-a934-7b21-89b1-2a13768d41ee?start_time=2026-09-21T04%3A44%3A31.412078Z