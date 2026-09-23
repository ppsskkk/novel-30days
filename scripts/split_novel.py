import os
import re

DAYS = 30
text = open("novels/full.txt", encoding="utf-8").read()
target = len(text) // DAYS

# 切分点：独占一行的中文数字序号，如「一」「二」「二十三」「一百零五」
num_pat = re.compile(r"^\s*[零一二三四五六七八九十百]{1,4}\s*$")

lines = text.split("\n")
chunks, buf = [], []
for line in lines:
    if num_pat.match(line) and buf:
        chunks.append("\n".join(buf))   # 遇到新序号，封存上一节
        buf = [line]
    else:
        buf.append(line)
chunks.append("\n".join(buf))
chunks = [c for c in chunks if c.strip()]

# 贪心合并：凑满 1/30 字数就封一份，保证每天阅读量均匀
parts, buf = [], ""
for chunk in chunks:
    buf += chunk
    if len(buf) >= target and len(parts) < DAYS - 1:
        parts.append(buf)
        buf = ""
parts.append(buf)

os.makedirs("novels", exist_ok=True)
for i, part in enumerate(parts, 1):
    open(f"novels/day{i:02d}.txt", "w", encoding="utf-8").write(part)
    print(f"day{i:02d}: {len(part)}字")
print(f"共识别 {len(chunks)} 个小节，合并为 {len(parts)} 份")
