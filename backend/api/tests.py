from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
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
        # Register Carol with valid password
        res = self.client.post('/api/auth/register/', {
            'username': 'carol',
            'password': 'CommunityWeave2026!',
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
            'password': 'CommunityWeave2026!'
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

    def test_conversation_and_post_permissions(self):
        carol = User.objects.create_user(username='carol', password='password123')
        post = Post.objects.create(
            author=self.alice,
            type='request',
            title='Need wrench',
            description='desc',
            category='Tools',
            neighborhood='Oakland'
        )
        conv = Conversation.objects.create(post=post, requester=self.bob, owner=self.alice)

        # Carol cannot read or write to Alice & Bob's conversation
        self.client.force_authenticate(user=carol)
        res = self.client.get(f'/api/conversations/{conv.id}/messages/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = self.client.post(f'/api/conversations/{conv.id}/messages/', {'text': 'Intruder'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Carol cannot edit or delete Alice's post
        res = self.client.patch(f'/api/posts/{post.id}/', {'title': 'Hacked'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        res = self.client.delete(f'/api/posts/{post.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_update_and_validation(self):
        self.client.force_authenticate(user=self.alice)
        res = self.client.patch('/api/auth/me/', {'neighborhood': 'Rockridge'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['profile']['neighborhood'], 'Rockridge')

        # Invalid post_id or non-string does not crash with 500
        res = self.client.post('/api/reports/', {'post_id': 'invalid', 'reason': 'spam'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Weak password rejected on register
        res = self.client.post('/api/auth/register/', {'username': 'dan', 'password': '123'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_neighborhoods_list(self):
        res = self.client.get('/api/neighborhoods/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('Downtown', res.data)

    def test_change_password(self):
        self.client.force_authenticate(user=self.alice)

        # Reject wrong old password
        res = self.client.post('/api/auth/change-password/', {
            'old_password': 'wrongpassword',
            'new_password': 'BrandNewPass2026!'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Successful change
        res = self.client.post('/api/auth/change-password/', {
            'old_password': 'password123',
            'new_password': 'BrandNewPass2026!'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

        # Verify new password authenticates
        self.client.logout()
        res = self.client.post('/api/auth/login/', {
            'username': 'alice',
            'password': 'BrandNewPass2026!'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_account(self):
        self.client.force_authenticate(user=self.bob)

        # Reject with wrong password
        res = self.client.post('/api/auth/delete-account/', {'password': 'wrongpassword'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(username='bob').exists())

        # Accept with correct password
        res = self.client.post('/api/auth/delete-account/', {'password': 'password123'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(username='bob').exists())

    def test_security_input_caps_and_report_quarantine(self):
        self.client.force_authenticate(user=self.alice)

        # Post title over 200 chars rejected
        res = self.client.post('/api/posts/', {
            'type': 'request',
            'title': 'A' * 201,
            'description': 'Valid description',
            'neighborhood': 'Oakland'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Create valid post with high precision GPS
        res = self.client.post('/api/posts/', {
            'type': 'request',
            'title': 'Ladder needed',
            'description': 'Brief note',
            'neighborhood': 'Oakland',
            'latitude': 14.5378291,
            'longitude': 120.9998123
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post_id = res.data['id']

        # Verify coordinate privacy fuzzing to 3 decimal places (~110m)
        self.assertEqual(res.data['latitude'], 14.538)
        self.assertEqual(res.data['longitude'], 121.0)

        # Create message over 2000 chars rejected
        conv = Conversation.objects.create(post=Post.objects.get(pk=post_id), requester=self.bob, owner=self.alice)
        res = self.client.post(f'/api/conversations/{conv.id}/messages/', {
            'text': 'M' * 2001
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Community report quarantine: Create 3 users and report post
        u1 = User.objects.create_user(username='u1', password='password123')
        u2 = User.objects.create_user(username='u2', password='password123')
        u3 = User.objects.create_user(username='u3', password='password123')

        for u in [u1, u2]:
            self.client.force_authenticate(user=u)
            self.client.post('/api/reports/', {'post_id': post_id, 'reason': 'Spam'})

        # Post is still open with 2 reports
        p = Post.objects.get(pk=post_id)
        self.assertEqual(p.status, 'open')

        # Third report triggers quarantine
        self.client.force_authenticate(user=u3)
        self.client.post('/api/reports/', {'post_id': post_id, 'reason': 'Malicious'})

        p.refresh_from_db()
        self.assertEqual(p.status, 'flagged')

        # Flagged post is excluded from default open feed
        res = self.client.get('/api/posts/')
        post_ids = [item['id'] for item in res.data]
        self.assertNotIn(post_id, post_ids)

    def test_online_presence_and_heartbeat(self):
        # Alice pings heartbeat
        self.client.force_authenticate(user=self.alice)
        res = self.client.post('/api/auth/ping/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_online'])
        self.assertIsNotNone(res.data['last_active'])

        # Alice's profile reflects online
        self.alice.profile.refresh_from_db()
        self.assertTrue(self.alice.profile.is_online)

        # Bob's last active was 5 minutes ago -> offline
        self.bob.profile.last_active = timezone.now() - datetime.timedelta(minutes=5)
        self.bob.profile.save()
        self.assertFalse(self.bob.profile.is_online)

    def test_read_receipts_and_unread_count(self):
        # Bob starts a conversation with Alice
        post = Post.objects.create(
            author=self.alice,
            type='offer',
            title='Gardening tools',
            description='Free to borrow',
            category='Tools',
            neighborhood='Oakland'
        )
        self.client.force_authenticate(user=self.bob)
        res = self.client.post('/api/conversations/', {
            'post_id': post.id,
            'message': 'Hello Alice, can I borrow them today?'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        conv_id = res.data['id']

        # Message is currently unread
        msg = Message.objects.get(conversation_id=conv_id)
        self.assertFalse(msg.is_read)
        self.assertIsNone(msg.read_at)

        # Alice views conversations list: unread_count is 1
        self.client.force_authenticate(user=self.alice)
        res = self.client.get('/api/conversations/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        conv_item = next(c for c in res.data if c['id'] == conv_id)
        self.assertEqual(conv_item['unread_count'], 1)

        # Alice opens the conversation (GET messages) -> automatically marks as read
        res = self.client.get(f'/api/conversations/{conv_id}/messages/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertTrue(res.data[0]['is_read'])
        self.assertIsNotNone(res.data[0]['read_at'])

        # DB record is updated
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        self.assertIsNotNone(msg.read_at)

        # Alice checks conversations list again: unread_count is 0
        res = self.client.get('/api/conversations/')
        conv_item = next(c for c in res.data if c['id'] == conv_id)
        self.assertEqual(conv_item['unread_count'], 0)

        # Bob views conversation messages: sees message is marked as read
        self.client.force_authenticate(user=self.bob)
        res = self.client.get(f'/api/conversations/{conv_id}/messages/')
        self.assertTrue(res.data[0]['is_read'])
        self.assertIsNotNone(res.data[0]['read_at'])

    def test_caching_and_invalidation(self):
        # First request to posts feed: Cache MISS
        res1 = self.client.get('/api/posts/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.headers.get('X-Cache'), 'MISS')
        self.assertIn('max-age=15', res1.headers.get('Cache-Control', ''))

        # Immediate second request to posts feed: Cache HIT
        res2 = self.client.get('/api/posts/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.headers.get('X-Cache'), 'HIT')

        # Creating a post invalidates feed cache
        self.client.force_authenticate(user=self.alice)
        create_res = self.client.post('/api/posts/', {
            'type': 'offer',
            'title': 'Fresh mint leaves',
            'description': 'From my backyard garden',
            'category': 'Food',
            'neighborhood': 'Oakland'
        })
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        # Third request to posts feed: Fresh Cache MISS with new post included
        res3 = self.client.get('/api/posts/')
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertEqual(res3.headers.get('X-Cache'), 'MISS')
        titles = [p['title'] for p in res3.data]
        self.assertIn('Fresh mint leaves', titles)

        # Neighborhoods list caching (2h TTL)
        n1 = self.client.get('/api/neighborhoods/')
        self.assertEqual(n1.status_code, status.HTTP_200_OK)
        self.assertEqual(n1.headers.get('X-Cache'), 'MISS')
        self.assertIn('max-age=7200', n1.headers.get('Cache-Control', ''))

        n2 = self.client.get('/api/neighborhoods/')
        self.assertEqual(n2.status_code, status.HTTP_200_OK)
        self.assertEqual(n2.headers.get('X-Cache'), 'HIT')






