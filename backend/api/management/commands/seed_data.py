from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from api.models import Post, Conversation, Message, Report
from api.views import invalidate_posts_cache
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed authentic Philippine community sample data and remove meaningless test posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-posts',
            action='store_true',
            help='Do not delete existing posts, only add seed data',
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding authentic Philippine neighborhood data...")

        # 1. Clean up meaningless/test posts and old placeholder data
        if not options['keep_posts']:
            self.stdout.write("Removing non-meaningful and test posts...")
            # We keep any user-created posts authored by 'mark'
            meaningless_query = Post.objects.exclude(author__username='mark')
            count_deleted = meaningless_query.count()
            meaningless_query.delete()
            self.stdout.write(f"Deleted {count_deleted} old/test posts.")

            # Clean old conversations/messages not involving 'mark'
            Conversation.objects.exclude(requester__username='mark').exclude(owner__username='mark').delete()

        # 2. Authentic Filipino Community Users
        users_data = [
            {
                'username': 'althea_m',
                'password': 'Password123!',
                'display_name': 'Althea Mendoza',
                'neighborhood': 'Brgy. 171 Bagumbong, Caloocan',
                'address': 'Phase 3, Brgy. 171 Bagumbong, Caloocan City',
                'latitude': 14.7432,
                'longitude': 121.0264,
                'minutes_ago': 5,
            },
            {
                'username': 'kuya_ben',
                'password': 'Password123!',
                'display_name': 'Kuya Ben Ramirez',
                'neighborhood': 'Brgy. 177 Camarin, Caloocan',
                'address': 'Area D, Brgy. 177 Camarin, Caloocan City',
                'latitude': 14.7548,
                'longitude': 121.0421,
                'minutes_ago': 1,
            },
            {
                'username': 'nanay_luz',
                'password': 'Password123!',
                'display_name': 'Nanay Luzviminda',
                'neighborhood': 'Brgy. 170 Deparo, Caloocan',
                'address': 'Deparo Road, Brgy. 170, Caloocan City',
                'latitude': 14.7315,
                'longitude': 121.0310,
                'minutes_ago': 20,
            },
            {
                'username': 'dave_v',
                'password': 'Password123!',
                'display_name': 'Dave Valenzuela',
                'neighborhood': 'Grace Park West, Caloocan',
                'address': '8th Avenue, Grace Park West, Caloocan City',
                'latitude': 14.6512,
                'longitude': 120.9881,
                'minutes_ago': 2,
            },
            {
                'username': 'maria_santos',
                'password': 'Password123!',
                'display_name': 'Maria Santos',
                'neighborhood': 'Brgy. UP Campus, Diliman, QC',
                'address': 'CP Garcia Ave, Diliman, Quezon City',
                'latitude': 14.6538,
                'longitude': 121.0685,
                'minutes_ago': 0,  # online
            },
            {
                'username': 'bea_tan',
                'password': 'Password123!',
                'display_name': 'Bea Tan',
                'neighborhood': 'Brgy. Loyola Heights, QC',
                'address': 'Katipunan Ave, Loyola Heights, Quezon City',
                'latitude': 14.6398,
                'longitude': 121.0772,
                'minutes_ago': 12,
            },
            {
                'username': 'paolo_qc',
                'password': 'Password123!',
                'display_name': 'Paolo Reyes',
                'neighborhood': 'Brgy. Commonwealth, QC',
                'address': 'Don Fabian, Brgy. Commonwealth, Quezon City',
                'latitude': 14.6980,
                'longitude': 121.0850,
                'minutes_ago': 45,
            },
            {
                'username': 'mang_tito',
                'password': 'Password123!',
                'display_name': 'Tito Rodolfo',
                'neighborhood': 'Brgy. 400 Sampaloc, Manila',
                'address': 'Dapitan St cor Lacson Ave, Sampaloc, Manila',
                'latitude': 14.6080,
                'longitude': 120.9950,
                'minutes_ago': 15,
            },
            {
                'username': 'nurse_joy',
                'password': 'Password123!',
                'display_name': 'Joy De Leon',
                'neighborhood': 'Brgy. 700 Malate, Manila',
                'address': 'Adriatico St, Malate, Manila',
                'latitude': 14.5710,
                'longitude': 120.9930,
                'minutes_ago': 3,
            },
            {
                'username': 'clara_makati',
                'password': 'Password123!',
                'display_name': 'Clara Reyes',
                'neighborhood': 'Brgy. Poblacion, Makati',
                'address': 'P. Burgos St, Brgy. Poblacion, Makati City',
                'latitude': 14.5650,
                'longitude': 121.0315,
                'minutes_ago': 0,  # online
            },
            {
                'username': 'doc_kristine',
                'password': 'Password123!',
                'display_name': 'Kristine Joy Flores',
                'neighborhood': 'Brgy. San Antonio, Makati',
                'address': 'Kamagong St, San Antonio Village, Makati City',
                'latitude': 14.5620,
                'longitude': 121.0110,
                'minutes_ago': 30,
            },
            {
                'username': 'arvin_pasig',
                'password': 'Password123!',
                'display_name': 'Arvin Gutierrez',
                'neighborhood': 'Brgy. Kapitolyo, Pasig',
                'address': 'East Capitol Drive, Kapitolyo, Pasig City',
                'latitude': 14.5720,
                'longitude': 121.0590,
                'minutes_ago': 18,
            },
            {
                'username': 'miguel_bgc',
                'password': 'Password123!',
                'display_name': 'Miguel Soriano',
                'neighborhood': 'Brgy. Pembo / BGC, Taguig',
                'address': 'Sampaguita St, Brgy. Pembo, Taguig City',
                'latitude': 14.5450,
                'longitude': 121.0610,
                'minutes_ago': 8,
            },
            {
                'username': 'rafael_cebu',
                'password': 'Password123!',
                'display_name': 'Rafael Lim',
                'neighborhood': 'Brgy. Lahug, Cebu City',
                'address': 'Salinas Drive, Brgy. Lahug, Cebu City',
                'latitude': 10.3340,
                'longitude': 123.8960,
                'minutes_ago': 10,
            },
            {
                'username': 'charlene_bacolod',
                'password': 'Password123!',
                'display_name': 'Charlene Gonzaga',
                'neighborhood': 'Brgy. Villamonte, Bacolod',
                'address': 'Burgos St, Brgy. Villamonte, Bacolod City',
                'latitude': 10.6720,
                'longitude': 122.9640,
                'minutes_ago': 25,
            },
            {
                'username': 'jayson_davao',
                'password': 'Password123!',
                'display_name': 'Jayson Morales',
                'neighborhood': 'Brgy. Matina, Davao City',
                'address': 'MacArthur Highway, Matina Crossing, Davao City',
                'latitude': 7.0580,
                'longitude': 125.5900,
                'minutes_ago': 40,
            },
            {
                'username': 'elena_baguio',
                'password': 'Password123!',
                'display_name': 'Elena Corpuz',
                'neighborhood': 'Session Road, Baguio City',
                'address': 'Upper Session Rd, Baguio City',
                'latitude': 16.4120,
                'longitude': 120.5960,
                'minutes_ago': 14,
            },
        ]

        users = {}
        now = timezone.now()
        for u_data in users_data:
            user, created = User.objects.get_or_create(username=u_data['username'])
            if created or not user.has_usable_password():
                user.set_password(u_data['password'])
                user.save()
            user.profile.display_name = u_data['display_name']
            user.profile.neighborhood = u_data['neighborhood']
            user.profile.address = u_data['address']
            user.profile.latitude = u_data['latitude']
            user.profile.longitude = u_data['longitude']
            user.profile.last_active = now - timedelta(minutes=u_data['minutes_ago'])
            user.profile.save()
            users[u_data['username']] = user

        # Also set coordinates for 'mark' if empty
        mark_user = User.objects.filter(username='mark').first()
        if mark_user:
            if not mark_user.profile.latitude or not mark_user.profile.longitude:
                mark_user.profile.neighborhood = mark_user.profile.neighborhood or 'Grace Park, Caloocan'
                mark_user.profile.address = mark_user.profile.address or 'Caloocan City, Metro Manila'
                mark_user.profile.latitude = 14.6512
                mark_user.profile.longitude = 120.9881
                mark_user.profile.save()
            users['mark'] = mark_user

        # 3. Rich, realistic Philippine neighborhood posts
        posts_data = [
            # === TOOLS ===
            {
                'author': users['althea_m'],
                'type': 'request',
                'title': 'Pahiram ng heavy-duty rotary hammer drill (concrete wall)',
                'description': 'Magandang araw mga kapitbahay! Need to mount heavy floating shelves and kitchen racks on concrete hollow block walls. Looking to borrow an SDS/rotary hammer drill with 6mm or 8mm masonry bits for 2 to 3 hours this Saturday afternoon. Ingatan ko po maigi, can leave a valid government ID or deposit.',
                'category': 'Tools',
                'neighborhood': 'Brgy. 171 Bagumbong, Caloocan',
                'address': 'Phase 3, Brgy. 171 Bagumbong, Caloocan City',
                'latitude': 14.7432,
                'longitude': 121.0264,
                'hours_ago': 2,
            },
            {
                'author': users['kuya_ben'],
                'type': 'offer',
                'title': 'High-pressure washer with snow foam cannon (car/motor wash)',
                'description': 'Available to lend our Lotus 1400W pressure washer and foam blaster this Sunday. Perfect if you need to deep clean your motorcycle, car underchassis, or mossy patio tiles. Just bring your own standard garden hose quick-connector.',
                'category': 'Tools',
                'neighborhood': 'Brgy. 177 Camarin, Caloocan',
                'address': 'Area D, Brgy. 177 Camarin, Caloocan City',
                'latitude': 14.7548,
                'longitude': 121.0421,
                'hours_ago': 5,
            },
            {
                'author': users['maria_santos'],
                'type': 'offer',
                'title': '12-foot aluminum folding multipurpose ladder',
                'description': 'Have a sturdy Werner 12ft folding step ladder that can convert into an extension ladder. Great for pruning high tree branches, clearing roof gutters, or repainting high walls. Free to borrow for UP / Katipunan neighbors.',
                'category': 'Tools',
                'neighborhood': 'Brgy. UP Campus, Diliman, QC',
                'address': 'CP Garcia Ave, Diliman, Quezon City',
                'latitude': 14.6538,
                'longitude': 121.0685,
                'hours_ago': 9,
            },
            {
                'author': users['mang_tito'],
                'type': 'request',
                'title': 'Pahiram po ng pipe wrench at teflon tape (lababo leak)',
                'description': 'May tumatagas po na PVC drainage pipe sa ilalim ng lababo namin. Need lang po ng pipe wrench/pliers para maayos at mapalitan yung gasket ngayong hapon. Within Sampaloc near UST or España po sana.',
                'category': 'Tools',
                'neighborhood': 'Brgy. 400 Sampaloc, Manila',
                'address': 'Dapitan St cor Lacson Ave, Sampaloc, Manila',
                'latitude': 14.6080,
                'longitude': 120.9950,
                'hours_ago': 1,
            },
            {
                'author': users['charlene_bacolod'],
                'type': 'offer',
                'title': 'Heavy-duty electric grass cutter / weed trimmer',
                'description': 'Ingco grass trimmer with safety goggles and extra nylon cord. If you need to trim your overgrown front lawn or backyard weeds this weekend, feel free to borrow. Pick up near Burgos St.',
                'category': 'Tools',
                'neighborhood': 'Brgy. Villamonte, Bacolod',
                'address': 'Burgos St, Brgy. Villamonte, Bacolod City',
                'latitude': 10.6720,
                'longitude': 122.9640,
                'hours_ago': 14,
            },

            # === FOOD ===
            {
                'author': users['nanay_luz'],
                'type': 'offer',
                'title': 'Fresh native calamansi harvest from backyard (free 3 bags)',
                'description': 'Namunga nang sobra-sobra ang native calamansi tree namin sa bakuran. Nakaprepare na in 3 brown grocery bags (halos 1 kilo each). Sobrang bango at makatas, perfect pang-calamansi juice, sawsawan sa pritong isda, o pambistek. Libre po for pickup!',
                'category': 'Food',
                'neighborhood': 'Brgy. 170 Deparo, Caloocan',
                'address': 'Deparo Road, Brgy. 170, Caloocan City',
                'latitude': 14.7315,
                'longitude': 121.0310,
                'hours_ago': 3,
            },
            {
                'author': users['bea_tan'],
                'type': 'offer',
                'title': 'Authentic Batangas pure cacao tablea for champorado',
                'description': 'My grandmother brought home a big sack of traditional unsweetened chocolate tablea from Lipa, Batangas. Sharing 4 packs (5 big rolls each) to fellow chocolate/champorado lovers in Loyola Heights. Super rich aroma and natural cocoa butter!',
                'category': 'Food',
                'neighborhood': 'Brgy. Loyola Heights, QC',
                'address': 'Katipunan Ave, Loyola Heights, Quezon City',
                'latitude': 14.6398,
                'longitude': 121.0772,
                'hours_ago': 6,
            },
            {
                'author': users['clara_makati'],
                'type': 'request',
                'title': 'Looking for active sourdough starter / levain discard',
                'description': 'Baking sourdough country batards at home this weekend. Looking to adopt a tablespoon of healthy, active 100% hydration sourdough culture (rye or bread flour). Can trade with fresh chocolate chip cookies or homemade kombucha!',
                'category': 'Food',
                'neighborhood': 'Brgy. Poblacion, Makati',
                'address': 'P. Burgos St, Brgy. Poblacion, Makati City',
                'latitude': 14.5650,
                'longitude': 121.0315,
                'hours_ago': 4,
            },
            {
                'author': users['rafael_cebu'],
                'type': 'offer',
                'title': 'Freshly baked warm pan de sal & Spanish bread (2 dozen)',
                'description': 'Baked extra breakfast buns this morning in our home deck oven! Still warm and buttery soft. Free 2 dozen for boarding house students or neighbors living along Lahug / near JY Square.',
                'category': 'Food',
                'neighborhood': 'Brgy. Lahug, Cebu City',
                'address': 'Salinas Drive, Brgy. Lahug, Cebu City',
                'latitude': 10.3340,
                'longitude': 123.8960,
                'hours_ago': 7,
            },
            {
                'author': users['arvin_pasig'],
                'type': 'offer',
                'title': 'Extra rooted stem cuttings: Sweet basil, rosemary, & pandan',
                'description': 'Propagated healthy stem cuttings in water bottles with active root nodes. Ready for direct potting in soil! Sweet Italian basil, fragrant pandan, and culinary rosemary. Great for your balcony edible garden.',
                'category': 'Food',
                'neighborhood': 'Brgy. Kapitolyo, Pasig',
                'address': 'East Capitol Drive, Kapitolyo, Pasig City',
                'latitude': 14.5720,
                'longitude': 121.0590,
                'hours_ago': 11,
            },

            # === GOODS ===
            {
                'author': users['althea_m'],
                'type': 'offer',
                'title': 'Pre-loved baby boy clothes (0-6 mos) & foldable Apruva stroller',
                'description': 'Clean, freshly laundered baby onesies, mittens, and swaddles plus a lightweight Apruva folding travel stroller. All in great condition. Prefer to pass on to an expectant mother or family with newborn in North Caloocan.',
                'category': 'Goods',
                'neighborhood': 'Brgy. 171 Bagumbong, Caloocan',
                'address': 'Phase 3, Brgy. 171 Bagumbong, Caloocan City',
                'latitude': 14.7432,
                'longitude': 121.0264,
                'hours_ago': 10,
            },
            {
                'author': users['mang_tito'],
                'type': 'request',
                'title': 'Need clean balikbayan boxes or sturdy cartons for moving',
                'description': 'Moving out of dorm unit after board exam review next week. Looking for 4 to 5 sturdy corrugated boxes / balikbayan boxes. Can pick up anytime around Sampaloc, Morayta, or UST area.',
                'category': 'Goods',
                'neighborhood': 'Brgy. 400 Sampaloc, Manila',
                'address': 'Dapitan St cor Lacson Ave, Sampaloc, Manila',
                'latitude': 14.6080,
                'longitude': 120.9950,
                'hours_ago': 8,
            },
            {
                'author': users['dave_v'],
                'type': 'request',
                'title': 'Pahiram po ng 2 spare 5-gallon blue water jugs',
                'description': 'May scheduled Maynilad water service interruption bukas sa street namin mula 10PM hanggang hapon. Looking to borrow 2 clean 5-gallon round or slim water containers for tap water storage. Ibabalik po agad the next day.',
                'category': 'Goods',
                'neighborhood': 'Grace Park West, Caloocan',
                'address': '8th Avenue, Grace Park West, Caloocan City',
                'latitude': 14.6512,
                'longitude': 120.9881,
                'hours_ago': 1,
            },
            {
                'author': users['paolo_qc'],
                'type': 'offer',
                'title': 'DepEd Grade 9 & 10 Science & Math reviewer workbooks',
                'description': 'Complete set of high school textbooks, MSA review modules, and practice workbooks in good readable condition. Free for any public school student or tutor in Phil-Am / West Ave area.',
                'category': 'Goods',
                'neighborhood': 'Brgy. Phil-Am, Quezon City',
                'address': 'West Avenue cor EDSA, Phil-Am, Quezon City',
                'latitude': 14.6525,
                'longitude': 121.0315,
                'hours_ago': 16,
            },
            {
                'author': users['jayson_davao'],
                'type': 'offer',
                'title': 'Cat scratch tower & unopened kitten kibble bag (1.5kg)',
                'description': 'Our kitten recently shifted to veterinary wet food. Giving away an unopened 1.5kg bag of SmartHeart kitten kibble and a 2-tier sisal rope scratch tree in clean condition. Pick up near Matina Crossing.',
                'category': 'Goods',
                'neighborhood': 'Brgy. Matina, Davao City',
                'address': 'MacArthur Highway, Matina Crossing, Davao City',
                'latitude': 7.0580,
                'longitude': 125.5900,
                'hours_ago': 22,
            },

            # === SKILLS ===
            {
                'author': users['kuya_ben'],
                'type': 'offer',
                'title': 'Free bicycle chain lube, derailleur tuning & brake check',
                'description': 'Have a bike maintenance stand, torque tools, and chain degreaser/lube at home. Any commuter cyclist or delivery rider in Camarin who needs brake adjustment or gear shifting tuned up is welcome to drop by this Saturday morning 8am-11am.',
                'category': 'Skills',
                'neighborhood': 'Brgy. 177 Camarin, Caloocan',
                'address': 'Area D, Brgy. 177 Camarin, Caloocan City',
                'latitude': 14.7548,
                'longitude': 121.0421,
                'hours_ago': 4,
            },
            {
                'author': users['maria_santos'],
                'type': 'offer',
                'title': 'Free Math & Science tutoring for Grade 7-10 high school kids',
                'description': 'UP Diliman Engineering alumnus offering 2 hours of free homework coaching and algebra/geometry review this Sunday afternoon at the community reading hub. Limited to 4 students so everyone gets hands-on help.',
                'category': 'Skills',
                'neighborhood': 'Brgy. UP Campus, Diliman, QC',
                'address': 'CP Garcia Ave, Diliman, Quezon City',
                'latitude': 14.6538,
                'longitude': 121.0685,
                'hours_ago': 12,
            },
            {
                'author': users['doc_kristine'],
                'type': 'offer',
                'title': 'Assistance configuring home Wi-Fi mesh & dead spot fixes',
                'description': 'Network engineer neighbor here. If your condo or townhouse has Wi-Fi dead spots, poor coverage in bedrooms, or need help configuring TP-Link Deco / Asus mesh routers securely, happy to help a neighbor over the weekend.',
                'category': 'Skills',
                'neighborhood': 'Brgy. San Antonio, Makati',
                'address': 'Kamagong St, San Antonio Village, Makati City',
                'latitude': 14.5620,
                'longitude': 121.0110,
                'hours_ago': 18,
            },
            {
                'author': users['arvin_pasig'],
                'type': 'request',
                'title': 'Looking for sewing machine help: Hemming 3 window curtains',
                'description': 'Bought new blackout curtains for our living room but they are about 5 inches too long. Looking for a neighbor with a sewing machine to hem them straight. Happy to pay or trade with fresh baked lasagna!',
                'category': 'Skills',
                'neighborhood': 'Brgy. Kapitolyo, Pasig',
                'address': 'East Capitol Drive, Kapitolyo, Pasig City',
                'latitude': 14.5720,
                'longitude': 121.0590,
                'hours_ago': 19,
            },
            {
                'author': users['elena_baguio'],
                'type': 'offer',
                'title': 'Beginner acoustic guitar lessons (basic chords & strumming)',
                'description': 'Play acoustic folk and indie songs. Offering free 45-minute beginner coaching for chords (G, C, D, Em), rhythm strumming, and finger transitions. Bring your own guitar near Session Road cafe.',
                'category': 'Skills',
                'neighborhood': 'Session Road, Baguio City',
                'address': 'Upper Session Rd, Baguio City',
                'latitude': 16.4120,
                'longitude': 120.5960,
                'hours_ago': 25,
            },

            # === HELP ===
            {
                'author': users['dave_v'],
                'type': 'request',
                'title': 'Urgent: Car battery jumpstart near Morning Breeze gate',
                'description': 'Naiwan po nakabukas ang dome light kagabi, ayaw mag-crank ng engine ngayon. I have jumper cables ready in my trunk! Just need a kind neighbor with a running car/van to hook up for 3 minutes near Brgy. 83 gate.',
                'category': 'Help',
                'neighborhood': 'Morning Breeze, Caloocan',
                'address': 'Rizal Ave Ext, Morning Breeze, Caloocan City',
                'latitude': 14.6575,
                'longitude': 120.9920,
                'hours_ago': 0,  # Just posted!
            },
            {
                'author': users['paolo_qc'],
                'type': 'request',
                'title': 'Pagtulong magbaba ng heavy solid wood dining table (15 mins)',
                'description': 'Need 1 or 2 malalakas na kapitbahay to help carry a 6-seater narra dining table from 2nd floor down to the ground floor garage. Takes about 15 minutes only. Meron pong malamig na merienda, buko pandan, at halo-halo for your help!',
                'category': 'Help',
                'neighborhood': 'Brgy. Commonwealth, QC',
                'address': 'Don Fabian, Brgy. Commonwealth, Quezon City',
                'latitude': 14.6980,
                'longitude': 121.0850,
                'hours_ago': 7,
            },
            {
                'author': users['nurse_joy'],
                'type': 'offer',
                'title': 'Can accompany senior citizen neighbors for clinic or grocery',
                'description': 'Registered nurse on rest day this Friday morning. Happy to accompany or drive any elderly neighbor along Taft / Malate to PGH or local clinic for check-up, blood pressure check, or prescription refills.',
                'category': 'Help',
                'neighborhood': 'Brgy. 700 Malate, Manila',
                'address': 'Adriatico St, Malate, Manila',
                'latitude': 14.5710,
                'longitude': 120.9930,
                'hours_ago': 13,
            },
            {
                'author': users['miguel_bgc'],
                'type': 'request',
                'title': 'Cat-sitting & indoor plant watering favor (3 days)',
                'description': 'Flying to Iloilo for family reunion from Oct 24 to 27. Looking for a trustworthy neighbor near Pembo/BGC to visit once a day for 15 minutes: refill water bowl, feed our gentle cat "Oreo", and water balcony monsteras.',
                'category': 'Help',
                'neighborhood': 'Brgy. Pembo / BGC, Taguig',
                'address': 'Sampaguita St, Brgy. Pembo, Taguig City',
                'latitude': 14.5450,
                'longitude': 121.0610,
                'hours_ago': 21,
            },
            {
                'author': users['charlene_bacolod'],
                'type': 'offer',
                'title': 'Proofreading & translation (English, Filipino, Hiligaynon)',
                'description': 'Former university campus journalist. Happy to assist high school or college neighbors proofread scholarship essays, resumes, thesis abstracts, or official barangay clearance documents.',
                'category': 'Help',
                'neighborhood': 'Brgy. Jaro, Iloilo City',
                'address': 'E. Lopez St, Jaro Plaza, Iloilo City',
                'latitude': 10.7290,
                'longitude': 122.5580,
                'hours_ago': 26,
            },

            # === OTHER ===
            {
                'author': users['nanay_luz'],
                'type': 'offer',
                'title': '20 clean glass jars with tight lids (great for spices / crafts)',
                'description': 'Cleaned and soaked in hot water to remove labels. Clear 250ml-350ml glass jars with metal twist lids. Very useful for pantry spices, chili garlic oil, candle pouring, or craft organizers. Free for pickup!',
                'category': 'Other',
                'neighborhood': 'Brgy. 165 Bagbaguin, Caloocan',
                'address': 'General Luis St, Brgy. 165 Bagbaguin, Caloocan City',
                'latitude': 14.7120,
                'longitude': 121.0115,
                'hours_ago': 8,
            },
            {
                'author': users['paolo_qc'],
                'type': 'offer',
                'title': 'Plant nursery plastic pots & seedling propagation trays',
                'description': 'Downsizing our rooftop garden. Giving away 20 seedling trays, 15 black durable 6-inch plastic pots, and half a sack of coconut coir peat. Free for fellow plantitas and plantitos in Batasan Hills.',
                'category': 'Other',
                'neighborhood': 'Brgy. Batasan Hills, QC',
                'address': 'IBP Road, Brgy. Batasan Hills, Quezon City',
                'latitude': 14.6850,
                'longitude': 121.0990,
                'hours_ago': 17,
            },
            {
                'author': users['rafael_cebu'],
                'type': 'request',
                'title': 'Looking to borrow portable HDMI projector for community kids',
                'description': 'Organizing an outdoor educational movie night for barangay children this Saturday 6:30PM. We have the white projector cloth and soundbar, just need a portable projector with HDMI cable. Babalik po kaagad after 9PM.',
                'category': 'Other',
                'neighborhood': 'Brgy. Banilad, Cebu City',
                'address': 'Gov. M. Cuenco Ave, Banilad, Cebu City',
                'latitude': 10.3420,
                'longitude': 123.9180,
                'hours_ago': 20,
            },
        ]

        created_posts = []
        for p in posts_data:
            hours = p.pop('hours_ago', 1)
            post = Post.objects.create(
                status='open',
                **p
            )
            # Set created_at backwards so timestamps look natural
            Post.objects.filter(id=post.id).update(created_at=now - timedelta(hours=hours))
            post.refresh_from_db()
            created_posts.append(post)

        self.stdout.write(f"Successfully created {len(created_posts)} authentic Philippine posts.")

        # 4. Realistic sample neighbor conversations
        tablea_post = next((p for p in created_posts if 'tablea' in p.title.lower()), None)
        if tablea_post:
            conv1, _ = Conversation.objects.get_or_create(
                post=tablea_post,
                requester=users['maria_santos'],
                defaults={'owner': tablea_post.author}
            )
            if not conv1.messages.exists():
                Message.objects.create(
                    conversation=conv1,
                    sender=users['maria_santos'],
                    text='Hi Bea! May available pa bang tablea? Would love to make champorado for my housemates this morning.'
                )
                Message.objects.create(
                    conversation=conv1,
                    sender=users['bea_tan'],
                    text='Hi Maria! Yes, may 2 packs pa dito. You can pick them up at our gate anytime after 2pm!'
                )
                Message.objects.create(
                    conversation=conv1,
                    sender=users['maria_santos'],
                    text='Salamat nang marami Bea! Daanan ko po around 3:30pm pagkauwi galing library.'
                )

        calamansi_post = next((p for p in created_posts if 'calamansi' in p.title.lower()), None)
        if calamansi_post:
            conv2, _ = Conversation.objects.get_or_create(
                post=calamansi_post,
                requester=users['althea_m'],
                defaults={'owner': calamansi_post.author}
            )
            if not conv2.messages.exists():
                Message.objects.create(
                    conversation=conv2,
                    sender=users['althea_m'],
                    text='Magandang araw Nanay Luz! Pwede po bang humingi ng 1 bag ng calamansi? Gagawa po sana ako ng honey calamansi juice para sa ubo ng anak ko.'
                )
                Message.objects.create(
                    conversation=conv2,
                    sender=users['nanay_luz'],
                    text='Oo naman Althea! Nakatabi na ang 1 bag para sa iyo dito sa may porch table. Daan ka lang anytime bago magdilim.'
                )
                Message.objects.create(
                    conversation=conv2,
                    sender=users['althea_m'],
                    text='Maraming salamat po Nanay Luz, daanan ko po mamayang 5pm!'
                )

        drill_post = next((p for p in created_posts if 'hammer drill' in p.title.lower()), None)
        if drill_post:
            conv3, _ = Conversation.objects.get_or_create(
                post=drill_post,
                requester=users['kuya_ben'],
                defaults={'owner': drill_post.author}
            )
            if not conv3.messages.exists():
                Message.objects.create(
                    conversation=conv3,
                    sender=users['kuya_ben'],
                    text='Hi Althea, may Makita rotary hammer drill ako dito sa Camarin with complete masonry bits. Pwede mo mahiram sa Sabado mula 1pm hanggang gabi.'
                )
                Message.objects.create(
                    conversation=conv3,
                    sender=users['althea_m'],
                    text='Naku Kuya Ben hulog ka ng langit! Iwan ko po valid ID ko and ibabalik ko bago mag-7pm. Salamat po!'
                )

        # 5. Clear all relevant caches
        invalidate_posts_cache()
        cache.delete('neighborhoods_list')

        self.stdout.write(self.style.SUCCESS("All Philippine neighborhood seeds created and caches cleared successfully!"))
