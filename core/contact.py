from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


class ContactThrottle(AnonRateThrottle):
    scope = 'contact'


class ContactView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ContactThrottle]
    authentication_classes = []

    def post(self, request):
        first_name = (request.data.get('firstName') or '').strip()
        last_name = (request.data.get('lastName') or '').strip()
        agency = (request.data.get('agency') or '').strip()
        email = (request.data.get('email') or '').strip()
        message = (request.data.get('message') or '').strip()

        if not first_name or not last_name or not email:
            return Response(
                {'error': {'detail': 'First name, last name, and email are required.'}},
                status=400,
            )
        if len(message) > 5000:
            return Response(
                {'error': {'detail': 'Message is too long.'}},
                status=400,
            )

        full_name = f'{first_name} {last_name}'.strip()
        body = (
            f'Name: {full_name}\n'
            f'Email: {email}\n'
            f'Agency / Department: {agency or "Not provided"}\n\n'
            f'Message:\n{message or "No message provided."}\n'
        )
        email_msg = EmailMessage(
            subject=f'KLYVOREK contact form: {full_name}',
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['klyvorek@gmail.com'],
            reply_to=[email],
        )
        email_msg.send(fail_silently=False)
        return Response({'message': 'Message sent.'})
