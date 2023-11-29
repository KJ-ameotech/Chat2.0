import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from chatapp.models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_slug']
        self.roomGroupName = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.roomGroupName,
            self.channel_name
        )
        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.roomGroupName,
            self.channel_name
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

            await self.save_message(message, username, other_user, room_name)

            await self.channel_layer.group_send(
                self.roomGroupName, {
                    "type": "sendMessage",
                    "message": message,
                    "username": username,
                    "room_name": room_name,
                }
            )

    async def sendMessage(self, event):
        message = event["message"]
        username = event["username"]
        await self.send(text_data=json.dumps({"message": message, "username": username}))

    @sync_to_async
    def save_message(self, message, username, other_user, room_name):
        try:
            room=Room.objects.get(name=room_name)
            Message.objects.create(user=username,other_user=other_user,room=room,content=message)
        except Exception as err:
            print('Error while saving message -', err)

    @sync_to_async
    def update_message(self, user_id, other_user, room_name):
        try:
            room=Room.objects.get(name=room_name)
            messages = Message.objects.filter(user=user_id, other_user=other_user, room=room)
            for msg in messages:
                msg.read_message = True
                msg.save()
        except Exception as err:
            print('Error while updating message -', err)
