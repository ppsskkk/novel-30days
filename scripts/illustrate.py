import os
import re
import json
import requests
from openai import OpenAI

state = json.load(open("state/progress.json", encoding="utf-8"))
day = state["current_day"] - 1  # 刚生成的那一集

md_text = open(f"output/day{day:02d}.md", encoding="utf-8").read()
html = open(f"output/day{day:02d}_wechat.html", encoding="utf-8").read()

# 1. 让大模型提炼3个英文画面关键词
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url="https://api.deepseek.com")
kw_resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content":
        "根据下面这篇文学解读文章，给出3个适合配图的英文搜索关键词（偏氛围/场景/意象，如 rainy street、candlelight、old library），只输出JSON数组，如 [\"a\",\"b\",\"c\"]：\n\n" + md_text[:3000]}],
).choices[0].message.content
keywords = json.loads(re.search(r"\[.*\]", kw_resp, re.S).group())

# 2. 去 Pexels 搜图
headers = {"Authorization": os.environ["PEXELS_API_KEY"]}
img_urls = []
for kw in keywords:
    r = requests.get("https://api.pexels.com/v1/search",
                     headers=headers,
                     params={"query": kw, "per_page": 1, "orientation": "landscape"}).json()
    if r.get("photos"):
        img_urls.append(r["photos"][0]["src"]["large"])

IMG_STYLE = "width:100%;border-radius:10px;margin:18px 0;box-shadow:0 2px 8px rgba(0,0,0,0.1);"
CAPTION = '<p style="text-align:center;font-size:12px;color:#999;margin:-10px 0 18px;">▲ 配图与文意呼应，营造阅读氛围</p>'

def img_tag(url):
    return f'<img src="{url}" style="{IMG_STYLE}"/>{CAPTION}'

# 3. 插图：第一张放标题下方当封面，其余插在小标题后
if img_urls:
    html = re.sub(r"(</h1>)", r"\1" + img_tag(img_urls[0]), html, count=1)
    h2s = list(re.finditer(r"</h2>", html))
    for i, m in enumerate(h2s[: len(img_urls) - 1], start=1):
        pos = m.end()
        html = html[:pos] + img_tag(img_urls[i]) + html[pos:]

# 4. 包一层整体底色，让邮件里也有完整配色
final = (
    '<div style="max-width:677px;margin:0 auto;background:#fffdf9;'
    'padding:24px 18px;font-family:-apple-system,PingFang SC,Microsoft YaHei,sans-serif;">'
    + html + "</div>"
)
open(f"output/day{day:02d}_final.html", "w", encoding="utf-8").write(final)
print(f"第{day}集配图完成，共插入 {len(img_urls)} 张图")
