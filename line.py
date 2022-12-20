""" Compact LINE messenger module
"""

# thrift
from thrift.protocol.TCompactProtocol import TCompactProtocolFactory
from thrift.transport.TTransport import TTransportBase

# service
from service.ttypes import *
from service import LineService
from akad import TalkService

# other
from contextlib import contextmanager
from io import BytesIO
import threading
import modhttplib2
import pickle
import hashlib
import time
import json
import os
import queue
import copy

MAX_CONNECTIONS = 100

def ModThriftClient(client):

    class ThriftClient:
        def __init__(self, client, transport):
            self._iprot = self._oprot = client._iprot.getProtocol(transport)
            if not self._iprot is self._oprot:
                self._oprot = client._oprot.getProtocol(transport)
            self._seqid = client._seqid

    def __init__(self, transport, iProtocolFactory, oProtocolFactory=None):
        self._iprot = self._oprot = iProtocolFactory
        if oProtocolFactory is not None:
            self._oprot = oProtocolFactory
        self._trans = transport
        self._seqid = 0

    setattr(client, "__init__", __init__)

    for name in dir(client):
        if (name[:2] == "__" and name[-2:] == "__") or name[:5] in ["send_", "recv_"]:
            continue

        if all(hasattr(client, "_".join([key, name])) for key in ["send", "recv"]):
            def create(func):
                send = getattr(client, "send_%s" % (func))
                recv = getattr(client, "recv_%s" % (func))
                def wrapper(self, *args, **kwargs):
                    with self._trans.getTransport() as transport:
                        client = ThriftClient(self, transport)
                        send(client, *args, **kwargs)
                        result = recv(client)
                    return result
                return wrapper

            setattr(client, name, create(name))

    return client

class LINE:
    """ LINE """

    class Config:
        """ LINE Config """

        # Headers
    #    USER_AGENT = "LLA/2.14.0 Nokia Plus "
    #    APPLICATION = "ANDROIDLITE\t2.14.0\tAndroid OS\t10"
        
        USER_AGENT = "LLA/2.17.0 vivo 1818 10"
        APPLICATION = "ANDROIDLITE\t2.17.0\tAndroid OS\t10"
        
        #USER_AGENT = "Line/10.16.1"
        #APPLICATION = "IOS\t10.16.1\tiPhone OS\t13.5.2"
        
        # Config
        REALTIME_CHATS = True
        FETCH_OPS_COUNT = 100
        
        # Keeper
        KEEPER_FILE_EXTENSION_NAME = "keeper"
        KEEPER_THREAD = False
        KEEPER_THREAD_SLEEP_INTERVAL = 10
        
        # Connection
        LINE_OBS_DOMAIN = "https://obs.line-apps.com"
        LINE_HOST = "https://legy-jp-addr-long.line.naver.jp"
        TALK_PATH = "/S4"
        POLL_PATH = "/P4"

        # Service
        CONNECTOR = {
            "mess": (TALK_PATH, TalkService.Client),
            "talk": (TALK_PATH, LineService.Client),
            "poll": (POLL_PATH, LineService.Client),
        }
        PROTOCOL = TCompactProtocolFactory

    class Keeper:
        """ LINE Keeper """
        __slots__ = {
            "token": None,
            "localRev": 0,
            "globalRev": 0,
            "individualRev": 0
        }

        def __init__(keeper, token):
            for attr, value in keeper.__slots__.items():
                setattr(keeper, attr, value)
            keeper.token = token
            keeper.load()

            if LINE.Config.KEEPER_THREAD:
                threading.Thread(target=keeper.auto, daemon=True).start()

        def load(keeper):
            try:
                with open(".".join([hashlib.md5(keeper.token.encode("utf-8")).hexdigest(), LINE.Config.KEEPER_FILE_EXTENSION_NAME]), "rb") as f:
                    for attr, value in pickle.load(f).items():
                        if attr in keeper.__slots__:
                            setattr(keeper, attr, value)
            except (FileNotFoundError, EOFError, pickle.UnpicklingError):
                return False
            return True

        def dump(keeper):
            return pickle.dumps({attr: getattr(keeper, attr, None) for attr in keeper.__slots__})

        def save(keeper):
            with open(".".join([hashlib.md5(keeper.token.encode("utf-8")).hexdigest(), LINE.Config.KEEPER_FILE_EXTENSION_NAME]), "wb+") as f:
                f.write(keeper.dump())

        def auto(keeper):
            while True:
                keeper.save()
                time.sleep(LINE.Config.KEEPER_THREAD_SLEEP_INTERVAL)

    class Session:
        """ LINE Session """

        class THttpClient:

            class Transport(TTransportBase):
                """ LINE Session Transport """

                def __init__(transport, client):
                    transport.client = client
                    transport.http = None
                    transport.last_read = 0
                    transport.wbuf = BytesIO()
                    transport.lock = threading.Lock()

                def isOpen(transport):
                    return transport.http is not None

                def open(transport):
                    transport.http = modhttplib2.Http(transport.client.session.line.source_ip, disable_ssl_certificate_validation=True)

                def close(transport):
                    if transport.isOpen():
                        transport.http.close()
                    transport.http = None
                    transport.last_read = 0
                    
                def read(transport, sz):
                    max_sz = transport.last_read + sz
                    min_sz = transport.last_read
                    transport.last_read = max_sz
                    return transport.data[min_sz:max_sz]

                def write(transport, buf):
                    transport.wbuf.write(buf)

                def flush(transport):
                    if not transport.isOpen():
                        transport.open()
                    data = transport.wbuf.getvalue()
                    transport.wbuf = BytesIO()
                    headers = {**{"Content-Type": "application/x-thrift"}, **transport.client.session.headers}
                    transport.response, transport.data = transport.http.request(transport.client.url, "POST", headers=headers, body=data)
                    transport.code = transport.response.status
                    transport.message = transport.response.reason
                    transport.headers = transport.response
                    transport.last_read = 0

            def __init__(self, client):
                self.client = client
                self.transportQueue = queue.LifoQueue(MAX_CONNECTIONS)
                self.semaphore = threading.BoundedSemaphore(MAX_CONNECTIONS)

            def createTransport(self):
                return self.Transport(self.client)

            @contextmanager
            def getTransport(self):
                self.semaphore.acquire()
                try:
                    transport = self.transportQueue.get(block=False)
                except queue.Empty:
                    try:
                        transport = self.createTransport()
                    except:
                        self.semaphore.release()
                        raise
                try:
                    yield transport
                finally:
                    self.transportQueue.put(transport)
                    self.semaphore.release()

        class Client:
            """ LINE Session Client """
        
            def __init__(client, session, path, service):
                client.session = session
                client.path = path
                client.url = session.line.config.LINE_HOST + client.path
                client.transport = LINE.Session.THttpClient(client)
                client.service = ModThriftClient(copy.deepcopy(service))(client.transport, session.line.config.PROTOCOL())

        def __init__(session, line):
            assert isinstance(line, LINE)
            session.line = line
            session.headers = {
                "User-Agent": line.config.USER_AGENT,
                "X-Line-Application": line.config.APPLICATION,
                "X-Line-Access": session.line.keeper.token,
                "X-lal": "en_US",
            }
            session.connector = {name: LINE.Session.Client(session, *value) for name, value in line.config.CONNECTOR.items()}

        def __getattr__(session, key):
            if key in session.connector: return session.connector[key].service

    class RequestSequence:
        """ LINE Request Sequence """
    
        def __init__(reqSeq):
            reqSeq._map = {}
        
        def __getitem__(reqSeq, key):
            if key not in reqSeq._map:
                reqSeq._map[key] = -1
            reqSeq._map[key] += 1
            return reqSeq._map[key]

        def __setitem__(reqSeq, key, value):
            reqSeq._map[key] = value

        def __delitem__(reqSeq, key):
            del reqSeq._map[key]

    class RealtimeChats:
        """ LINE Realtime Chats """
        
        class Chat:
            __slots__ = (
                "chatMid",
                "chatName",
                "type",
                "members",
                "invites",
            )
        
            def __init__(rtchat, chat):
                rtchat.chatMid = chat.chatMid
                rtchat.chatName = chat.chatName
                rtchat.type = chat.type
                if rtchat.type in [ChatType.GROUP, ChatType.ROOM]:
                    rtchat.members = list(chat.extra.groupExtra.memberMids)
                    rtchat.invites = list(chat.extra.groupExtra.inviteeMids)
                else:
                    rtchat.members = []
                    rtchat.invites = []

            def __repr__(rtchat):
                return "%s(%s)" % (rtchat.__class__.__name__, ", ".join(["%s=%r" % (key, getattr(rtchat, key, None)) for key in rtchat.__slots__]))

        __type__ = {
            ChatType.GROUP: "groups",
            ChatType.ROOM: "rooms",
            ChatType.PEER: "peers",
        }
    
        def __init__(rtc, line):
            rtc.line = line
            rtc.groups = {}
            rtc.rooms = {}
            rtc.peers = {}

        def __setitem__(rtc, chatMid, chat):
            data = getattr(rtc, rtc.__type__[chat.type])
            data[chatMid] = LINE.RealtimeChats.Chat(chat)
        
        def __delitem__(rtc, chatMid):
            for key in rtc.__type__.values():
                data = getattr(rtc, key)
                if chatMid in data:
                    del data[chatMid]
        
        def __getitem__(rtc, chatMid):

            for key in rtc.__type__.values():
                data = getattr(rtc, key)
                if chatMid in data:
                    return data[chatMid]

            if not rtc.line.config.REALTIME_CHATS:
                return LINE.RealtimeChats.Chat(Chat())

            chat = rtc.line.getChat(chatMid)
            if not chat: return LINE.RealtimeChats.Chat(Chat())
            rtc[chatMid] = chat
            return rtc[chatMid]

        def __call__(rtc, op):

            # invite to chat
            if op.type in [OperationType.INVITE_INTO_GROUP, OperationType.NOTIFIED_INVITE_INTO_GROUP, OperationType.INVITE_INTO_CHAT, OperationType.NOTIFIED_INVITE_INTO_CHAT]:
                chat = rtc[op.param1]
                if op.param3:
                    for mid in op.param3.split("\x1e"):
                        if mid not in chat.invites:
                            chat.invites.append(mid)

            # cancel chat invitation
            if op.type in [OperationType.NOTIFIED_CANCEL_INVITATION_GROUP, OperationType.CANCEL_INVITATION_GROUP, OperationType.CANCEL_CHAT_INVITATION, OperationType.NOTIFIED_CANCEL_CHAT_INVITATION]:
                chat = rtc[op.param1]
                if op.param3:
                    for mid in op.param3.split("\x1e"):
                        if mid in chat.invites:
                            chat.invites.remove(mid)

            # reject chat invitation
            if op.type in [OperationType.REJECT_GROUP_INVITATION, OperationType.NOTIFIED_REJECT_GROUP_INVITATION, OperationType.REJECT_CHAT_INVITATION]:
                chat = rtc[op.param1]
                if op.param2:
                    for mid in op.param2.split("\x1e"):
                        if mid in chat.invites:
                            chat.invites.remove(mid)

            # delete other from chat
            if op.type in [OperationType.KICKOUT_FROM_GROUP, OperationType.NOTIFIED_KICKOUT_FROM_GROUP, OperationType.DELETE_OTHER_FROM_CHAT, OperationType.NOTIFIED_DELETE_OTHER_FROM_CHAT]:
                chat = rtc[op.param1]
                if op.param3:
                    for mid in op.param3.split("\x1e"):
                        if mid == rtc.line.profile.mid:
                            del rtc[op.param1]
                            return
                        if mid in chat.members:
                            chat.members.remove(mid)

            # accept chat invitation
            if op.type in [OperationType.ACCEPT_GROUP_INVITATION, OperationType.NOTIFIED_ACCEPT_GROUP_INVITATION, OperationType.ACCEPT_CHAT_INVITATION, OperationType.NOTIFIED_ACCEPT_CHAT_INVITATION]:
                chat = rtc[op.param1]
                if op.param2:
                    for mid in op.param2.split("\x1e"):
                        if mid not in chat.members:
                            chat.members.append(mid)

            # leave chat
            if op.type in [OperationType.LEAVE_GROUP, OperationType.NOTIFIED_LEAVE_GROUP, OperationType.DELETE_SELF_FROM_CHAT, OperationType.NOTIFIED_DELETE_SELF_FROM_CHAT]:
                chat = rtc[op.param1]
                if op.param2:
                    for mid in op.param2.split("\x1e"):
                        if mid in chat.members:
                            chat.members.remove(mid)

                if op.type in [OperationType.LEAVE_GROUP, OperationType.DELETE_SELF_FROM_CHAT]:
                    del rtc[op.param1]

            if op.type in [26, 25]:
                msg = op.message
                if msg.contentType == 18:
                    key = msg.contentMetadata["LOC_KEY"]
                    args = msg.contentMetadata["LOC_ARGS"].split("\x1e")
                    chat = rtc[op.param1]
                    if key == "C_MI": # invite
                        if args[1] not in chat.invites:
                            chat.invites.append(args[1])
                    if key == "C_IC": # cancel
                        if args[1] in chat.invites:
                            chat.invites.remove(args[1])

    def __init__(line, keeper, source_ip):
        assert isinstance(keeper, LINE.Keeper)
        line.source_ip = (source_ip, 0)
        line.config = LINE.Config()
        line.keeper = keeper
        line.session = LINE.Session(line)
        line.reqSeq = LINE.RequestSequence()
        line.chats = LINE.RealtimeChats(line)
        line.profile = line.getProfile()
        line.contacts = line.getAllContactIds()
        line.lock = threading.Lock()

    def getProfile(line, syncReason=SyncReason.FULL_SYNC):
        line.profile = line.session.talk.getProfile(syncReason)
        return line.profile

    def unsendMessage(line, msgId):
        return line.session.talk.unsendMessage(line.reqSeq["unsendMessage"], msgId)

    def sendMessage(line, to, text, contentMetadata={}, contentType=0):
        msg = Message()
        msg.to = to
        msg._from = line.profile.mid
        msg.text = text
        msg.contentType = contentType
        msg.contentMetadata = contentMetadata
        return line.sendMessageObject(msg)

    def sendMessageObject(line, msg):
        return line.session.talk.sendMessage(line.reqSeq["sendMessage"], msg)

    def sendContact(line, to, mid):
        return line.sendMessage(to, "", {"mid": mid}, ContentType.CONTACT)

    def getAllChatMids(line, withMemberChats=True, withInvitedChats=True, syncReason=SyncReason.FULL_SYNC):
        return line.session.talk.getAllChatMids(request=GetAllChatMidsRequest(withMemberChats=withMemberChats, withInvitedChats=withInvitedChats), syncReason=syncReason)

    def getChats(line, chatMids, withMembers=True, withInvitees=True):
        return line.session.talk.getChats(GetChatsRequest(chatMids=chatMids, withMembers=withMembers, withInvitees=withInvitees)).chats
    
    def getChat(line, chatMid, withMembers=True, withInvitees=True):
        chats = line.getChats([chatMid], withMembers=withMembers, withInvitees=withInvitees)
        if chats:
            return chats[0]

    def acceptChatInvitation(line, chatMid):
        return line.session.talk.acceptChatInvitation(AcceptChatInvitationRequest(line.reqSeq["acceptChatInvitation"], chatMid=chatMid))

    def acceptChatInvitationByTicket(line, chatMid, ticketId):
        return line.session.talk.acceptChatInvitationByTicket(AcceptChatInvitationByTicketRequest(line.reqSeq["acceptChatInvitationByTicket"], chatMid=chatMid, ticketId=ticketId))

    def inviteIntoChat(line, chatMid, targetUserMids):
        for mid in targetUserMids:
            if mid not in line.contacts:
                try:
                    line.contacts.append(mid)
                    line.findAndAddContactsByMid(mid)
                except:
                    continue
        return line.session.talk.inviteIntoChat(InviteIntoChatRequest(line.reqSeq["inviteIntoChat"], chatMid=chatMid, targetUserMids=set(targetUserMids)))

    def cancelChatInvitation(line, chatMid, targetUserMids):
        return line.session.talk.cancelChatInvitation(CancelChatInvitationRequest(line.reqSeq["cancelChatInvitation"], chatMid=chatMid, targetUserMids=set(targetUserMids)))

    def rejectChatInvitation(line, chatMid):
        return line.session.talk.rejectChatInvitation(CancelChatInvitationRequest(line.reqSeq["rejectChatInvitation"], chatMid=chatMid))

    def deleteOtherFromChat(line, chatMid, targetUserMids):
        return line.session.talk.deleteOtherFromChat(DeleteOtherFromChatRequest(line.reqSeq["deleteOtherFromChat"], chatMid=chatMid, targetUserMids=set(targetUserMids)))

    def deleteSelfFromChat(line, chatMid):
        return line.session.talk.deleteSelfFromChat(DeleteSelfFromChatRequest(line.reqSeq["deleteSelfFromChat"], chatMid=chatMid))

    def reissueChatTicket(line, groupMid):
        return line.session.talk.reissueChatTicket(ReissueChatTicketRequest(line.reqSeq["reissueChatTicket"], groupMid=groupMid))

    def getAllContactIds(line, syncReason=SyncReason.FULL_SYNC):
        return line.session.talk.getAllContactIds(syncReason)

    def findAndAddContactsByMid(line, mid, type=ContactType.MID, reference=""):
        if mid in line.contacts or mid == line.profile.mid: return
        with line.lock:
            try:
                return line.session.talk.findAndAddContactsByMid(line.reqSeq["findAndAddContactsByMid"], mid, type, reference)
            finally:
                time.sleep(3)

    def updateChat(line, chat, updatedAttribute):
        return line.session.talk.updateChat(UpdateChatRequest(line.reqSeq["updateChat"], chat=chat, updatedAttribute=updatedAttribute))

    def updateProfile(line, profile):
        return line.session.talk.updateProfile(line.reqSeq["updateProfile"], profile)

    def getGroupIdsJoined(line):
        return line.session.talk.getGroupIdsJoined()

    def removeAllMessages(line, lastMessageId):
        return line.session.talk.removeAllMessages(0, lastMessageId)

    def getContact(line, mid):
        return line.session.talk.getContact(mid)

    def getRecentMessagesV2(line, to, count):
        return line.session.mess.getRecentMessagesV2(to, count)

    def fetchOps(line):
        try:
            ops = line.session.poll.fetchOperations(line.keeper.localRev, line.config.FETCH_OPS_COUNT)
        except EOFError:
            # timeout
            return []

        for op in ops:
            line.keeper.localRev = max(line.keeper.localRev, op.revision)
            threading.Thread(target=line.chats, args=(op,)).start()
        return ops
