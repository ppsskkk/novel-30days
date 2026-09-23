import os
import json
from openai import OpenAI

BOOK_TITLE = "《沧浪之水》"

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url="https://api.deepseek.com",
)

state = json.load(open("state/progress.json", encoding="utf-8"))
day = state["current_day"]
total = state["total_days"]

if day > total:
    print(f"{total}集已全部生成完毕")
    exit(0)

content = open(f"novels/day{day:02d}.txt", encoding="utf-8").read()

# 第一阶段：分段精读，多摘原文
SEG = 30000
segments = [content[i:i + SEG] for i in range(0, len(content), SEG)]
digests = []
for idx, seg in enumerate(segments, 1):
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content":
            f"请精读以下长篇小说片段，输出两部分：\n"
            f"1）详细情节梗概（600字以内，保留关键转折、人物行为与重要对话）\n"
            f"2）原著原文摘录5~6段：优先选关键对话、心理描写、戳人的细节描写，"
            f"每段50~150字，原文照录，注明出自什么情境\n\n"
            f"片段如下：\n{seg}"}],
    )
    digests.append(r.choices[0].message.content)
    print(f"  精读第{idx}/{len(segments)}段完成")

material = "\n\n---\n\n".join(digests)

recap = ""
if state["summaries"]:
    recap = "【前情提要】\n" + "\n".join(
        f"第{i+1}集：{s}" for i, s in enumerate(state["summaries"][-3:])
    )

# 第二阶段：基于精读笔记写解说稿，要求大量引用原文
prompt = f"""你是一位资深文学评论家，正在做{BOOK_TITLE}的连载解读，共{total}集，今天是第{day}集。

{recap}

下面是今天这部分原文的精读笔记（含情节梗概和原著摘录），请据此写一篇1500~2500字的公众号解说文章，要求：
1. 标题格式：「{BOOK_TITLE}·第{day}讲 | 一句吸引人的副标题」（一级标题）
2. 开头一段话承接前文（第1集则写全书引子，制造期待感；最后一集写全书总评收尾）
3. 结构：今日情节 → 人物与细节分析 → 主题深挖 → 金句摘抄 → 结尾留悬念引导明天继续（最后一集改为阅读推荐）
4. 【重要】多引用原文：今日情节、人物分析、主题深挖每个板块至少嵌入1~2段原著原文（用引用块），从笔记的"原著摘录"中选取，引用后紧跟一两句你的点评；金句摘抄板块再集中放3~4段最精彩的
5. 语言通俗有网感，多分段，每段不超过4行
6. 评论部分用自己的话转述，不要整段照抄原文

精读笔记：
{material}"""

resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.8,
)
article = resp.choices[0].message.content

os.makedirs("output", exist_ok=True)
open(f"output/day{day:02d}.md", "w", encoding="utf-8").write(article)

summary = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": f"用100字以内概括以下精读笔记的核心情节和人物进展：\n{material[:8000]}"}],
).choices[0].message.content

state["summaries"].append(summary)
state["current_day"] = day + 1
json.dump(state, open("state/progress.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"第{day}/{total}集生成完毕")
