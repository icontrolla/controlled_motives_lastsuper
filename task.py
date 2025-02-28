from celery import shared_task
from .models import Artwork

@shared_task
def update_trending_artworks():
    """Automatically update trending status for artworks based on views and likes."""
    artworks = Artwork.objects.all()
    for artwork in artworks:
        if artwork.likes > 50:  # Example threshold
            artwork.is_trending = True
        else:
            artwork.is_trending = False
        artwork.save()
