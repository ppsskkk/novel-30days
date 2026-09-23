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

# 第一阶段：分段精读，大量摘录原文
SEG = 30000
segments = [content[i:i + SEG] for i in range(0, len(content), SEG)]
digests = []
for idx, seg in enumerate(segments, 1):
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content":
            f"请精读以下长篇小说片段，输出两部分：\n"
            f"1）详细情节梗概（800字以内，保留关键转折、人物行为与重要对话）\n"
            f"2）原著原文摘录8~10段：优先选关键对话、心理描写、戳人的细节描写、"
            f"有张力的冲突场景，每段80~200字，原文照录，注明出自什么情境\n\n"
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

# 第二阶段：写解说稿，原文占比不低于三分之一
prompt = f"""你是一位资深文学评论家，正在做{BOOK_TITLE}的连载解读，共{total}集，今天是第{day}集。

{recap}

下面是今天这部分原文（约6万字）的精读笔记（含情节梗概和大量原著摘录），请据此写一篇2500~4000字的公众号解说文章，要求：
1. 标题格式：「{BOOK_TITLE}·第{day}讲 | 一句吸引人的副标题」（一级标题）
2. 开头一段话承接前文（第1集则写全书引子，制造期待感；最后一集写全书总评收尾）
3. 结构：今日情节 → 人物与细节分析 → 主题深挖 → 金句摘抄 → 结尾留悬念引导明天继续（最后一集改为阅读推荐）
4. 【核心要求】这是一篇"带原文的解读"，全文的原著原文占比不低于三分之一：
   - 今日情节：按故事发展顺序，每个关键情节点都先引一段原文（引用块），再用一两句话点评，至少引4~6段
   - 人物与细节分析、主题深挖：每个板块至少嵌入2~3段原文，引用后紧跟你的点评
   - 金句摘抄：集中放4~5段最精彩的原文
   - 所有原文从笔记的"原著摘录"中原文照录，不要改写
5. 评论语言通俗有网感，多分段，每段不超过4行
6. 评论部分用自己的话转述，评论本身不要照抄原文

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
