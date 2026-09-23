import os
import re
import json
import glob
from openai import OpenAI

MAX_DAYS = 10

text = open("novels/full.txt", encoding="utf-8").read()
total_chars = len(text)

# 第一步：按"独占一行的中文数字序号"切出所有小节
num_pat = re.compile(r"^\s*[零一二三四五六七八九十百]{1,4}\s*$")
lines = text.split("\n")
chunks, buf = [], []
for line in lines:
    if num_pat.match(line) and buf:
        chunks.append("\n".join(buf))
        buf = [line]
    else:
        buf.append(line)
chunks.append("\n".join(buf))
chunks = [c for c in chunks if c.strip()]
print(f"全书 {total_chars} 字，识别到 {len(chunks)} 个小节")

# 第二步：让 AI 决定分几天讲完
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": f"""我在为长篇小说做公众号连载解读，需要制定阅读计划。

全书信息：总字数约 {total_chars//10000} 万字，共 {len(chunks)} 个序号小节。

请在【不超过{MAX_DAYS}天】的前提下，决定分几天讲完。考虑：
- 每天阅读量控制在3~8万字比较合适
- 天数尽量少，读者追更压力小
- 返回JSON，只要一个字段，如 {{"days": 7}}"""}],
).choices[0].message.content

days = json.loads(re.search(r"\{.*\}", resp, re.S).group())["days"]
days = max(1, min(MAX_DAYS, int(days)))
print(f"AI 决定：分 {days} 天讲完")

# 第三步：小节不够时对半劈长节，再按字数均匀合并成 days 份
target = total_chars // days
while len(chunks) < days:
    i = max(range(len(chunks)), key=lambda k: len(chunks[k]))
    biggest = chunks.pop(i)
    mid = len(biggest) // 2
    chunks.insert(i, biggest[mid:])
    chunks.insert(i, biggest[:mid])

parts, buf = [], ""
for chunk in chunks:
    buf += chunk
    if len(buf) >= target and len(parts) < days - 1:
        parts.append(buf)
        buf = ""
parts.append(buf)
while len(parts) < days:
    parts.append("")

# 第四步：清掉旧文件，写入新的拆分结果
for f in glob.glob("novels/day*.txt") + glob.glob("output/*"):
    os.remove(f)
os.makedirs("novels", exist_ok=True)
for i, part in enumerate(parts[:days], 1):
    open(f"novels/day{i:02d}.txt", "w", encoding="utf-8").write(part)
    print(f"day{i:02d}: {len(part)}字")

# 第五步：重置进度文件，记下总天数
os.makedirs("state", exist_ok=True)
json.dump({"current_day": 1, "total_days": days, "summaries": []},
          open("state/progress.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"拆分完成，共 {days} 份")
