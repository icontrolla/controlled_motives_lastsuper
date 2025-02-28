from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from celery import shared_task
import openai
from .models import Artwork, Post, Profile, ArtistProfile
from .utils import send_login_email

User = get_user_model()


### 1. Task for Trending Artworks ###
@shared_task
def update_trending_artworks():
    artworks = Artwork.objects.all()
    for artwork in artworks:
        artwork.is_trending = artwork.flowers > 50  # Simplified condition
        artwork.save()


### 2. Notify on New Artwork ###
@receiver(post_save, sender=Artwork)
def notify_new_artwork(sender, instance, created, **kwargs):
    if created:
        print(f"New artwork added: {instance.title}")


### 3. Send Email on User Login ###
@receiver(user_logged_in)
def send_email_on_login(sender, request, user, **kwargs):
    send_login_email(user, request)  # Ensure `send_login_email` is correctly defined in utils


### 4. Update Post Count (Profile) ###
@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
def update_post_count(sender, instance, **kwargs):
    profile = instance.user.profile
    profile.update_post_count()


### 5. Create User Profile ###
@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


### 6. Create Artist Profile ###
@receiver(post_save, sender=User)
def create_artist_profile(sender, instance, created, **kwargs):
    if created:
        ArtistProfile.objects.create(user=instance)


### 7. Generate Caption for Posts ###
@receiver(pre_save, sender=Post)
def generate_caption(sender, instance, **kwargs):
    if instance.generate_caption_with_ai and not instance.caption:
        if instance.image:
            try:
                # Configure OpenAI API key
                openai.api_key = "your-openai-api-key"  # Replace with your OpenAI API key

                # Generate caption (text prompt instead of image upload)
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt="Describe this image in one sentence with an artistic impression.",
                    max_tokens=50
                )
                instance.caption = response.choices[0].text.strip()
            except Exception as e:
                print(f"Error generating caption: {e}")
