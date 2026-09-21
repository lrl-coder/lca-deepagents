# python/m1/gh_auth/github_agent.py
"""GitHub MCP agent — OAuth via the MCP SDK's built-in flow.

The MCP SDK's OAuthClientProvider handles PKCE, discovery, and token exchange.
GitHubTokenStorage pre-seeds the registered client credentials so the SDK skips
dynamic client registration (which GitHub does not support).

Run:  uv run python m1/gh_auth/github_agent.py
"""

from __future__ import annotations

import asyncio
import base64
import mimetypes
import os
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from mcp.types import TextResourceContents

from models import model

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

TOKEN_FILE = Path(__file__).resolve().parent.parent.parent / ".m1_github_token"
RESOURCE_DIR = Path(__file__).resolve().parent / "github_resources"

MCP_URL = "https://api.githubcopilot.com/mcp/"
REDIRECT_URI = "http://127.0.0.1:8765/"
SCOPE = "repo read:user"


class GitHubOAuthClientProvider(OAuthClientProvider):
    """OAuthClientProvider with two GitHub-specific fixes:

    1. Scope: the SDK replaces client_metadata.scope with the full list from
       GitHub's PRM scopes_supported. We restore the intended scope before the
       authorization URL is built.
    2. Token response: GitHub returns URL-encoded form data by default; adding
       Accept: application/json forces a JSON response the SDK can parse.
    """

    def __init__(self, *args, requested_scope: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._requested_scope = requested_scope

    async def _perform_authorization_code_grant(self) -> tuple[str, str]:
        self.context.client_metadata.scope = self._requested_scope
        return await super()._perform_authorization_code_grant()

    async def _exchange_token_authorization_code(
        self, auth_code: str, code_verifier: str, *, token_data: dict | None = {}
    ) -> httpx.Request:
        req = await super()._exchange_token_authorization_code(
            auth_code, code_verifier, token_data=token_data
        )
        req.headers["Accept"] = "application/json"
        return req


class GitHubTokenStorage:
    """Pre-seeds client credentials so the SDK skips dynamic client registration."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def get_tokens(self) -> OAuthToken | None:
        if TOKEN_FILE.exists():
            raw = TOKEN_FILE.read_text().strip()
            if raw:
                try:
                    return OAuthToken.model_validate_json(raw)
                except Exception:
                    return OAuthToken(access_token=raw, token_type="Bearer")
        return None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        TOKEN_FILE.write_text(tokens.model_dump_json())

    async def get_client_info(self) -> OAuthClientInformationFull:
        return OAuthClientInformationFull(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uris=[REDIRECT_URI],
            token_endpoint_auth_method="client_secret_post",
        )

    async def set_client_info(self, info: OAuthClientInformationFull) -> None:
        pass  # credentials come from .env, not from registration


async def open_browser(url: str) -> None:
    print(f"Opening browser for GitHub login ({SCOPE})...")
    print(f"If it doesn't open, paste this URL:\n{url}\n")
    webbrowser.open(url)


async def wait_for_callback() -> tuple[str, str | None]:
    """Loopback server that captures the authorization code from GitHub's redirect."""
    result: dict[str, str] = {}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            params = parse_qs(urlparse(self.path).query)
            result["code"] = params.get("code", [""])[0]
            result["state"] = params.get("state", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h3>Authorized. You can close this tab.</h3>")
            done.set()

        def log_message(self, *a): pass

    port = int(urlparse(REDIRECT_URI).port or 80)
    server = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    if not done.wait(timeout=300):
        server.shutdown()
        raise SystemExit("Timed out waiting for OAuth callback.")
    server.shutdown()
    return result["code"], result.get("state")


def create_github_client(client_id: str, client_secret: str) -> MultiServerMCPClient:
    auth = GitHubOAuthClientProvider(
        server_url=MCP_URL,
        client_metadata=OAuthClientMetadata(
            redirect_uris=[REDIRECT_URI],
            scope=SCOPE,
            token_endpoint_auth_method="client_secret_post",
        ),
        storage=GitHubTokenStorage(client_id, client_secret),
        redirect_handler=open_browser,
        callback_handler=wait_for_callback,
        requested_scope=SCOPE,
    )
    return MultiServerMCPClient({
        "github": {
            "transport": "streamable_http",
            "url": MCP_URL,
            "auth": auth,
        }
    })


async def download_resources(client_id: str, client_secret: str, resources) -> int:
    """Read listed MCP resources and save their contents to local files."""
    if not resources:
        return 0

    RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for resource_index, resource in enumerate(resources, start=1):
        try:
            # A malformed HTTP response can terminate the MCP transport's
            # background task. Isolate each read so one bad resource does not
            # poison the session used by later resources or the agent.
            resource_client = create_github_client(client_id, client_secret)
            async with resource_client.session("github") as session:
                result = await session.read_resource(resource.uri)
        except Exception as e:  # noqa: BLE001
            print(f"  Could not download {resource.name}: {e}")
            continue

        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", resource.name).strip(" .")
        safe_name = safe_name or "resource"
        name_path = Path(safe_name)
        for content_index, content in enumerate(result.contents, start=1):
            try:
                default_extension = (
                    ".txt" if isinstance(content, TextResourceContents) else ".bin"
                )
                extension = name_path.suffix or mimetypes.guess_extension(
                    content.mimeType or ""
                ) or default_extension
                part = f"_part{content_index}" if len(result.contents) > 1 else ""
                filename = f"{resource_index:03d}_{name_path.stem}{part}{extension}"
                path = RESOURCE_DIR / filename

                if isinstance(content, TextResourceContents):
                    path.write_text(content.text, encoding="utf-8")
                else:
                    path.write_bytes(base64.b64decode(content.blob))
                downloaded += 1
                print(f"  Downloaded {resource.name} -> {path}")
            except Exception as e:  # noqa: BLE001
                print(f"  Could not save {resource.name} part {content_index}: {e}")

    return downloaded


async def main() -> None:
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env.")

    client = create_github_client(client_id, client_secret)

    resources = []
    async with client.session("github") as session:
        try:
            cursor = None
            while True:
                page = await session.list_resources(cursor=cursor)
                resources.extend(page.resources)
                cursor = page.nextCursor
                if not cursor:
                    break
            print(f"github: {len(resources)} resource(s) available")
            for resource in resources:
                description = f" - {resource.description}" if resource.description else ""
                print(f"  {resource.name}: {resource.uri}{description}")
        except Exception as e:  # noqa: BLE001
            print(f"github: could not list resources: {e}")

        try:
            prompts = []
            cursor = None
            while True:
                page = await session.list_prompts(cursor=cursor)
                prompts.extend(page.prompts)
                cursor = page.nextCursor
                if not cursor:
                    break
            print(f"github: {len(prompts)} prompt(s) available")
            for prompt in prompts:
                description = f" - {prompt.description}" if prompt.description else ""
                print(f"  {prompt.name}{description}")
        except Exception as e:  # noqa: BLE001
            print(f"github: could not list prompts: {e}")

    downloaded = await download_resources(client_id, client_secret, resources)
    print(f"github: downloaded {downloaded} resource file(s) to {RESOURCE_DIR}")

    client = create_github_client(client_id, client_secret)
    async with client.session("github") as session:
        tools = await load_mcp_tools(session)
        for tool in tools:
            # BaseTool.handle_tool_error only catches ToolException, not the MCP
            # server's own errors (e.g. McpError on a 404), which would otherwise
            # crash the whole run. Wrap the coroutine so failures become a normal
            # tool result the agent can see and react to.
            def _make_safe(coro):
                async def _safe(*args, **kwargs):
                    try:
                        return await coro(*args, **kwargs)
                    except Exception as e:  # noqa: BLE001
                        # response_format="content_and_artifact" expects a 2-tuple
                        return f"Tool call failed: {e}", None
                return _safe

            tool.coroutine = _make_safe(tool.coroutine)
        print(f"github: {len(tools)} tool(s) available")

        agent = create_deep_agent(model=model, tools=tools)
        print("Running agent...\n")
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": (
                "What is my GitHub username and what repositories do I have?"
            )}]
        })
        print("\n" + result["messages"][-1].text)


if __name__ == "__main__":
    asyncio.run(main())
