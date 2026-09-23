import os
import json
from openai import OpenAI

BOOK_TITLE = "《沧浪之水》"   # ← 改成你的书名

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
if len(content) > 45000:
    content = content[:45000]

recap = ""
if state["summaries"]:
    recap = "【前情提要】\n" + "\n".join(
        f"第{i+1}集：{s}" for i, s in enumerate(state["summaries"][-3:])
    )

prompt = f"""你是一位资深文学评论家，正在做{BOOK_TITLE}的连载解读，共{total}集，今天是第{day}集。

{recap}

请对今天这部分内容写一篇1500~2500字的公众号解说文章，要求：
1. 标题格式：「{BOOK_TITLE}·第{day}讲 | 一句吸引人的副标题」（一级标题）
2. 开头一段话承接前文（第1集则写全书引子，制造期待感；最后一集写全书总评收尾）
3. 结构：今日情节 → 人物与细节分析 → 主题深挖 → 金句摘抄（引用块）→ 结尾留悬念引导明天继续（最后一集改为阅读推荐）
4. 语言通俗有网感，多分段，每段不超过4行
5. 以转述和评论为主，不要大段照抄原文

今日原文：
{content}"""

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
    messages=[{"role": "user", "content": f"用100字以内概括以下内容的核心情节和人物进展：\n{content[:10000]}"}],
).choices[0].message.content

state["summaries"].append(summary)
state["current_day"] = day + 1
json.dump(state, open("state/progress.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"第{day}/{total}集生成完毕")
