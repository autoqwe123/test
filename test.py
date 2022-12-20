from lesting import Lesting
from line import LINE
import threading
import time
import json

WNER = ["u71f1617925d001be7217ca641db9a646"]

PLAIN_TOKEN = """
TOKEN1
TOKEN2
TOKEN3
TOKEN4
"""
print("พร้อมใช้งานแล้ว!!")
with open("address.json") as f:
    address = json.load(f)

SOURCE = {
    "u39c373a022579c0d3812bc66f94876d3": address["IP1"],
    "ud0dce1996da0b3a47dc4133f7e74bedd": address["IP1"],
    "u0d0c4261648a38cc5de2ed06a0e8ae01": address["IP2"],
    "u90f1c57bb3f0f46cfcaaf1503813f87b": address["IP2"]
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
