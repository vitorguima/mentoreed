import factory
from allauth.socialaccount.models import EmailAddress


class EmailAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmailAddress

    user = factory.SubFactory("core_apps.users.tests.factories.UserFactory")
