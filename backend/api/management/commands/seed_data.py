from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Post, Conversation, Message


class Command(BaseCommand):
    help = 'Seed realistic sample data for Community Weave'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding sample data...")

        # Create demo users
        users_data = [
            ('elena', 'pass123', 'Elena Rostova', 'Downtown'),
            ('marcus', 'pass123', 'Marcus Chen', 'North Hills'),
            ('sarah', 'pass123', 'Sarah Jenkins', 'Riverside'),
        ]

        users = {}
        for username, password, display_name, neighborhood in users_data:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
            user.profile.display_name = display_name
            user.profile.neighborhood = neighborhood
            user.profile.save()
            users[username] = user

        # Create sample posts
        posts_data = [
            {
                'author': users['elena'],
                'type': 'request',
                'title': 'Need a ladder for gutter cleaning this Saturday',
                'description': 'Looking to borrow a 12ft+ ladder for about 3 hours in the afternoon. Can return same day with freshly baked cookies!',
                'category': 'Tools',
                'neighborhood': 'Downtown',
                'status': 'open'
            },
            {
                'author': users['marcus'],
                'type': 'offer',
                'title': 'Extra home-grown Meyer lemons (2 bags)',
                'description': 'Our tree produced way too many lemons this season. Organic, juicy, ready for pickup by the porch.',
                'category': 'Food',
                'neighborhood': 'North Hills',
                'status': 'open'
            },
            {
                'author': users['sarah'],
                'type': 'request',
                'title': 'Looking for cardboard moving boxes',
                'description': 'Moving next weekend! Need medium/large clean boxes. Can pick up anywhere in Riverside or Downtown.',
                'category': 'Goods',
                'neighborhood': 'Riverside',
                'status': 'open'
            },
            {
                'author': users['marcus'],
                'type': 'offer',
                'title': 'Can help with bicycle tuning / flat tires',
                'description': 'Have a full bike stand and tools. Free 20-min tune-up or brake check for neighbors this Sunday.',
                'category': 'Skills',
                'neighborhood': 'North Hills',
                'status': 'open'
            },
        ]

        for p_data in posts_data:
            post, _ = Post.objects.get_or_create(
                author=p_data['author'],
                title=p_data['title'],
                defaults=p_data
            )

        # Create sample conversation
        post = Post.objects.filter(title__icontains='lemons').first()
        if post:
            conv, _ = Conversation.objects.get_or_create(
                post=post,
                requester=users['sarah'],
                defaults={'owner': users['marcus']}
            )
            if not conv.messages.exists():
                Message.objects.create(
                    conversation=conv,
                    sender=users['sarah'],
                    text='Hi Marcus! Are the lemons still available? I can stop by around 4 PM.'
                )
                Message.objects.create(
                    conversation=conv,
                    sender=users['marcus'],
                    text='Hi Sarah! Yes, I left a bag on the porch bench for you.'
                )

        self.stdout.write(self.style.SUCCESS("Sample data seeded successfully!"))
