from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Profile, Post, Conversation, Message, Report


class ProfileSerializer(serializers.ModelSerializer):
    is_online = serializers.ReadOnlyField()

    class Meta:
        model = Profile
        fields = ['display_name', 'neighborhood', 'address', 'latitude', 'longitude', 'is_online', 'last_active']
        read_only_fields = ['is_online', 'last_active']


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
            'address', 'latitude', 'longitude', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'author', 'created_at']

    def get_author_display_name(self, obj):
        if hasattr(obj.author, 'profile') and obj.author.profile.display_name:
            return obj.author.profile.display_name
        return obj.author.username

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Location privacy: Round coordinates to 3 decimal places (~110m) to protect exact doorstep
        if ret.get('latitude') is not None:
            try:
                ret['latitude'] = round(float(ret['latitude']), 3)
            except (ValueError, TypeError):
                pass
        if ret.get('longitude') is not None:
            try:
                ret['longitude'] = round(float(ret['longitude']), 3)
            except (ValueError, TypeError):
                pass
        return ret


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_username', 'text', 'is_read', 'read_at', 'created_at']
        read_only_fields = ['id', 'conversation', 'sender', 'is_read', 'read_at', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    post_title = serializers.ReadOnlyField(source='post.title')
    requester_username = serializers.ReadOnlyField(source='requester.username')
    requester_display_name = serializers.SerializerMethodField()
    owner_username = serializers.ReadOnlyField(source='owner.username')
    owner_display_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    partner_username = serializers.SerializerMethodField()
    partner_display_name = serializers.SerializerMethodField()
    partner_is_online = serializers.SerializerMethodField()
    partner_last_active = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'post', 'post_title', 'requester', 'requester_username', 'requester_display_name',
            'owner', 'owner_username', 'owner_display_name', 'last_message',
            'partner_username', 'partner_display_name', 'partner_is_online', 'partner_last_active',
            'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'requester', 'owner', 'created_at', 'updated_at']

    def _get_partner_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.owner if obj.requester_id == request.user.id else obj.requester
        return obj.owner

    def get_partner_username(self, obj):
        partner = self._get_partner_user(obj)
        return partner.username if partner else ''

    def get_partner_display_name(self, obj):
        partner = self._get_partner_user(obj)
        if partner and hasattr(partner, 'profile') and partner.profile.display_name:
            return partner.profile.display_name
        return partner.username if partner else ''

    def get_partner_is_online(self, obj):
        partner = self._get_partner_user(obj)
        return getattr(getattr(partner, 'profile', None), 'is_online', False)

    def get_partner_last_active(self, obj):
        partner = self._get_partner_user(obj)
        return getattr(getattr(partner, 'profile', None), 'last_active', None)

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'messages' in obj._prefetched_objects_cache:
                return sum(1 for m in obj.messages.all() if m.sender_id != request.user.id and not m.is_read)
            return obj.messages.filter(~Q(sender=request.user), is_read=False).count()
        return 0

    def get_requester_display_name(self, obj):
        if hasattr(obj.requester, 'profile') and obj.requester.profile.display_name:
            return obj.requester.profile.display_name
        return obj.requester.username

    def get_owner_display_name(self, obj):
        if hasattr(obj.owner, 'profile') and obj.owner.profile.display_name:
            return obj.owner.profile.display_name
        return obj.owner.username

    def get_last_message(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'messages' in obj._prefetched_objects_cache:
            msgs = list(obj.messages.all())
            if msgs:
                last = msgs[-1]
                return {
                    'id': last.id,
                    'sender': last.sender.username,
                    'text': last.text,
                    'is_read': last.is_read,
                    'read_at': last.read_at,
                    'created_at': last.created_at
                }
            return None
        last = obj.messages.order_by('-created_at').first()
        if last:
            return {
                'id': last.id,
                'sender': last.sender.username,
                'text': last.text,
                'is_read': last.is_read,
                'read_at': last.read_at,
                'created_at': last.created_at
            }
        return None


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'post', 'reason', 'created_at']
        read_only_fields = ['id', 'reporter', 'created_at']
