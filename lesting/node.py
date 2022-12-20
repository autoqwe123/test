from queue import Queue
import time
from .utils import format_map
import threading

# PROTECT LESTING VER 2 BY H4CK

PROTECT_LISTALL = {
    "kick": "ระบบป้องกันเตะ",
    "invite": "ระบบป้องกันเชิญ",
    "qrcode": "ระบบป้องกันลิ้งค์กลุ่ม",
    "cancel": "ระบบป้องกันยกเชิญ",
    "join": "ระบบป้องกันเข้ากลุ่ม",
    "flex": "ระบบป้องกันส่งเฟรก",
    "share": "ระบบป้องกันแชร์โพส",
    "album": "ระบบป้องกันสร้างอัลบั้ม",
    "note": "ระบบป้องกันสร้างโน็ต",
    "namegroup": "ระบบป้องกันชื่อกลุ่ม"
}

class Node:
    class Operation:
        TYPE = -99
        ADD_CONTACT_BY_MID = 0
        REQUEST_SQUAD = 1

    def __init__(self, lesting, client):
        self.lesting = lesting
        self.client = client
        self.lesting.local[self.client.profile.mid] = self.client
        self.operations = Queue()
        self.running = False
        self.lesting.user(client.profile.mid).squad = True

    def fetch(self):
        while True:
            self.startup = round(time.time() * 1000)
            self.running = False

            while True:
                ops = self.client.fetchOps()
                for op in ops:
                    if not self.running:
                        if op.createdTime < self.startup:
                            continue
                        self.running = True
                    self.operations.put(op)

    def executor(self):
        while True:
            try:
                threading.Thread(target=self.execute, args=(self.operations.get(),)).start()
            except:
                import traceback
                traceback.print_exc()

    def execute(self, op):

        if op.type == Node.Operation.TYPE:
            if op.action == Node.Operation.ADD_CONTACT_BY_MID:
                if op.mid not in self.client.contacts:
                    self.client.findAndAddContactsByMid(op.mid)
                    self.client.contacts.append(op.mid)
                    
            if op.action == Node.Operation.REQUEST_SQUAD:
                self.lesting.squad.apply(op.ticket, self.client.profile.mid)

        if op.type in [11, 122]:

            chat = self.lesting.chat(op.param1)
            param2 = self.lesting.user(op.param2)

            if self.client.profile.mid not in chat.squad:
                return
            if op.param1 not in self.lesting.data.type["rank"]["admin"] and op.param1 not in self.lesting.data.type["rank"]["blacklist"]:
                return 

            if op.param3 == 1:
                if op.param1 in self.lesting.data.type["protect"]["namegroup"] and self.lesting.data.type["protect"]["namegroup"][op.param1]["status"]:
                    if not (param2.squad or param2.owner):
                        if param2.key not in self.lesting.data.type["rank"]["admin"][op.param1]:
                            if self.lesting.messenger(op):
                                group = self.client.getChat(op.param1)
                                if self.lesting.data.type["protect"]["namegroup"][op.param1]["name"] != None:
                                    if group.name != self.lesting.data.type["protect"]["namegroup"][op.param1]["name"]:
                                        if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                                            self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                                        threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                                        group.name = self.lesting.data.type["protect"]["namegroup"][op.param1]["name"]
                                        threading.Thread(target=self.client.updateChat, args=(group, 1,)).start()

            elif op.param3 == 4:
                if op.param1 in self.lesting.data.type["protect"]["qrcode"] and self.lesting.data.type["protect"]["qrcode"][op.param1]["status"]:
                    if not (param2.squad or param2.owner):
                        if param2.key not in self.lesting.data.type["rank"]["admin"][op.param1]:
                            if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                                self.data.type["rank"]["blacklist"][op.param1].append(param2.key) 
                            if self.lesting.messenger(op):
                                threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                                group = self.client.getChat(op.param1)
                                if group.extra.groupExtra.preventedJoinByTicket == False:
                                    group.extra.groupExtra.preventedJoinByTicket = True
                                    threading.Thread(target=self.client.updateChat, args=(group, 4,)).start()

        if op.type in [19, 133]:

            chat  = self.lesting.chat(op.param1)
            param2 = self.lesting.user(op.param2)
            param3 = self.lesting.user(op.param3)

            if self.client.profile.mid not in chat.squad:
                return

            if op.param1 not in self.lesting.data.type["rank"]["admin"] and op.param1 not in self.lesting.data.type["rank"]["blacklist"]:
                return 

            if op.param1 in self.lesting.data.type["protect"]["kick"] and self.lesting.data.type["protect"]["kick"][op.param1]["status"]:
                if not (param2.squad or param2.owner):
                    if param2.key not in self.lesting.data.type["rank"]["admin"][op.param1]:
                        if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                            self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                        if self.lesting.messenger(op, "a"):
                            threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()

            if param2.squad or param2.owner:
                return

            if param3.key in chat.squad:
                if param2.key in self.lesting.data.type["rank"]["admin"][op.param1]:
                    return

               if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                    self.data.type["rank"]["blacklist"][op.param1].append(param2.key)

                if param3.key == self.client.profile.mid:
                    return

                if self.lesting.messenger(op, "a"):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                    group = self.client.chats[op.param1]
                    squad = {mid for mid in chat.squad if mid not in group.members}
                    invites = {mid for mid in squad if mid not in group.invites}
                    if param3.key not in invites:
                        invites.add(param3.key)
                    threading.Thread(target=self.client.inviteIntoChat, args=(chat.key, invites)).start()

                elif self.lesting.messenger(op, "b"):
                    for mid in self.client.chats[op.param1].members:
                        if mid == param2.key:
                            continue
                        if self.lesting.user(mid).blacklist:
                            threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {mid})).start()
        
            elif param3.owner:
                if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                    self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                if self.lesting.messenger(op, "a"):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                    if param3.key not in self.client.contacts:
                        self.client.findAndAddContactsByMid(param3.key)
                    threading.Thread(target=self.client.inviteIntoChat, args=(op.param1, {param3.key})).start()

            elif param3.key in self.lesting.data.type["rank"]["admin"][op.param1]:
                if param2.key in self.lesting.data.type["rank"]["admin"][op.param1]:
                    return
                if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                    self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                if self.lesting.messenger(op, "a"):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                    if param3.key not in self.client.contacts:
                        self.client.findAndAddContactsByMid(param3.key)
                    threading.Thread(target=self.client.inviteIntoChat, args=(op.param1, {param3.key})).start()

        if op.type in [13, 124]:
            chat   = self.lesting.chat(op.param1)
            param2 = self.lesting.user(op.param2)

            if self.client.profile.mid in op.param3:
                if param2.squad or param2.owner or self.client.profile.mid in chat.squad:
                    threading.Thread(target=self.client.acceptChatInvitation, args=(op.param1,)).start()
                else:
                    return

            if self.client.profile.mid not in chat.squad:
                return

            if op.param1 not in self.lesting.data.type["rank"]["admin"] and op.param1 not in self.lesting.data.type["rank"]["blacklist"]:
                return 

            param3 = [self.lesting.user(mid) for mid in op.param3.split("\x1e")]
            if op.param1 in self.lesting.data.type["protect"]["invite"] and self.lesting.data.type["protect"]["invite"][op.param1]["status"]:
                if not (param2.squad or param2.owner):
                    if param2.key not in self.lesting.data.type["rank"]["admin"][op.param1]:
                        if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                            self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                        if self.lesting.messenger(op, "a"):
                            threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                            for user in param3:
                                if not (user.squad or user.owner):
                                    if user.key not in self.lesting.data.type["rank"]["admin"][op.param1]:
                                        if user.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                                            self.data.type["rank"]["blacklist"][op.param1].append(user.key)
                                        threading.Thread(target=self.client.cancelChatInvitation, args=(op.param1, {user.key})).start()

            if param2.squad or param2.owner:
                return

            if param2.key in self.data.type["rank"]["blacklist"][op.param1] or any(mid for mid in param3 if mid in self.data.type["rank"]["blacklist"][op.param1]):
                if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                    self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                for user in param3:
                    if user.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                        self.data.type["rank"]["blacklist"][op.param1].append(user.key)

                if self.lesting.messenger(op, "a"):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                    for user in param3:
                        threading.Thread(target=self.client.cancelChatInvitation, args=(op.param1, {user.key})).start()

        if op.type in [17, 130]:
            param2 = self.lesting.user(op.param2)
            if param2.squad:
                return
            if op.param1 not in self.lesting.data.type["rank"]["admin"] and op.param1 not in self.lesting.data.type["rank"]["blacklist"]:
                return 
            if param2.key in self.data.type["rank"]["blacklist"][op.param1]
                if self.lesting.messenger(op):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
            
            if op.param1 in self.lesting.data.type["protect"]["join"] and self.lesting.data.type["protect"]["join"][op.param1]["status"]:
                if not (param2.squad or param2.owner):
                    if param2.key not in self.lesting.data.type["rank"]["admin"][op.param1]:
                        if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                            self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                        if self.lesting.messenger(op, "a"):
                            threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
            
        if op.type in [32, 126]:
            chat  = self.lesting.chat(op.param1)
            param2 = self.lesting.user(op.param2)
            if self.client.profile.mid not in chat.squad:
                return
            if op.param1 not in self.lesting.data.type["rank"]["admin"] and op.param1 not in self.lesting.data.type["rank"]["blacklist"]:
                return
            if op.param1 in self.lesting.data.type["protect"]["cancel"] and self.lesting.data.type["protect"]["cancel"][op.param1]["status"]:
                if not (param2.squad or param2.owner):
                    if param2.key not in self.lesting.data.type["rank"]["admin"][op.param1]:
                        if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                            self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                        if self.lesting.messenger(op, "a"):
                            threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()

            param3 = self.lesting.user(op.param3)
            if param3.key in chat.squad:
                if param2.key in self.lesting.data.type["rank"]["admin"][op.param1]:
                    return
                if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                   self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                if param3.key == self.client.profile.mid:
                    return
                if self.lesting.messenger(op, "a"):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(chat.key, {param2.key}, )).start()
                    threading.Thread(target=self.client.inviteIntoChat, args=(chat.key, {param3.key}, )).start()

            elif param3.owner:
                if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                    self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                if self.lesting.messenger(op, "a"):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                    if param3.key not in self.client.contacts:
                        self.client.findAndAddContactsByMid(param3.key)
                    threading.Thread(target=self.client.inviteIntoChat, args=(op.param1, {param3.key})).start()

            elif param3.key in self.lesting.data.type["rank"]["admin"][op.param1]:
                if param2.key in self.lesting.data.type["rank"]["admin"][op.param1]:
                    return
                if param2.key not in self.lesting.data.type["rank"]["blacklist"][op.param1]["mid"]:
                    self.data.type["rank"]["blacklist"][op.param1].append(param2.key)
                if self.lesting.messenger(op, "a"):
                    threading.Thread(target=self.client.deleteOtherFromChat, args=(op.param1, {param2.key})).start()
                    if param3.key not in self.client.contacts:
                        self.client.findAndAddContactsByMid(param3.key)
                    threading.Thread(target=self.client.inviteIntoChat, args=(op.param1, {param3.key})).start()


        if op.type in [26]:
            msg = op.message
            to  = msg.to
            chat = self.lesting.chat(msg.to)
            user = self.lesting.user(msg._from)
            if msg.contentType == 0:
                text = msg.text
                if text is None: # E2EE was enable
                    return
                
                command, args = self.lesting.command(text)
                
                if user.owner:
                    if command == "install":
                        if self.lesting.messenger(op):
                            if to not in self.lesting.data.type["settings"]["setup"]:
                                self.lesting.data.type["settings"]["setup"][to] = True
                                if to not in self.lesting.data.type["rank"]["admin"]:
                                    self.lesting.data.type["rank"]["admin"][to] = {}
                                if to not in self.lesting.data.type["rank"]["blacklist"]:
                                    self.lesting.data.type["rank"]["blacklist"][to] = {}
                                for protect in PROTECT_LISTALL:
                                    if protect == "namegroup":
                                        self.lesting.data.type["protect"][protect][to] = {"status": False, "name": None}
                                    else:
                                        self.lesting.data.type["protect"][protect][to] = {"status": False}
                                client.sendMessage(to, "ติดตั้งเสร็จสิ้นแล้ว.")
                            else:
                                client.sendMessage(to, "คุณได้ทำการติดตั้งไปแล้ว.")

                    if command == "uninstall":
                        if self.lesting.messenger(op):
                            if to in self.lesting.data.type["settings"]["setup"]:
                                del self.lesting.data.type["settings"]["setup"][to]
                                del self.lesting.data.type["rank"]["admin"][to]
                                del self.lesting.data.type["rank"]["blacklist"][to]
                                for protect in PROTECT_LISTALL:
                                    del self.lesting.data.type["protect"][protect][to]
                                client.sendMessage(to, "ถอนการติดตั้งเสร็จสิ้นแล้ว.")
                                square = [mid for mid in self.lesting.local if mid in self.client.chats[to].members]
                                if square:
                                    for mid in square:
                                        self.lesting.local[mid].deleteSelfFromChat(to)
                            else:
                                client.sendMessage(to, "คุณไม่ได้ทำการติดตั้งอยู่แล้ว.")

            if to not in self.lesting.data.type["rank"]["admin"] and to not in self.lesting.data.type["rank"]["blacklist"]:
                return
            if msg.toType == 2:
                if not (user.squad or user.owner):
                    if to in self.lesting.data.type["rank"]["admin"] and user.key not in self.lesting.data.type["rank"]["admin"][to]:
                        if to in self.lesting.data.type["protect"]["flex"] and self.lesting.data.type["protect"]["flex"][to]["status"]:
                            if msg.contentType == 22:
                                if self.lesting.messenger(op, "a"):
                                    threading.Thread(target=self.client.deleteOtherFromChat, args=(to, {user.key}, )).start()
                            if "USE_FULL_WIDTH" in msg.contentMetadata:
                                if self.lesting.messenger(op, "a"):
                                    threading.Thread(target=self.client.deleteOtherFromChat, args=(to, {user.key}, )).start()
                        if to in self.lesting.data.type["protect"]["share"] and self.lesting.data.type["protect"]["share"][to]["status"]:
                            if msg.contentType == 16 and msg.contentMetadata["serviceType"] == "MH":
                                if self.lesting.messenger(op, "a"):
                                    threading.Thread(target=self.client.deleteOtherFromChat, args=(to, {user.key}, )).start()
                        if to in self.lesting.data.type["protect"]["album"] and self.lesting.data.type["protect"]["album"][to]["status"]:
                            if "LOC_KEY" in msg.contentMetadata and msg.contentMetadata["LOC_KEY"] == "BD":
                                if self.lesting.messenger(op, "a"):
                                    threading.Thread(target=self.client.deleteOtherFromChat, args=(to, {user.key}, )).start()
                        if to in self.lesting.data.type["protect"]["note"] and self.lesting.data.type["protect"]["note"][to]["status"]:
                            if msg.contentType == 16 and msg.contentMetadata["serviceType"] == "GB":
                                if self.lesting.messenger(op, "a"):
                                    threading.Thread(target=self.client.deleteOtherFromChat, args=(to, {user.key}, )).start()

            if msg.contentType == 0:
                text = msg.text
                if text is None: # E2EE was enable
                    return
                
                command, args = self.lesting.command(text)
                
                if user.owner:
                    if command == "help":
                        if self.lesting.messenger(op):
                            text = "\n".join([
                                "lesting protect:",
                                "- speed",
                                "- protect [type]",
                                "- admin [type]",
                                "- blacklist [type]",
                                "- setup",
                                "- uninstall",
                                "- in [count]",
                                "- reinvite",
                                "- kick (@)",
                                "- status",
                                "- leave",
                            ])
                            self.client.sendMessage(to, text)

                    if command == "speed":
                        if self.client.profile.mid not in chat.squad:
                            return
                        if "a" not in args or self.lesting.messenger(op):
                            c = 1
                            if "c" in args:
                                ci = args.index("c") + 1
                                if len(args) > ci:
                                    cs = args[ci]
                                    if cs.isdigit():
                                        c = int(cs)
    
                            def test():
                                s = time.time()
                                self.client.getProfile()
                                e = time.time() - s
                                self.client.sendMessage(to, "%s [%s ms]" % (str(e)[:7], int(e*1000)))
    
                            for _ in range(c):
                                test()
    
                    if command == "limit": 
                        if self.client.profile.mid not in chat.squad:
                            return
                        try:
                            self.client.inviteIntoChat(to, {self.client.profile.mid})
                            limit = False
                        except:
                            limit = True
                        self.client.sendMessage(to, "limit" if limit else "ready")
    
                    if command == "kick":
                        if self.client.profile.mid not in chat.squad:
                            return
                        if self.lesting.messenger(op):
                            MENTION = msg.contentMetadata.get("MENTION", None)
                            if MENTION:
                                chat = self.client.chats[to]
                                MENTIONEES = eval(MENTION)["MENTIONEES"]
                                for mention in MENTIONEES:
                                    if mention["M"] in chat.members:
                                        self.lesting.user(mention["M"]).blacklist = True
                                        self.client.deleteOtherFromChat(to, {mention["M"]})
    
                    if command == "reinvite": 
                        if self.lesting.messenger(op):
                            chat = self.lesting.chat(to)
                            if chat.squad == []:
                                self.client.sendMessage(to, "no squad on this group")
                                return
                            group = self.client.chats[to]
                            invites = {mid for mid in chat.squad if mid not in group.members and mid not in group.invites}
                            if invites:
                                self.client.inviteIntoChat(to, invites)
                            else:
                                self.client.sendMessage(to, "squad already on group")
    
                    if command == "in":
                        if self.lesting.messenger(op):
                            if len(args) >= 1:
                                if not args[0].isdigit():
                                    self.client.sendMessage(to, "in [count:int]")
                                    return
                                chat = self.lesting.chat(to)
                                count = int(args[0])
                                if count == 0:
                                    chat.squad = []
                                    self.client.sendMessage(to, "delete squad")
                                    return
                                accept = self.lesting.squad.request(count, self.client.profile.mid)
                                if not accept:
                                    self.client.sendMessage(to, "no accept squad")
                                    return
                                chat.squad = accept
                                group = self.client.chats[to]
                                invites = {mid for mid in chat.squad if mid not in group.members and mid not in group.invites}
                                self.client.sendMessage(to, "squad: %s" % (count))
                                if invites:
                                    self.client.inviteIntoChat(to, invites)
                            else:
                                self.client.sendMessage(to, "in [count:int]")

                    if command == "blacklist":
                        if self.client.profile.mid not in chat.squad:
                            return
                        if self.lesting.messenger(op):
                            if len(args) >= 1:
                                toggle = args[0]
                                MENTION = msg.contentMetadata.get("MENTION", None)
                                if MENTION:
                                    chat = self.client.chats[to]
                                    MENTIONEES = eval(MENTION)["MENTIONEES"]
                                    for mention in MENTIONEES:
                                        if mention["M"] in chat.members:
                                            if toggle == "apply":
                                                if mention["M"] not in self.lesting.data.type["rank"]["blacklist"][to]:
                                                    self.lesting.data.type["rank"]["blacklist"][to].append(mention["M"])
                                                    self.client.sendMessage(to, "เพิ่มเสร็จสิ้น")
                                                else:
                                                    self.client.sendMessage(to, "อยู่ในระบบอยู่แล้ว")
                                            elif toggle == "remove":
                                                if mention["M"] in self.lesting.data.type["rank"]["blacklist"][to]:
                                                    self.lesting.data.type["rank"]["blacklist"][to].remove(mention["M"])
                                                    self.client.sendMessage(to, "ลบเสร็จสิ้น")
                                                else:
                                                    self.client.sendMessage(to, "ไม่ได้อยู่ในระบบอยู่แล้ว")
                            else:
                                if not self.lesting.data.type["rank"]["blacklist"][to]:
                                    self.client.sendMessage(to, "ไม่พบข้อมูล")
                                else:
                                    text = "รายชื่อดำของกลุ่มนี้:\n"
                                    text += "\n".join([f'- {self.client.getContact(mid).displayName}' for mid in self.lesting.data.type["rank"]["blacklist"][to]])
                                    self.client.sendMessage(to, text)

                    if command == "admin":
                        if self.client.profile.mid not in chat.squad:
                            return
                        if self.lesting.messenger(op):
                            if len(args) >= 1:
                                toggle = args[0]
                                MENTION = msg.contentMetadata.get("MENTION", None)
                                if MENTION:
                                    chat = self.client.chats[to]
                                    MENTIONEES = eval(MENTION)["MENTIONEES"]
                                    for mention in MENTIONEES:
                                        if mention["M"] in chat.members:
                                            if toggle == "apply":
                                                if mention["M"] not in self.lesting.data.type["rank"]["admin"][to]:
                                                    self.lesting.data.type["rank"]["admin"][to].append(mention["M"])
                                                    self.client.sendMessage(to, "เพิ่มเสร็จสิ้น")
                                                else:
                                                    self.client.sendMessage(to, "อยู่ในระบบอยู่แล้ว")
                                            elif toggle == "remove":
                                                if mention["M"] in self.lesting.data.type["rank"]["admin"][to]:
                                                    self.lesting.data.type["rank"]["admin"][to].remove(mention["M"])
                                                    self.client.sendMessage(to, "ลบเสร็จสิ้น")
                                                else:
                                                    self.client.sendMessage(to, "ไม่ได้อยู่ในระบบอยู่แล้ว")
                            else:
                                if not self.lesting.data.type["rank"]["admin"][to]:
                                    self.client.sendMessage(to, "ไม่พบข้อมูล")
                                else:
                                    text = "รายชื่อแอดมินกลุ่ม:\n"
                                    text += "\n".join([f'- {self.client.getContact(mid).displayName}' for mid in self.lesting.data.type["rank"]["admin"][to]])
                                    self.client.sendMessage(to, text)

                    if command == "protect":
                        if self.client.profile.mid not in chat.squad:
                            return
                        if self.lesting.messenger(op):
                            if len(args) >= 1:
                                cmd = args[0]
                                if cmd == "list":
                                    text = "\n".join(["ระบบป้องกันของกลุ่มนีั:"] + ["- %s %s" %(NAME, "เปิด" if self.lesting.data.type["protect"][PRO][to]["status"] else "ปิด") for PRO, NAME in PROTECT_LISTALL.items()])
                                    client.sendMessage(to, text)
                                elif cmd in PROTECT_LISTALL:
                                    PROTECT = args[0]
                                    toggle = args[1]
                                    if toggle == "on":
                                        if self.lesting.data.type["protect"][PROTECT][to]["status"]:
                                            self.client.sendMessage(to, "เปิดอยู่แล้ว")
                                        else:
                                            self.lesting.data.type["protect"][PROTECT][to]["status"] = True
                                            if PROTECT == "namegroup":
                                                self.lesting.data.type["protect"][PROTECT][to]["name"] = self.client.getChat(to).name
                                            self.client.sendMessage(to, "เปิดเสร็จสิ้น")
                                    elif toggle == "off":
                                        if not self.lesting.data.type["protect"][PROTECT][to]["status"]:
                                            self.client.sendMessage(to, "ปิดอยู่แล้ว")
                                        else:
                                            self.lesting.data.type["protect"][PROTECT][to]["status"] = False
                                            if PROTECT == "namegroup":
                                                self.lesting.data.type["protect"][PROTECT][to]["name"] = ""
                                            self.client.sendMessage(to, "ปิดเสร็จสิ้น")

                    if command == "exec":
                        if self.lesting.messenger(op):
                            try:
                                exec(" ".join(args).strip())
                            except:
                                import traceback
                                error = traceback.format_exc()
                                self.client.sendMessage(to, str(error).strip())
    
                    if command == "change":
                        name = " ".join(args)
                        name = name.replace("{index}", str(list(self.lesting.local).index(self.client.profile.mid) + 1))
                        self.client.profile.displayName = name
                        self.client.updateProfile(self.client.profile)
                        self.client.sendMessage(to, "successfully update display name")
    
                    if command == "leave":
                        self.client.deleteSelfFromChat(to)