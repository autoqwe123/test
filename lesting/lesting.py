from .storage import Storage
from .command import Command
from .messenger import Messenger
from .node import Node
import time
import livejson

class Lesting:

    class Core:

        def __init__(self, lesting):
            self.lesting = lesting

        def handler_user(self, mid, user):
            if user.get("squad"):
                self.lesting.node.operation(Node.Operation.ADD_CONTACT_BY_MID, mid=mid)

    class User(Storage):
        attributes = {
            "squad"     : False,
            "owner"     : False,
        }

        def __init__(self, lesting):
            super(Lesting.User, self).__init__()
            self.handler = lesting.core.handler_user

    class Chat(Storage):
        attributes = {
            "squad": [],
            "mode": 0,
            "war": False
        }

        def __init__(self, lesting):
            super(Lesting.Chat, self).__init__()

    class Command(Command):
        def __init__(self, lesting):
            super(Lesting.Command, self).__init__()

    class Messenger(Messenger):
        def __init__(self, lesting):
            super(Lesting.Messenger, self).__init__()

    class Node:
        def __init__(self, lesting):
            self.lesting = lesting
            self.nodes = []
            self.notify = []

        def __call__(self, node):
            for mid in self.lesting.user.values:
                if self.lesting.user(mid).squad and mid != node.client.profile.mid:
                    node.operations.put(type("Operation", (object,), { **{ "type": Node.Operation.TYPE, "action": Node.Operation.ADD_CONTACT_BY_MID, "mid": mid}})())
            self.nodes.append(node)
            self.lesting.user(node.client.profile.mid).squad = True
            for mid in self.lesting.user.values:
                if self.lesting.user(mid).owner:
                    node.client.sendMessage(mid, "ʀᴜɴ ᴋɪᴄᴋ ʀᴇᴀᴅʏ")

        def operation(self, action, **args):
            op = type("Operation", (object,), { **{ "type": Node.Operation.TYPE, "action": action}, **args})()
            for node in self.nodes:
                node.operations.put(op)

    class Squad:
        def __init__(self, lesting):
            self.lesting  = lesting
            self.requests = {}

        def apply(self, ticket, mid):
            if ticket in self.requests:
                self.requests[ticket].append(mid)

        def request(self, count, mid, timeout=2):
            timeout = time.time() + timeout
            ticket = time.time()
            self.lesting.node.operation(Node.Operation.REQUEST_SQUAD, ticket=ticket,)
            self.requests[ticket] = [mid]
            while len(self.requests[ticket]) < count and timeout > time.time():
                time.sleep(0)
            accept = self.requests[ticket][:count]
            del self.requests[ticket]
            return accept

    class Data:

        def __init__(self, lesting):
            self.lesting  = lesting
            self.type = livejson.File("data.json")
            if "settings" not in self.type:
                self.type["settings"] = {
                    "setup": {}
                }
            if "protect" not in self.type:
                self.type["protect"] = {
                    "kick": {},
                    "invite": {},
                    "qrcode": {},
                    "cancel": {},
                    "join": {},
                    "flex": {},
                    "share": {},
                    "namegroup": {},
                    "album": {},
                    "note": {}
                }
            if "rank" not in self.type:
                self.type["rank"] = {
                    "admin": {},
                    "blacklist": {}
                }

    def __init__(self):
        self.node = Lesting.Node(self)
        self.core = Lesting.Core(self)
        self.local = {}
        self.user = Lesting.User(self)
        self.chat = Lesting.Chat(self)
        self.command = Lesting.Command(self)
        self.messenger = Lesting.Messenger(self)
        self.squad = Lesting.Squad(self)
        self.data = Lesting.Data(self)

    def new(self, client):
        node = Node(self, client)
        self.node(node)
        return node
