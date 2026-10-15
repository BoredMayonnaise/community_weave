from django.contrib import admin
from .models import Profile, Post, Conversation, Message, Report

admin.site.register([Profile, Post, Conversation, Message, Report])
