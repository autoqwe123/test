from lesting import Lesting
from line import LINE
import threading
import time
import json

OWNER = ["u71f1617925d001be7217ca641db9a646"]

PLAIN_TOKEN = """
u66c8d86261d634a47adb4a6e0e530a73:aXNzdWVkVG86IHU2NmM4ZDg2MjYxZDYzNGE0N2FkYjRhNmUwZTUzMGE3MwppYXQ6IDE2MTk0NDYwMDM3NzAK.dHlwZTogWVdUCmFsZzogSE1BQ19TSEExCg==.R7zWLseEXDVoomLNChVXCbbyWnc=
u4d98609aa3857f4e6133ab1d7e21f556:aXNzdWVkVG86IHU0ZDk4NjA5YWEzODU3ZjRlNjEzM2FiMWQ3ZTIxZjU1NgppYXQ6IDE2MTk0NTY5NjEyNjEK.dHlwZTogWVdUCmFsZzogSE1BQ19TSEExCg==.ukQ4pvR87zZ7yG2RSLjE+FgRpNY=
u32544c913d2c9af1e0a8302feef41caf:aXNzdWVkVG86IHUzMjU0NGM5MTNkMmM5YWYxZTBhODMwMmZlZWY0MWNhZgppYXQ6IDE2MTk0NTczNTI2MjAK.dHlwZTogWVdUCmFsZzogSE1BQ19TSEExCg==.3yB8tadvnErWKc2fbLexNNWpWW8=
u30351ab66476a528f02ba4f14ddf6896:aXNzdWVkVG86IHUzMDM1MWFiNjY0NzZhNTI4ZjAyYmE0ZjE0ZGRmNjg5NgppYXQ6IDE2MTk0NTkxMTgyMjQK.dHlwZTogWVdUCmFsZzogSE1BQ19TSEExCg==.tJ2lFHW+yUYZWBL4LAEbP+1RoBg=
"""
print("พร้อมใช้งานแล้ว!!")
with open("address.json") as f:
    address = json.load(f)

SOURCE = {
    "u66c8d86261d634a47adb4a6e0e530a73": address["IP1"],
    "u4d98609aa3857f4e6133ab1d7e21f556": address["IP1"],
    "u32544c913d2c9af1e0a8302feef41caf": address["IP2"],
    "u30351ab66476a528f02ba4f14ddf6896": address["IP2"]
}

lesting = Lesting()
for mid in OWNER:
    lesting.user(mid).owner = True

for token in PLAIN_TOKEN.split("\n"):
    token = token.strip()
    if token:
        n = lesting.new(LINE(LINE.Keeper(token), SOURCE[token.split(":")[0]]))
        threading.Thread(target=n.fetch, daemon=True).start()
        threading.Thread(target=n.executor, daemon=True).start()

while True:
    time.sleep(1)
