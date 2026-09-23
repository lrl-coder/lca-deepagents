# python/m4/m4.2_homework.py
"""M4.2 Homework: Give Each Subagent Its Own Scoped Scratch Folder.

THE IDEA
The lab's genre-researcher subagents each wrote raw search notes to their own
assigned /research/<genre>/ folder, kept out of the editor's context by
FilesystemPermission scoping: researchers could write under /research/**, the
editor could not. 

This homework asks you to build a small team of 2 subagent types for 
a domain YOU pick (e.g., trip planning, home renovation), each with 
its own private, permission-scoped folder under /scratch/<name>/ to
stash raw notes in before answering. The harness below wires up the scratch
folder, the permissions, and the write-before-answering instruction for you;
you just decide who your two subagents are.

WHAT YOU FILL IN
  TODO 1: for each of the two entries in SUBAGENT_SPECS, fill in "name",
    "description" (when the main agent should call it), and "role_prompt"
    (who this subagent is and what its job is). Everything else -- the
    scratch folder, the permissions, the instruction to save raw notes
    before answering -- is handled for you.
  TODO 2: write the main agent's system prompt, telling it which subagent
    to call for which part of the job, and a user request that should
    trigger delegation to BOTH subagents.

RUN
  cd python
  uv run ./m4/m4.2_homework.py
"""

from deepagents import FilesystemPermission, create_deep_agent

from models import model, strong_model

SCRATCH_ROOT = "/scratch"


def scratch_path(subagent_name: str) -> str:
    return f"{SCRATCH_ROOT}/{subagent_name}/notes.md"


def scratch_permissions(subagent_name: str) -> list:
    """Scope a subagent to write only under its own scratch folder -- the same
    first-match-wins allow-then-deny pattern the lab used for
    research_permissions/editor_permissions."""
    return [
        FilesystemPermission(operations=["read", "write"], paths=[f"{SCRATCH_ROOT}/{subagent_name}/**"], mode="allow"),
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
    ]


def scratch_instruction(subagent_name: str) -> str:
    return (
        f'Before you answer, call write_file on "{scratch_path(subagent_name)}" '
        "with your raw notes or reasoning. Then give your final answer using "
        "only the polished result -- do not repeat those raw notes in your reply."
    )


def build_subagents(specs: list[dict]) -> list[dict]:
    team = []
    for spec in specs:
        name = spec["name"]
        team.append(
            {
                "name": name,
                "description": spec["description"],
                "system_prompt": spec["role_prompt"] + "\n\n" + scratch_instruction(name),
                "permissions": scratch_permissions(name),
            }
        )
    return team


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Fill in your two subagents.
#
# For each entry: "name" is the handle the main agent calls it by, kebab-
# case (e.g. "flight-finder"). "description" is how the main agent decides
# which one to use. "role_prompt" is that subagent's own job description --
# don't mention scratch files or write_file here, that's added for you.
# ════════════════════════════════════════════════════════════════════════

SUBAGENT_SPECS = [
    {
        "name": "exercise-expert",
        "description": (
            "为希望塑形、增肌或改善体能的用户设计安全、可执行的训练方案，"
            "包括动作、组数、次数、频率和渐进方式。"
        ),
        "role_prompt": (
            "你是一名运动专家，擅长力量训练、体态塑形和训练计划设计。"
            "根据用户的目标，给出兼顾纤细体态与清晰肌肉线条的训练建议，"
            "说明每周频率、动作选择、组数次数、强度与渐进方式，并提醒必要的"
            "热身、恢复和安全注意事项。建议应现实、具体且适合普通健身者。"
        ),
    },
    {
        "name": "nutrition-planner",
        "description": (
            "为减脂、塑形和增肌目标提供营养搭配建议，包括热量、蛋白质、"
            "膳食结构和便于执行的食物选择。"
        ),
        "role_prompt": (
            "你是一名营养搭配师，擅长为健身与体态管理目标设计均衡、可持续的"
            "饮食方案。根据用户想要纤细身材并保留肌肉线条的目标，给出合理的"
            "热量策略、蛋白质摄入、三餐搭配、训练前后饮食和食物示例。"
            "避免极端节食；信息不足时给出按体重计算的通用范围，并说明如何调整。"
        ),
    },
]


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write the main agent's system prompt and a triggering request.
#
# MAIN_PROMPT should tell the main agent about each subagent by name and
# when to call it (mirror how EDITOR_PROMPT in the lab named
# genre-researcher and explained the job).
# USER_REQUEST should be a task that should make the main agent delegate to
# BOTH of your subagents.
# ════════════════════════════════════════════════════════════════════════

MAIN_PROMPT = """你是一名健身方案协调顾问，负责整合运动与饮食建议。

处理用户请求时使用 task 工具委派给以下两名专家：
- exercise-expert（运动专家）：负责训练计划、动作安排、训练频率、强度和恢复建议。
- nutrition-planner（营养搭配师）：负责热量策略、营养素分配、餐食搭配和食物选择。

当用户的问题同时涉及身材塑形和饮食时，必须分别调用这两个子代理。收集两名专家的
结果后，将其整合成一份清晰、协调、可执行的中文方案；不要代替专家自行制定训练或
饮食内容。若用户未提供身体数据，先给出安全的通用方案，并列出后续个性化所需信息。"""

USER_REQUEST = "我身高162cm，体重48kg，我想要纤细的身材，同时拥有清晰的肌肉线条，应该如何锻炼和饮食？"

for _spec in SUBAGENT_SPECS:
    if _spec["name"].startswith("TODO-1"):
        raise NotImplementedError("TODO 1: see the comment block above")
if MAIN_PROMPT.startswith("TODO 2") or USER_REQUEST.startswith("TODO 2"):
    raise NotImplementedError("TODO 2: see the comment block above")

_team = build_subagents(SUBAGENT_SPECS)

# The main agent must never write into any subagent's scratch folder either.
MAIN_PERMISSIONS = [
    FilesystemPermission(operations=["write"], paths=[f"{SCRATCH_ROOT}/**"], mode="deny"),
]

agent = create_deep_agent(
    model=strong_model,
    name="Homework_Team_Agent",
    system_prompt=MAIN_PROMPT,
    subagents=_team,
    permissions=MAIN_PERMISSIONS,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": USER_REQUEST}]},
    config={"recursion_limit": 50},
)
print(result["messages"][-1].content)

files = result.get("files", {})
print("\n--- Scratch folder isolation check ---")
for spec in SUBAGENT_SPECS:
    path = scratch_path(spec["name"])
    print(f"  {path}: {'found' if path in files else 'not written (subagent may not have been called)'}")

scratch_files = [p for p in files if p.startswith(SCRATCH_ROOT + "/")]
expected = {scratch_path(spec["name"]) for spec in SUBAGENT_SPECS}
stray = [p for p in scratch_files if p not in expected]
if stray:
    print(f"  Unexpected scratch files (isolation may have failed): {stray}")
else:
    print("  No stray scratch files -- each subagent wrote only to its own folder.")
