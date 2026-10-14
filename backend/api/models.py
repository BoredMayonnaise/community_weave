from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    neighborhood = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.display_name or self.user.username


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, display_name=instance.username)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


class Post(models.Model):
    TYPE_CHOICES = [
        ('request', 'Request'),
        ('offer', 'Offer'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='request')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, default='General')
    neighborhood = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type.upper()}] {self.title} ({self.neighborhood})"


class Conversation(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='conversations')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_conversations')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('post', 'requester')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Post #{self.post_id}: {self.requester.username} <-> {self.owner.username}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.text[:30]}"


class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporter.username} on post #{self.post_id}"
