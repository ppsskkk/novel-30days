import re
import glob
import markdown

CSS_MAP = {
    "h1": "font-size:22px;font-weight:bold;text-align:center;color:#2c3e50;margin:20px 0;",
    "h2": "font-size:17px;font-weight:bold;color:#c0392b;border-left:4px solid #c0392b;padding-left:10px;margin:28px 0 14px;",
    "p": "font-size:15px;line-height:1.9;color:#3f3f3f;margin:14px 0;text-align:justify;",
}

for md_path in sorted(glob.glob("output/*.md")):
    name = md_path.rsplit("/", 1)[-1].replace(".md", "")
    html_path = f"output/{name}_wechat.html"

    html = markdown.markdown(open(md_path, encoding="utf-8").read(), extensions=["extra"])
    for tag, style in CSS_MAP.items():
        html = re.sub(f"<{tag}>", f'<{tag} style="{style}">', html)
    html = html.replace(
        "<blockquote>",
        '<blockquote style="border-left:3px solid #c0392b;background:#fdf6f5;'
        'padding:12px 16px;margin:16px 0;color:#7f8c8d;">',
    )

    open(html_path, "w", encoding="utf-8").write(html)
    print(f"已排版: {html_path}")
