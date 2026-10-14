from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Post, Conversation, Message, Report


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['display_name', 'neighborhood']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'profile']


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    author_display_name = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_username', 'author_display_name',
            'type', 'title', 'description', 'category', 'neighborhood',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'author', 'created_at']

    def get_author_display_name(self, obj):
        if hasattr(obj.author, 'profile') and obj.author.profile.display_name:
            return obj.author.profile.display_name
        return obj.author.username


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_username', 'text', 'created_at']
        read_only_fields = ['id', 'conversation', 'sender', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    post_title = serializers.ReadOnlyField(source='post.title')
    requester_username = serializers.ReadOnlyField(source='requester.username')
    owner_username = serializers.ReadOnlyField(source='owner.username')
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'post', 'post_title', 'requester', 'requester_username',
            'owner', 'owner_username', 'last_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'requester', 'owner', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if last:
            return {'sender': last.sender.username, 'text': last.text, 'created_at': last.created_at}
        return None


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'post', 'reason', 'created_at']
        read_only_fields = ['id', 'reporter', 'created_at']
