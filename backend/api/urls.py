from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/me/', views.me_view, name='me'),
    path('auth/change-password/', views.change_password_view, name='change_password'),
    path('auth/delete-account/', views.delete_account_view, name='delete_account'),
    path('auth/ping/', views.ping_view, name='ping'),

    # Posts
    path('posts/', views.posts_list_create, name='posts_list_create'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),

    # Conversations & Messages
    path('conversations/', views.conversations_list_create, name='conversations_list_create'),
    path('conversations/<int:pk>/messages/', views.conversation_messages, name='conversation_messages'),

    # Reports
    path('reports/', views.report_post, name='report_post'),

    # Neighborhoods
    path('neighborhoods/', views.neighborhoods_list, name='neighborhoods_list'),
]
