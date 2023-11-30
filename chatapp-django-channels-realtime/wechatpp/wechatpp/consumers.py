import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.db.models import Q
from chatapp.models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = set()

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_slug']
        self.reverse_room_name = f"{self.room_name.split('__chat__')[1]}__chat__{self.room_name.split('__chat__')[0]}"
        self.roomGroupName = await self.getRoomName()

        await self.channel_layer.group_add(
            self.roomGroupName,
            self.channel_name
        )
        await self.accept()
        self.connected_users.add(self.channel_name)
        self.room_members = len(self.connected_users)
        self.username = self.room_name.split('__chat__')[0]
        await self.channel_layer.group_send(
            self.roomGroupName, {
                "type": "sendMessage",
                "status": "Online",
                "username": self.username,
                "online_members": self.room_members,
            }
        )


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.roomGroupName,
            self.channel_name
        )
        self.connected_users.discard(self.channel_name)
        self.room_members = len(self.connected_users)
        await self.channel_layer.group_send(
            self.roomGroupName, {
                "type": "sendMessage",
                "status": "Offline",
                "username": self.username,
                "online_members": self.room_members,
            }
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if text_data_json.get('user_id', None):
            other_user = text_data_json["other_user"]
            user_id = text_data_json["user_id"]
            room_name = text_data_json["room_name"]
            await self.update_message(user_id, other_user, room_name)
        else:
            message = text_data_json["message"]
            username = text_data_json["username"]
            other_user = text_data_json["other_user"]
            room_name = text_data_json["room_name"]

            await self.save_message(message, username, other_user, self.room_name)

            await self.channel_layer.group_send(
                self.roomGroupName, {
                    "type": "sendMessage",
                    "message": message,
                    "username": username,
                    "room_name": self.room_name,
                }
            )

    async def sendMessage(self, event):
        message = event.get("message")
        username = event.get("username")
        if event.get("status"):
            await self.send(text_data=json.dumps({"status": event.get("status"), "username": event.get("username"), "online_members": event.get("online_members")}))
        else:
            await self.send(text_data=json.dumps({"message": message, "username": username}))

    @sync_to_async
    def save_message(self, message, username, other_user, room_name):
        try:
            room=Room.objects.get(name=self.roomGroupName)
            Message.objects.create(user=username,other_user=other_user,room=room,content=message)
        except Exception as err:
            print('Error while saving message -', err)

    @sync_to_async
    def update_message(self, user_id, other_user, room_name):
        try:
            room=Room.objects.get(name=self.roomGroupName)
            messages = Message.objects.filter(user=user_id, other_user=other_user, room=room)
            for msg in messages:
                msg.read_message = True
                msg.save()
        except Exception as err:
            print('Error while updating message -', err)


    async def get_group_members_count(self):
        group_members = await self.channel_layer.group_channels(self.roomGroupName)
        members_count = len(group_members)
        return members_count


    @sync_to_async
    def getRoomName(self):
        room = Room.objects.filter(Q(name=self.room_name) | Q(name=self.reverse_room_name)).first()
        return room.name if room else ''
