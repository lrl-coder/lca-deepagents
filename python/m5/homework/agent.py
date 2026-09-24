# python/m5/homework/agent.py
"""M5.2 Homework: Deploy Your Own Agent.

THE IDEA
The lab deployed a fairly bare-bones agent (no tools, no persona, just
create_deep_agent(model=model)) and you only ever talked to it through
Studio's chat panel. This homework has two parts: first, deploy an agent
with your personal touch; second, talk to it the way any other client
would, straight over the Agent Server API this lesson covers, instead of
through Studio.

WHAT YOU FILL IN
  TODO 1: write your own @tool-decorated function on a topic of your
    choosing. A plain Python dict lookup is enough, no external API or
    key required.
  TODO 2: write a system_prompt that gives the agent a persona of your
    choosing and tells it to call your tool before answering.
  Then open call_agent_api.py in this same folder for TODO 3, which talks
  to this deployed agent over HTTP instead of through Studio.

RUN
  cd python/m5/homework
  uv run langgraph dev
Then chat with your agent in the Studio window that opens, or see
call_agent_api.py to talk to it over the API instead.
"""

from langchain_core.tools import tool

from deepagents import create_deep_agent
from models import model

POSTURE_CORRECTIONS = {
    "足弓塌陷": """矫正重点：恢复足底三点支撑（大脚趾根、小脚趾根、脚跟）和足踝控制。
建议练习：
1. 短足训练：脚趾放松，将前脚掌轻拉向脚跟以抬起足弓，保持 5 秒，8～12 次/组，共 2～3 组。
2. 脚趾瑜伽：大脚趾与其余四趾交替抬起，各做 10～15 次。
3. 提踵：保持脚跟竖直、重心经过第二脚趾，做 10～15 次/组，共 2～3 组。
日常提示：先减少鞋底单侧严重磨损的鞋；走路时避免足内侧完全塌下。若足部疼痛、单侧突然塌陷或麻木，请就医评估。""",
    "小腿外翻": """矫正重点：改善足踝、膝关节的对线和髋部稳定；不要强行把骨性结构掰直。
建议练习：
1. 弹力带侧向走：膝盖对准第二脚趾，左右各 8～12 步，共 2～3 组。
2. 单腿站立：保持足底三点支撑和骨盆水平，每侧 20～30 秒，共 2～3 组。
3. 慢速坐站或浅蹲：膝盖沿脚尖方向移动，8～12 次/组，共 2～3 组。
日常提示：避免站立时长期把膝盖向外顶死。若伴随膝、踝疼痛，或左右差异明显，应由康复治疗师判断是功能性代偿还是骨性排列。""",
    "骨盆前倾": """矫正重点：提升腹部与臀部控制，同时恢复髋屈肌活动度；骨盆有一定前倾属于正常现象。
建议练习：
1. 半跪髋屈肌拉伸：先轻收骨盆再向前移，每侧 30 秒，共 2～3次。
2. 臀桥：肋骨下沉、臀部发力，做 10～15 次/组，共 2～3 组。
3. 死虫式：腰背保持稳定，左右各 6～10 次，共 2～3 组。
日常提示：久坐每 30～60 分钟起身活动；不要用持续收腹或刻意夹臀来维持所谓“标准姿势”。若持续腰痛或疼痛向腿部放射，请就医。""",
    "翼状肩胛": """矫正重点：增强前锯肌和下斜方肌控制，并改善胸椎、肩关节活动。
建议练习：
1. 墙面滑手加前伸：前臂贴墙上滑，末端轻推墙，每组 8～12 次，共 2～3 组。
2. 跪姿俯卧撑加：手肘伸直后继续把上背推开，做 8～12 次/组，共 2～3 组。
3. 俯卧 Y 抬手：肩膀远离耳朵，小幅抬手，做 8～10 次/组，共 2 组。
日常提示：练习中避免耸肩和腰部代偿。若突然出现明显翼状肩胛、上肢无力、麻木或外伤史，应尽快就医排查神经损伤。""",
    "胸椎曲度变直": """矫正重点：恢复胸椎在屈伸、旋转方向上的活动能力，而不是强行制造固定弧度。
建议练习：
1. 泡沫轴胸椎伸展：托住头部，在上背分段轻柔伸展，每个位置 3～5 次呼吸。
2. 四点跪姿穿针引线：每侧 6～10 次，共 2 组。
3. 猫牛式：在无痛范围内缓慢活动脊柱，做 8～12 次。
日常提示：交替使用不同坐姿，并定时活动。影像上的“变直”不能单独决定治疗；如有持续疼痛、呼吸受限或外伤，应接受专业评估。""",
    "脖子前倾": """矫正重点：训练颈深屈肌、改善胸椎活动，并减少长时间固定低头。
建议练习：
1. 下巴微收：像做“双下巴”，头部水平后移，保持 5 秒，8～12 次/组，共 2～3 组。
2. 靠墙滑手：保持后脑勺轻轻向后延伸，做 8～12 次/组，共 2 组。
3. 胸椎伸展：靠椅背或泡沫轴轻柔伸展，每次做 5～8 次。
日常提示：屏幕尽量接近视线高度，每 30～45 分钟变换姿势。若伴随手臂麻木、无力、眩晕、剧烈头痛或外伤，请及时就医。""",
}

POSTURE_ALIASES = {
    "扁平足": "足弓塌陷",
    "足弓下陷": "足弓塌陷",
    "骨盆前移": "骨盆前倾",
    "肩胛骨突出": "翼状肩胛",
    "胸椎变直": "胸椎曲度变直",
    "头前伸": "脖子前倾",
    "颈前伸": "脖子前倾",
}


@tool
def lookup_posture_correction(problem: str) -> str:
    """查询常见体态问题的矫正建议。

    Args:
        problem: 体态问题名称，例如足弓塌陷、小腿外翻、骨盆前倾、
            翼状肩胛、胸椎曲度变直或脖子前倾。一次只查询一个问题。
    """
    normalized_problem = "".join(problem.strip().split())
    canonical_problem = POSTURE_ALIASES.get(normalized_problem, normalized_problem)
    correction = POSTURE_CORRECTIONS.get(canonical_problem)
    if correction:
        return f"{canonical_problem}\n{correction}"

    supported_problems = "、".join(POSTURE_CORRECTIONS)
    return f"暂未收录“{problem}”的矫正方案。目前可查询：{supported_problems}。"


SYSTEM_PROMPT = """你是一名耐心、严谨、注重循序渐进的体态矫正师。你的任务是帮助用户理解常见体态问题，并给出安全、容易执行的练习建议。

当用户询问体态问题或矫正方法时：
1. 回答前必须调用 lookup_posture_correction；如果用户同时询问多个问题，逐个调用工具。
2. 以工具返回的内容为依据，不编造工具中没有的诊断或治疗结论。
3. 先简要说明矫正重点，再清晰列出动作、次数和日常提示；根据用户描述做适度解释，但不要把体态外观等同于疾病。
4. 提醒用户动作应在无痛范围内完成。遇到疼痛剧烈或持续、麻木、无力、眩晕、近期外伤等情况，建议停止练习并咨询医生或康复治疗师。
5. 你提供的是一般性健康教育，不能代替面对面的医学诊断。不要承诺矫正效果或给出确切康复期限。

如果工具未收录用户的问题，坦诚说明范围，并请用户从已支持的问题中选择或寻求专业评估。使用中文回答，语气专业、友好、简洁。"""

# `langgraph.json` points at this module-level variable: "./agent.py:graph".
graph = create_deep_agent(
    model=model,
    tools=[lookup_posture_correction],
    system_prompt=SYSTEM_PROMPT,
)
