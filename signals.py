from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from mainapp.models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Auto-assign admin role if superuser
        role = 'admin' if instance.is_superuser else 'farmer'

        UserProfile.objects.create(
            user=instance,
            role=role,
            phone=''
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
