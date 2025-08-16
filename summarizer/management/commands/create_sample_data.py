from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from summarizer.models import Summary, UserProfile


class Command(BaseCommand):
    help = 'Create sample data for testing the AI summarizer'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to create sample data for'
        )
    
    def handle(self, *args, **options):
        username = options['user']
        
        try:
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(f'Found user: {user.username}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist. Creating...')
            )
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='testpass123'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created user: {user.username}')
            )
        
        # Ensure user profile exists
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created user profile for {user.username}')
            )
        
        # Create sample summary
        sample_text = """
        Meeting Notes - Project Alpha Review
        Date: August 16, 2025
        Attendees: John Doe, Jane Smith, Mike Johnson, Sarah Wilson
        
        Agenda Items Discussed:
        
        1. Project Timeline Review
        - Current milestone completion at 75%
        - Identified potential delays in testing phase
        - Need to allocate additional resources for Q4
        
        2. Budget Analysis
        - Currently under budget by 15%
        - Savings from vendor negotiations
        - Proposal to reinvest savings into marketing
        
        3. Technical Challenges
        - Performance optimization required for mobile platform
        - Database scaling concerns for expected user growth
        - Integration issues with third-party API resolved
        
        4. Action Items
        - John to provide updated timeline by Friday
        - Jane to coordinate with QA team for testing schedule
        - Mike to present budget reallocation proposal next week
        - Sarah to finalize vendor contracts by month-end
        
        5. Next Steps
        - Weekly check-ins every Tuesday at 2 PM
        - Milestone review scheduled for September 1st
        - Stakeholder presentation planned for September 15th
        
        Meeting concluded at 3:30 PM with all action items assigned and deadlines confirmed.
        """
        
        summary, created = Summary.objects.get_or_create(
            user=user,
            title='Project Alpha Review Meeting Notes',
            defaults={
                'summary_type': 'meeting',
                'original_text': sample_text.strip(),
                'custom_prompt': 'Summarize this meeting in bullet points for executives, highlighting key decisions and action items.',
                'status': 'draft'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created sample summary: {summary.title}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Sample summary already exists: {summary.title}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample data setup complete!\n'
                f'User: {user.username}\n'
                f'Summary ID: {summary.id}\n'
                f'You can now test the AI summarizer with this data.'
            )
        )
