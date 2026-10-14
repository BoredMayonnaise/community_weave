from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Post, Conversation, Message, Report


class CommunityWeaveApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Alice
        self.alice = User.objects.create_user(username='alice', password='password123')
        self.alice.profile.display_name = 'Alice W.'
        self.alice.profile.neighborhood = 'Oakland'
        self.alice.profile.save()

        # Create Bob
        self.bob = User.objects.create_user(username='bob', password='password123')
        self.bob.profile.display_name = 'Bob M.'
        self.bob.profile.neighborhood = 'Berkeley'
        self.bob.profile.save()

    def test_auth_register_and_login(self):
        # Register Carol
        res = self.client.post('/api/auth/register/', {
            'username': 'carol',
            'password': 'password123',
            'display_name': 'Carol D.',
            'neighborhood': 'Oakland'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        token = res.data['token']
        self.assertTrue(token)
        self.assertEqual(res.data['user']['profile']['display_name'], 'Carol D.')

        # Login Carol
        res = self.client.post('/api/auth/login/', {
            'username': 'carol',
            'password': 'password123'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['token'], token)

    def test_post_lifecycle_and_filters(self):
        # Alice creates a request post
        self.client.force_authenticate(user=self.alice)
        res = self.client.post('/api/posts/', {
            'type': 'request',
            'title': 'Need ladder for weekend',
            'description': 'Cleaning gutters on Saturday',
            'category': 'Tools',
            'neighborhood': 'Oakland'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post_id = res.data['id']

        # Bob creates an offer post
        self.client.force_authenticate(user=self.bob)
        self.client.post('/api/posts/', {
            'type': 'offer',
            'title': 'Free lemons from garden',
            'description': 'Bag full of lemons at front porch',
            'category': 'Food',
            'neighborhood': 'Berkeley'
        })

        # Filter by type=request
        self.client.logout()
        res = self.client.get('/api/posts/?type=request')
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], 'Need ladder for weekend')

        # Filter by neighborhood
        res = self.client.get('/api/posts/?neighborhood=Oakland')
        self.assertEqual(len(res.data), 1)

        # Alice closes her post
        self.client.force_authenticate(user=self.alice)
        res = self.client.patch(f'/api/posts/{post_id}/', {'status': 'closed'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'closed')

        # Check that default listing excludes closed posts
        res = self.client.get('/api/posts/')
        self.assertEqual(len(res.data), 1)  # only Bob's offer remains open

    def test_conversation_and_messaging_flow(self):
        # Alice posts an offer
        post = Post.objects.create(
            author=self.alice,
            type='offer',
            title='Lawn mower lending',
            description='Happy to lend my electric mower',
            category='Tools',
            neighborhood='Oakland'
        )

        # Bob contacts Alice
        self.client.force_authenticate(user=self.bob)
        res = self.client.post('/api/conversations/', {
            'post_id': post.id,
            'message': 'Hi Alice! Can I borrow it Sunday morning?'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        conv_id = res.data['id']

        # Alice checks her conversations
        self.client.force_authenticate(user=self.alice)
        res = self.client.get('/api/conversations/')
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['post_title'], 'Lawn mower lending')

        # Alice replies
        res = self.client.post(f'/api/conversations/{conv_id}/messages/', {
            'text': 'Sure Bob, Sunday 9 AM works!'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Bob reads messages
        self.client.force_authenticate(user=self.bob)
        res = self.client.get(f'/api/conversations/{conv_id}/messages/')
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[1]['text'], 'Sure Bob, Sunday 9 AM works!')

    def test_report_post(self):
        post = Post.objects.create(
            author=self.bob,
            type='offer',
            title='Suspicious post',
            description='Spam text',
            category='Other',
            neighborhood='Berkeley'
        )
        self.client.force_authenticate(user=self.alice)
        res = self.client.post('/api/reports/', {
            'post_id': post.id,
            'reason': 'Looks like spam'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 1)
