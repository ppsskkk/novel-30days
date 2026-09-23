import os
import re
import json
import requests
from openai import OpenAI

state = json.load(open("state/progress.json", encoding="utf-8"))
day = state["current_day"] - 1

md_text = open(f"output/day{day:02d}.md", encoding="utf-8").read()
html = open(f"output/day{day:02d}_wechat.html", encoding="utf-8").read()

# 1. AI 出配图方案
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content":
        "根据下面这篇文学解读文章，设计3张配图方案。每张图给出：\n"
        "- keyword：用于图库搜索的英文关键词（偏场景/意象，如 cemetery、mountain village，用常见词，不要太生僻）\n"
        "- caption：一句贴合文章情节或人物的中文图注，15字以内，有文学感\n"
        "只返回JSON数组，如 [{\"keyword\":\"a\",\"caption\":\"b\"}]\n\n"
        + md_text[:3000]}],
).choices[0].message.content
items = json.loads(re.search(r"\[.*\]", resp, re.S).group())
print(f"AI配图方案: {items}")

# 2. 搜图，带备用关键词兜底
headers = {"Authorization": os.environ["PEXELS_API_KEY"]}
FALLBACK = ["old book", "chinese village", "oil lamp"]

def search_photo(keyword):
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         headers=headers,
                         params={"query": keyword, "per_page": 1,
                                 "orientation": "landscape"},
                         timeout=30).json()
        photos = r.get("photos") or []
        return photos[0]["src"]["large"] if photos else None
    except Exception as e:
        print(f"  搜图出错({keyword}): {e}")
        return None

blocks = []
for i, item in enumerate(items[:3]):
    caption = item.get("caption", "").strip()
    url = search_photo(item.get("keyword", ""))
    if not url:  # 主关键词没搜到，用备用词
        url = search_photo(FALLBACK[i % len(FALLBACK)])
    if not url:
        print(f"  第{i+1}张图彻底搜不到，跳过")
        continue
    print(f"  第{i+1}张图: {url}")
    caption_html = (
        f'<p style="text-align:center;font-size:12px;color:#999;margin:-10px 0 18px;">'
        f'▲ {caption}</p>' if caption else ""
    )
    blocks.append(
        f'<img src="{url}" style="width:100%;border-radius:10px;margin:18px 0;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.1);"/>{caption_html}'
    )

# 3. 插图（从后往前插，避免位置错乱）
if blocks:
    html = re.sub(r"(</h1>)", r"\1" + blocks[0], html, count=1)
    h2s = list(re.finditer(r"</h2>", html))[: len(blocks) - 1]
    for m, block in zip(reversed(h2s), reversed(blocks[1:])):
        pos = m.end()
        html = html[:pos] + block + html[pos:]

# 4. 包整体底色
final = (
    '<div style="max-width:677px;margin:0 auto;background:#fffdf9;'
    'padding:10px 2px;font-family:-apple-system,PingFang SC,Microsoft YaHei,sans-serif;">'
    + html + "</div>"
)
open(f"output/day{day:02d}_final.html", "w", encoding="utf-8").write(final)
print(f"第{day}集配图完成，共插入 {len(blocks)} 张图")
