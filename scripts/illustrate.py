import os
import re
import json
import requests
from openai import OpenAI

state = json.load(open("state/progress.json", encoding="utf-8"))
day = state["current_day"] - 1  # 刚生成的那一集

md_text = open(f"output/day{day:02d}.md", encoding="utf-8").read()
html = open(f"output/day{day:02d}_wechat.html", encoding="utf-8").read()

# 1. 让 AI 给出3个配图方案：英文搜图词 + 贴合本文的中文图注
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content":
        "根据下面这篇文学解读文章，设计3张配图方案。每张图给出：\n"
        "- keyword：用于图库搜索的英文关键词（偏场景/意象，如 cemetery、mountain village）\n"
        "- caption：一句贴合文章情节或人物的中文图注，15字以内，有文学感，不要泛泛而谈\n"
        "只返回JSON数组，如 [{\"keyword\":\"a\",\"caption\":\"b\"}]\n\n"
        + md_text[:3000]}],
).choices[0].message.content
items = json.loads(re.search(r"\[.*\]", resp, re.S).group())

# 2. 按 keyword 去 Pexels 搜图
headers = {"Authorization": os.environ["PEXELS_API_KEY"]}
blocks = []
for item in items[:3]:
    r = requests.get("https://api.pexels.com/v1/search",
                     headers=headers,
                     params={"query": item["keyword"], "per_page": 1,
                             "orientation": "landscape"}).json()
    if not r.get("photos"):
        continue
    url = r["photos"][0]["src"]["large"]
    caption = item.get("caption", "").strip()
    caption_html = (
        f'<p style="text-align:center;font-size:12px;color:#999;margin:-10px 0 18px;">'
        f'▲ {caption}</p>' if caption else ""
    )
    blocks.append(
        f'<img src="{url}" style="width:100%;border-radius:10px;margin:18px 0;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>{caption_html}'
    )

# 3. 插图：第一张放标题下方当封面，其余插在小标题后
if blocks:
    html = re.sub(r"(</h1>)", r"\1" + blocks[0], html, count=1)
    h2s = list(re.finditer(r"</h2>", html))
    for i, m in enumerate(h2s[: len(blocks) - 1], start=1):
        pos = m.end()
        html = html[:pos] + blocks[i] + html[pos:]

# 4. 包整体底色
final = (
    '<div style="max-width:677px;margin:0 auto;background:#fffdf9;'
    'padding:24px 18px;font-family:-apple-system,PingFang SC,Microsoft YaHei,sans-serif;">'
    + html + "</div>"
)
open(f"output/day{day:02d}_final.html", "w", encoding="utf-8").write(final)
print(f"第{day}集配图完成，共插入 {len(blocks)} 张图，图注已按内容生成")
