from django.shortcuts import render
from .models import Room, Message
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Room
from .serializers import RoomSerializer, MessageSerializer
from django.http import Http404
from django.db.models import Q
from collections import defaultdict
def rooms(request):
    rooms=Room.objects.all()
    return render(request, "rooms.html",{"rooms":rooms})

def room(request,slug):
    try:
        room_name=Room.objects.get(slug=slug).name
        messages=Message.objects.filter(room=Room.objects.get(slug=slug))
        return render(request, "room.html",{"room_name":room_name,"slug":slug,'messages':messages})
    except:
        return render(request, "room.html")
class RoomList(APIView):
    """
    List all rooms or create a new room.
    """
    def get(self, request, format=None):
        response = {'status': False}
        user_id = request.GET.get('user_id', None)
        if user_id:
            messages = Message.objects.filter(Q(other_user=user_id) & Q(read_message=False))
            user_msg_counts = defaultdict(int)
            for msg in messages:
                user_msg_counts[msg.user] += 1
            user_msgs = [{'id': id, 'count': count} for id, count in user_msg_counts.items()]
            if len(messages) > 0:
                response['status'] = True
                response['total_msgs'] = len(messages)
                response['user_msgs'] = user_msgs
        return Response(response)

    def post(self, request, format=None):
        # Deserialize the request data using your RoomSerializer
        serializer = RoomSerializer(data=request.data)

        if serializer.is_valid():
            room_name = serializer.validated_data['name']
            room_slug = serializer.validated_data['slug']

            # Check if a room with the same name or slug already exists
            if Room.objects.filter(Q(name=room_name) | Q(slug=room_slug)).exists():
                # Retrieve the first hundred messages based on the slug
                messages = Message.objects.filter(room__slug=room_slug)[:100]
                message_data = MessageSerializer(messages, many=True).data

                print(message_data, "=================")

                # Create the response data with the error message and messages
                response_data = {
                    "detail": "Room and slug already exist",
                    "messages": message_data
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

            # Save the new room
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

class RoomDetail(APIView):
    """
    Retrieve, update or delete a room instance.
    """
    def get_object(self, slug):
        try:
            return Room.objects.get(slug=slug)
        except Room.DoesNotExist:
            raise Http404

    def get(self, request, slug, format=None):
        room = self.get_object(slug)
        serializer = RoomSerializer(room)
        return Response(serializer.data)

    def put(self, request, slug, format=None):
        room = self.get_object(slug)
        serializer = RoomSerializer(room, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug, format=None):
        room = self.get_object(slug)
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
