import os
import re

DAYS = 30
text = open("novels/full.txt", encoding="utf-8").read()
target = len(text) // DAYS

# 按"第X章/回/节/卷"或"Chapter N"切分
chunks = re.split(r"(?=(?:第[0-9一二三四五六七八九十百千零两]{1,8}[章节回卷]|Chapter\s+\d+))", text)
chunks = [c for c in chunks if c.strip()]

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
print(f"共拆出 {len(parts)} 份")
