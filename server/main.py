# -*- coding: utf-8 -*-
import classes.eb_websocket as eb # our eb_websocket class
from random import random

# FUNCTIONS
# -

# HANDLERS
def setNickname(conn, data, server, private_data):
    if private_data["isTakenNickname"]:
        return False
    
    private_data["nickname"]        = data["nickname"]
    private_data["isTakenNickname"] = True

    server.user_list.append({
        "userID"       : private_data["userID"],
        "nickname"     : private_data["nickname"],
        "private_data" : private_data,
        "conn"         : conn
    })

def getRoomList(conn, data, server, _):
    server.emit(conn, "getRoomListResponse", server.room_list)

def newRoom(conn, data, server, private_data):
    if not private_data["isCreatedRoom"]:
        server.room_list.append({
            "roomID"      : random(),
            "roomName"    : data["roomName"],
            "ownerID"     : private_data["userID"],
            "userList"    : [], # stored as nickname and user id pair
            "chatHistory" : []
        })

        private_data["isCreatedRoom"] = True

        server.emit(conn, "newRoomResponse", {"code":1, "roomList":server.room_list})

        server.emit_all("getRoomListResponse", server.room_list)

    else:
        server.emit(conn, "newRoomResponse", {"code":2})

def enterRoom(conn, data, server, private_data):
    for room in server.room_list:
        if room["roomID"] == data["roomID"]:
            if private_data["currentRoomID"] is not room["roomID"]:
                room["userList"].append((private_data["userID"], private_data["nickname"]))

                server.emit(conn, "enterRoomResponse", {"code":1, "room_name":room["roomName"],"room_user_list":room["userList"], "chat_history":room["chatHistory"]})
                
                private_data["currentRoomID"] = room["roomID"]

                break

            else:
                server.emit(conn, "enterRoomResponse", {"code":3}) # already in chat room

        else:
            server.emit(conn, "enterRoomResponse", {"code":2}) # room is not exist

def chatNewMessage(conn, data, server, private_data):
    if private_data["currentRoomID"] == data["roomID"]:
        for room in server.room_list:
            if room["roomID"] == private_data["currentRoomID"]:
                room["chatHistory"].append({
                    "senderID"       : private_data["userID"],
                    "senderNickname" : private_data["nickname"],
                    "message"        : data["message"]
                })

                for user in server.user_list:
                    if user["private_data"]["currentRoomID"] == room["roomID"]:
                        server.emit(user["conn"], "chatNewMessageResponse", {
                            "senderID"       : private_data["userID"],
                            "senderNickname" : private_data["nickname"],
                            "message"        : data["message"]
                        })

    else:
        # hack attempt
        return False

# SPECIAL HANDLERS
def init(server):
	server.user_list = []
	server.room_list = []

	# print("[?] Server is online.")

def on_socket_open(server, private_data):
    #create random id for socket user
    private_data["userID"]          = random()
    private_data["nickname"]        = None
    private_data["isCreatedRoom"]   = False
    private_data["isTakenNickname"] = False
    private_data["currentRoomID"]   = None

def loop(server):
    pass

def disconnect(server, private_data):
	for i, user in enumerate(server.user_list):
		if private_data["userID"] == user["userID"]:
			server.user_list.pop(i)

	if private_data["currentRoomID"] is not None:
		for room in server.room_list:
			for i, user in enumerate(room["userList"]):
				if user[0] == private_data["userID"]:
					room["userList"].pop(i)
					
					if len(room["userList"]) < 1:
						for j, _room in enumerate(server.room_list):
							if _room["roomID"] == room["roomID"]:
								server.room_list.pop(j)
								server.emit_all("getRoomListResponse", server.room_list)
                            

server_addr = ("", 3232) # host, port
handlers    = {
    "getRoomList"    : getRoomList,
    "newRoom"        : newRoom,
    "setNickname"    : setNickname,
    "enterRoom"      : enterRoom,
    "chatNewMessage" : chatNewMessage
}
special_handlers = {
	"init" : init,
	"disconnect": disconnect,
    "loop" : loop,
    "on_socket_open" : on_socket_open
}

Websocket_server = eb.EB_Websocket(server_addr, handlers, special_handlers, debug=1)
