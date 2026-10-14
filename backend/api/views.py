from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Profile, Post, Conversation, Message, Report
from .serializers import (
    UserSerializer, PostSerializer, ConversationSerializer,
    MessageSerializer, ReportSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    display_name = request.data.get('display_name', '').strip() or username
    neighborhood = request.data.get('neighborhood', '').strip()

    if not username or not password:
        return Response({'detail': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username__iexact=username).exists():
        return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
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
def login_view(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

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


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    if request.method == 'PATCH':
        display_name = request.data.get('display_name')
        neighborhood = request.data.get('neighborhood')
        if display_name is not None:
            user.profile.display_name = display_name.strip()
        if neighborhood is not None:
            user.profile.neighborhood = neighborhood.strip()
        user.profile.save()
    return Response(UserSerializer(user).data)


@api_view(['GET', 'POST'])
def posts_list_create(request):
    if request.method == 'GET':
        posts = Post.objects.all()

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
        return Response(serializer.data)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
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
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversations_list_create(request):
    user = request.user
    if request.method == 'GET':
        conversations = Conversation.objects.filter(Q(requester=user) | Q(owner=user))
        return Response(ConversationSerializer(conversations, many=True).data)

    if request.method == 'POST':
        post_id = request.data.get('post_id')
        if not post_id:
            return Response({'detail': 'post_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        if post.author == user:
            return Response({'detail': 'Cannot start a conversation with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        conv, created = Conversation.objects.get_or_create(
            post=post,
            requester=user,
            defaults={'owner': post.author}
        )

        initial_message = request.data.get('message', '').strip()
        if initial_message:
            Message.objects.create(conversation=conv, sender=user, text=initial_message)

        return Response(ConversationSerializer(conv).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversation_messages(request, pk):
    try:
        conv = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({'detail': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.user != conv.requester and request.user != conv.owner:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        messages = conv.messages.all()
        return Response(MessageSerializer(messages, many=True).data)

    if request.method == 'POST':
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'detail': 'Text cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
        msg = Message.objects.create(conversation=conv, sender=request.user, text=text)
        conv.save()  # update timestamp
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_post(request):
    post_id = request.data.get('post_id')
    reason = request.data.get('reason', '').strip()

    if not post_id or not reason:
        return Response({'detail': 'post_id and reason are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

    report = Report.objects.create(reporter=request.user, post=post, reason=reason)
    return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
