import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from pathlib import Path

from deepagents import create_deep_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool

from models import model

DB_PATH = Path(__file__).parent / "chinook.db"
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

SYSTEM_PROMPT = """You are a SQL analyst with access to the Chinook music store database.

Rules:
- Use read_sql for SELECT queries.
- Do not modify the database.
- If a tool returns an error, revise the SQL and try again.
- Show your SQL in your final answer.
"""


@tool
def read_sql(query: str) -> str:
    """Run a read-only SELECT query against the Chinook music store database."""
    try:
        return str(db.run(query))
    except Exception as e:
        return f"Error: {e}"


agent = create_deep_agent(
    model=model,
    name="SQL_Agent",
    tools=[read_sql],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "Which five genres have the most tracks?"}
        ]
    }
)

print(result["messages"][-1].content)

"""
{
    "messages": [
        HumanMessage(
            content="Which five genres have the most tracks?",
            additional_kwargs={},
            response_metadata={},
            id="5bd8b489-1098-4afd-9f76-78df43f653ac",
        ),
        AIMessage(
            content=[
                {
                    "id": "rs_03a33c395c0fc3e6006aafc94673b887d095cec4012e1647f2",
                    "summary": [],
                    "type": "reasoning",
                    "content": [],
                    "encrypted_content": "gAAAAABqr8lHBv4jc5YIYM5x2So_yvs3bOXgob9ldHTvbsz8mbmww23NnodQYknKDPuXrAoNyY7KYwd7Bhoi7VISzyjgHGg1-LwmqPfE3cbpaPg4Q7KwKiFuNP2h43msOAw4tUwi8HLTuNtLFfY7Nd52iGUjCgz6elRAp8Hxfc2PHBvGWCSPG69XaJh8UNBWRk7AQEzpeEsRjb0TXbYp_9uqKbDjcNh5bxT728udliQ2VkU_iGWPqX8kdvMLhTD3tMnL7G9xeWTkZ_qs49_S7gkbaIUN5eJmSYO5MuFAQ12VnQMf4wNy53MfRM_CAxxe2zogoL580R0bGVknaOP4OsSkE8wc7PZSyyVhm0B1k2OjsW99u2wy7-OC_rJmKCnrsRKl0vd3tseBLNjTTnP1o1vAoYxFfiohIv9WLzKnz8DhrhCcgs1fCxi0huwk-ez3b3kaxgG_BGBC90Mpc5EqmLN4R84232phMA2p97PIhY2htCtnb5qMx4HfYcQY5VkFLtPBBIdDlWVOb9VT8AJVgs3hZeVvvuZlM-UHya_Krnl5JCtdmJo3UtkHlWpwKHa8lS5YyfygzS5mKEsNYcDqe0-XAo0yIM_KAdrQt0SWD_V8I-EIdd4jJkVmkdpho288TYUM5gy5btUSqoaO1SNOG4Etqqt8TjfrPLNTlfqIo9c6g9xwzB6h7iQJpFLewGCc3Gr61n6O3RJNy5Uetgx_d5dOKzqrPTsRK1CBesrVhSv6nkZKVopNaS2GkcbiP_jCfqI2m-XVNvGgVh_yfEIX2YHRI-fRN-C9aG2VoxjS3JvPYtoFq7GaThe_LH_M5I-zMtZUY-WYw3GYz3btIGtajFXUn4LKZ44DJ-KutJZtvvdb6oJFyQKG71rjthsi6ewtSElOvcOKewBYif04biyx0Fq34ot6b4o1XwyHHWfFA0zj6xCyKzUcjYmRsACCInCGMEOgKQ4hYqaZyiXr8LB6-TsxvJmVKmmyuEyKrDRwqo487XwvOZQFY6EGregHfyhGYApS9sAkCFDA2cWNAEewgdJ0EJw-aqo2HpxR7w_CkW2KBAU3ImaeQ6Xb33oNRiTSQ4XkjQ09oyd22SrlncAStSR93iM-pg6qKQPDorEpGg1mjaOCd9BIJjFPT1SWY5PEAXr7YNXgmrWiJ9mB0b9OzOW89IiR4a0uxQ8WXNJF_rtl8d__UVXVUiE1S-TaZAMDlUEZ7r61cFl-vZqWzqRrO1Qig1WhrUUziekccG9rmLPJV7i9nBzlgcU=",
                },
                {
                    "arguments": '{"query":"SELECT g.Name AS Genre, COUNT(t.TrackId) AS TrackCount\\nFROM Genre AS g\\nJOIN Track AS t ON t.GenreId = g.GenreId\\nGROUP BY g.GenreId, g.Name\\nORDER BY TrackCount DESC, Genre ASC\\nLIMIT 5;"}',
                    "call_id": "call_wQCVc5IrdtOKY91bgHZ0SfPn",
                    "name": "read_sql",
                    "type": "function_call",
                    "id": "fc_03a33c395c0fc3e6006aafc946b88c87d0967aea9bb88a2224",
                    "status": "completed",
                },
            ],
            additional_kwargs={},
            response_metadata={
                "id": "resp_03a33c395c0fc3e6006aafc945bac887d095a5165ea73b4c85",
                "created_at": 1789905221.0,
                "metadata": {},
                "model": "gpt-5.6-luna",
                "object": "response",
                "service_tier": "default",
                "status": "completed",
                "model_provider": "openai",
                "model_name": "gpt-5.6-luna",
            },
            name="SQL_Agent",
            id="resp_03a33c395c0fc3e6006aafc945bac887d095a5165ea73b4c85",
            tool_calls=[
                {
                    "name": "read_sql",
                    "args": {
                        "query": "SELECT g.Name AS Genre, COUNT(t.TrackId) AS TrackCount\nFROM Genre AS g\nJOIN Track AS t ON t.GenreId = g.GenreId\nGROUP BY g.GenreId, g.Name\nORDER BY TrackCount DESC, Genre ASC\nLIMIT 5;"
                    },
                    "id": "call_wQCVc5IrdtOKY91bgHZ0SfPn",
                    "type": "tool_call",
                }
            ],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 1829,
                "output_tokens": 95,
                "total_tokens": 1924,
                "input_token_details": {"cache_creation": 1826, "cache_read": 0},
                "output_token_details": {"reasoning": 18},
            },
        ),
        ToolMessage(
            content="[('Rock', 1297), ('Latin', 579), ('Metal', 374), ('Alternative & Punk', 332), ('Jazz', 130)]",
            name="read_sql",
            id="a7516844-74f5-4b67-b6d7-47dca1515c71",
            tool_call_id="call_wQCVc5IrdtOKY91bgHZ0SfPn",
        ),
        AIMessage(
            content=[
                {
                    "type": "text",
                    "text": "The five genres with the most tracks are:\n\n| Rank | Genre | Tracks |\n|---:|---|---:|\n| 1 | Rock | 1,297 |\n| 2 | Latin | 579 |\n| 3 | Metal | 374 |\n| 4 | Alternative & Punk | 332 |\n| 5 | Jazz | 130 |\n\n```sql\nSELECT g.Name AS Genre, COUNT(t.TrackId) AS TrackCount\nFROM Genre AS g\nJOIN Track AS t ON t.GenreId = g.GenreId\nGROUP BY g.GenreId, g.Name\nORDER BY TrackCount DESC, Genre ASC\nLIMIT 5;\n```",
                    "annotations": [],
                    "id": "msg_03a33c395c0fc3e6006aafc94e83ac87d0a49e8629b2ccf422",
                    "phase": "final_answer",
                }
            ],
            additional_kwargs={},
            response_metadata={
                "id": "resp_03a33c395c0fc3e6006aafc94d3c8887d08e723e62232e563b",
                "created_at": 1789905229.0,
                "metadata": {},
                "model": "gpt-5.6-luna",
                "object": "response",
                "service_tier": "default",
                "status": "completed",
                "model_provider": "openai",
                "model_name": "gpt-5.6-luna",
            },
            name="SQL_Agent",
            id="resp_03a33c395c0fc3e6006aafc94d3c8887d08e723e62232e563b",
            tool_calls=[],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 1969,
                "output_tokens": 140,
                "total_tokens": 2109,
                "input_token_details": {"cache_creation": 140, "cache_read": 1826},
                "output_token_details": {"reasoning": 0},
            },
        ),
    ],
    "files": {},
}

"""
