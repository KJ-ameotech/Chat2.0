from django.db import models

# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)


    def __str__(self):
        return "Room : "+ self.name + " | Id : " + self.slug


class Message(models.Model):
    user = models.CharField(max_length=255)
    other_user = models.CharField(max_length=255)
    content = models.TextField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    read_message = models.BooleanField(default=False)


    def __str__(self):
        return "Message is :- "+ self.content