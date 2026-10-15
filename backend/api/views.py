from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from .models import Profile, Post, Conversation, Message, Report
from .serializers import (
    UserSerializer, PostSerializer, ConversationSerializer,
    MessageSerializer, ReportSerializer
)


def get_posts_cache_version():
    ver = cache.get('posts_cache_version')
    if ver is None:
        ver = 1
        cache.set('posts_cache_version', ver, timeout=86400)
    return ver


def invalidate_posts_cache():
    try:
        cache.incr('posts_cache_version')
    except (ValueError, TypeError):
        cache.set('posts_cache_version', 1, timeout=86400)


class AuthRateThrottle(AnonRateThrottle):
    rate = '15/minute'


class MessageRateThrottle(UserRateThrottle):
    rate = '60/minute'


def _clean_str(val):
    return val.strip() if isinstance(val, str) else ''


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register_view(request):
    username = _clean_str(request.data.get('username'))
    password = str(request.data.get('password') or '')
    display_name = _clean_str(request.data.get('display_name')) or username
    neighborhood = _clean_str(request.data.get('neighborhood'))

    if not username or not password:
        return Response({'detail': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(username) < 3 or len(username) > 50:
        return Response({'detail': 'Username must be between 3 and 50 characters.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) > 128:
        return Response({'detail': 'Password cannot exceed 128 characters.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(display_name) > 100:
        display_name = display_name[:100]

    if len(neighborhood) > 100:
        neighborhood = neighborhood[:100]

    try:
        validate_password(password)
    except ValidationError as e:
        return Response({'detail': ' '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username__iexact=username).exists():
        return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user.profile.display_name = display_name
    user.profile.neighborhood = neighborhood
    user.profile.save()

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login_view(request):
    username = _clean_str(request.data.get('username'))
    password = str(request.data.get('password') or '')

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response({'detail': 'Logged out successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AuthRateThrottle])
def change_password_view(request):
    old_password = str(request.data.get('old_password') or '')
    new_password = str(request.data.get('new_password') or '')

    if not old_password or not new_password:
        return Response({'detail': 'Current password and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not user.check_password(old_password):
        return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) > 128:
        return Response({'detail': 'Password cannot exceed 128 characters.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return Response({'detail': ' '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    Token.objects.filter(user=user).delete()
    new_token = Token.objects.create(user=user)

    return Response({
        'detail': 'Password changed successfully.',
        'token': new_token.key
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AuthRateThrottle])
def delete_account_view(request):
    password = str(request.data.get('password') or '')
    if not password:
        return Response({'detail': 'Password confirmation is required to delete your account.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not user.check_password(password):
        return Response({'detail': 'Incorrect password. Account deletion canceled.'}, status=status.HTTP_400_BAD_REQUEST)

    Token.objects.filter(user=user).delete()
    user.delete()
    invalidate_posts_cache()
    cache.delete('neighborhoods_list')

    return Response({'detail': 'Your account and personal data have been permanently deleted.'})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    if request.method == 'PATCH':
        display_name = request.data.get('display_name')
        neighborhood = request.data.get('neighborhood')
        address = request.data.get('address')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if isinstance(display_name, str):
            user.profile.display_name = display_name.strip()
        if isinstance(neighborhood, str):
            user.profile.neighborhood = neighborhood.strip()
        if isinstance(address, str):
            user.profile.address = address.strip()
        if latitude is not None:
            try:
                user.profile.latitude = float(latitude)
            except (ValueError, TypeError):
                pass
        if longitude is not None:
            try:
                user.profile.longitude = float(longitude)
            except (ValueError, TypeError):
                pass
        user.profile.save()
    return Response(UserSerializer(user).data)


@api_view(['GET', 'POST'])
def posts_list_create(request):
    if request.method == 'GET':
        allowed_params = ['status', 'type', 'category', 'neighborhood', 'search', 'author']
        normalized_parts = []
        for k in sorted(allowed_params):
            v = request.query_params.get(k)
            if v and v.strip():
                normalized_parts.append(f"{k}={v.strip().lower()}")
        norm_query = '&'.join(normalized_parts)
        version = get_posts_cache_version()
        cache_key = f"posts_feed_v{version}_{norm_query}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            resp = Response(cached_data)
            resp['Cache-Control'] = 'public, max-age=15'
            resp['X-Cache'] = 'HIT'
            return resp

        posts = Post.objects.select_related('author__profile').all()

        status_param = request.query_params.get('status', 'open')
        if status_param != 'all':
            posts = posts.filter(status=status_param)

        post_type = request.query_params.get('type')
        if post_type in ['request', 'offer']:
            posts = posts.filter(type=post_type)

        category = request.query_params.get('category')
        if category and category.lower() != 'all':
            posts = posts.filter(category__iexact=category)

        neighborhood = request.query_params.get('neighborhood')
        if neighborhood and neighborhood.strip():
            posts = posts.filter(neighborhood__icontains=neighborhood.strip())

        search = request.query_params.get('search')
        if search:
            posts = posts.filter(Q(title__icontains=search) | Q(description__icontains=search))

        author = request.query_params.get('author')
        if author:
            posts = posts.filter(author__username=author)

        serializer = PostSerializer(posts, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=15)
        resp = Response(data)
        resp['Cache-Control'] = 'public, max-age=15'
        resp['X-Cache'] = 'MISS'
        return resp

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        title = request.data.get('title')
        description = request.data.get('description')
        if isinstance(title, str) and len(title.strip()) > 200:
            return Response({'detail': 'Title cannot exceed 200 characters.'}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(description, str) and len(description.strip()) > 5000:
            return Response({'detail': 'Description cannot exceed 5,000 characters.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            extra_kwargs = {'author': request.user}
            if serializer.validated_data.get('latitude') is None and hasattr(request.user, 'profile') and request.user.profile.latitude is not None:
                extra_kwargs['latitude'] = request.user.profile.latitude
            if serializer.validated_data.get('longitude') is None and hasattr(request.user, 'profile') and request.user.profile.longitude is not None:
                extra_kwargs['longitude'] = request.user.profile.longitude
            serializer.save(**extra_kwargs)
            invalidate_posts_cache()
            cache.delete('neighborhoods_list')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def post_detail(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(PostSerializer(post).data)

    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    if post.author != request.user:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            invalidate_posts_cache()
            cache.delete('neighborhoods_list')
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        post.delete()
        invalidate_posts_cache()
        cache.delete('neighborhoods_list')
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversations_list_create(request):
    user = request.user
    Profile.objects.filter(user=user).update(last_active=timezone.now())

    if request.method == 'GET':
        conversations = Conversation.objects.filter(
            Q(requester=user) | Q(owner=user)
        ).select_related('post', 'requester__profile', 'owner__profile').prefetch_related('messages', 'messages__sender')
        return Response(ConversationSerializer(conversations, many=True, context={'request': request}).data)

    if request.method == 'POST':
        post_id = request.data.get('post_id')
        if not post_id or not str(post_id).isdigit():
            return Response({'detail': 'Valid post_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(pk=int(post_id))
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        if post.author == user:
            return Response({'detail': 'Cannot start a conversation with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        conv, created = Conversation.objects.get_or_create(
            post=post,
            requester=user,
            defaults={'owner': post.author}
        )

        initial_message = _clean_str(request.data.get('message'))
        if initial_message:
            Message.objects.create(conversation=conv, sender=user, text=initial_message)
            conv.save()

        return Response(ConversationSerializer(conv, context={'request': request}).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageRateThrottle])
def conversation_messages(request, pk):
    Profile.objects.filter(user=request.user).update(last_active=timezone.now())

    try:
        conv = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({'detail': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.user != conv.requester and request.user != conv.owner:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Mark incoming unread messages as read (Seen status)
        conv.messages.filter(~Q(sender=request.user), is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        messages = conv.messages.select_related('sender').all()
        return Response(MessageSerializer(messages, many=True).data)

    if request.method == 'POST':
        text = _clean_str(request.data.get('text'))
        if not text:
            return Response({'detail': 'Text cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(text) > 2000:
            return Response({'detail': 'Message cannot exceed 2,000 characters.'}, status=status.HTTP_400_BAD_REQUEST)
        msg = Message.objects.create(conversation=conv, sender=request.user, text=text)
        conv.save()  # update timestamp
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ping_view(request):
    now = timezone.now()
    Profile.objects.filter(user=request.user).update(last_active=now)
    return Response({'status': 'ok', 'is_online': True, 'last_active': now.isoformat()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AuthRateThrottle])
def report_post(request):
    post_id = request.data.get('post_id')
    reason = _clean_str(request.data.get('reason'))

    if not post_id or not str(post_id).isdigit() or not reason:
        return Response({'detail': 'Valid post_id and reason are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        post = Post.objects.get(pk=int(post_id))
    except Post.DoesNotExist:
        return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Prevent a single user from spamming multiple reports on the same post
    if Report.objects.filter(reporter=request.user, post=post).exists():
        return Response({'detail': 'You have already reported this post.'}, status=status.HTTP_400_BAD_REQUEST)

    report = Report.objects.create(reporter=request.user, post=post, reason=reason[:500])

    # Auto-quarantine: If 3 or more unique neighbors report the post, flag it from public feed
    if post.reports.count() >= 3 and post.status == 'open':
        post.status = 'flagged'
        post.save(update_fields=['status'])
        invalidate_posts_cache()

    return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def neighborhoods_list(request):
    cache_key = 'neighborhoods_list'
    cached = cache.get(cache_key)
    if cached is not None:
        resp = Response(cached)
        resp['Cache-Control'] = 'public, max-age=7200'
        resp['X-Cache'] = 'HIT'
        return resp

    names = Post.objects.values_list('neighborhood', flat=True).distinct()
    defaults = ['Downtown', 'North Hills', 'Riverside', 'West End', 'Oakridge']
    combined = sorted(set(defaults) | {n.strip() for n in names if n and n.strip()})
    cache.set(cache_key, combined, timeout=7200)
    resp = Response(combined)
    resp['Cache-Control'] = 'public, max-age=7200'
    resp['X-Cache'] = 'MISS'
    return resp

