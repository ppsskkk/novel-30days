import os
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header

state = json.load(open("state/progress.json", encoding="utf-8"))
day = state["current_day"] - 1
total = state["total_days"]

html = open(f"output/day{day:02d}_final.html", encoding="utf-8").read()
title = open(f"output/day{day:02d}.md", encoding="utf-8").readline().strip("# \n")

msg = MIMEText(html, "html", "utf-8")
msg["Subject"] = Header(f"【第{day}讲/共{total}讲】{title}", "utf-8")
msg["From"] = os.environ["EMAIL_USER"]
msg["To"] = os.environ["EMAIL_TO"]

with smtplib.SMTP_SSL(os.environ["EMAIL_HOST"], 465) as smtp:
    smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
    smtp.sendmail(os.environ["EMAIL_USER"], [os.environ["EMAIL_TO"]], msg.as_string())

print(f"第{day}/{total}集已发送到 {os.environ['EMAIL_TO']}")
