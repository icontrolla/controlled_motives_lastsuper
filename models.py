from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import requests
import openai
import datetime

my_date = timezone.make_aware(datetime.datetime.now())
# Subscription Plan Model

# Thrift Store Item Model
class ThriftStoreItem(models.Model):
    name = models.CharField(max_length=255)  # Item name
    description = models.TextField()  # Item description
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Item price
    image = models.ImageField(upload_to='thrift_store_items/')  # Image of the item
    created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto timestamp for updates

    objects = models.Manager()


    def __str__(self):
        return self.name


class EmailAddress(models.Model):
    email = models.EmailField(unique=True)  # Remove conditionally unique constraints


# Feedback Model
class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback")  # User giving feedback
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating (1 to 5)
    comment = models.TextField(blank=True, null=True)  # Optional comment
    created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp for creation
    is_helpful = models.PositiveIntegerField(default=0)  # Track how many users found this feedback helpful
    is_visible = models.BooleanField(default=True)  # If feedback is visible to other users
    source = models.CharField(max_length=50, choices=[('website', 'Website'), ('mobile', 'Mobile')], default='website')  # Where the feedback came from
    admin_notes = models.TextField(blank=True, null=True)
    is_flagged = models.BooleanField(default=False)  # Flag for inappropriate or spammy feedback
    helpful = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return f"Feedback from {self.user} - Rating: {self.rating}"

    def mark_as_helpful(self):
        """Method to increment the helpful count."""
        self.is_helpful += 1
        self.save()

    def flag_as_inappropriate(self):
        """Method to flag feedback as inappropriate."""
        self.is_flagged = True
        self.save()

    def unflag_feedback(self):
        """Method to remove the inappropriate flag."""
        self.is_flagged = False
        self.save()

        
# Models for Art and Moments
class Moment(models.Model):
    title = models.CharField(max_length=255)  # Moment title
    description = models.TextField(blank=True, null=True)  # Optional description
    image = models.ImageField(upload_to='aesthetic_moments/')  # Associated image
    created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp for creation

    objects = models.Manager()


    def __str__(self):
        return self.title


class ArtGallery(models.Model):
    title = models.CharField(max_length=255)  # Gallery title
    description = models.TextField(blank=True, null=True)  # Optional description
    image = models.ImageField(upload_to='art_galleries/')  # Gallery image
    created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp for creation
    flowers = models.IntegerField(default=0)
    users_who_flowered = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='flowered', blank=True)

    is_tokenized = models.BooleanField(default=False)  # Whether the artwork is tokenized
    blockchain_txn_hash = models.CharField(max_length=255, blank=True, null=True, unique=True)  # Transaction hash
    blockchain_address = models.CharField(max_length=255, blank=True, null=True)  # Address storing the NFT
    blockchain_network = models.CharField(
        max_length=50,
        choices=[
            ('Ethereum', 'Ethereum'),
            ('Polygon', 'Polygon'),
            ('Solana', 'Solana'),
            ('Tezos', 'Tezos'),
        ],
        default='Ethereum'
    )  # Blockchain network used

    objects = models.Manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# Static File Model for File Management
class StaticFile(models.Model):
    file_name = models.CharField(max_length=255)  # File name
    file_path = models.CharField(max_length=255)  # Path to the file
    description = models.TextField(blank=True, null=True)  # Optional description

    objects = models.Manager()

    def __str__(self):
        return self.file_name


# Models for Artworks
class AbstractArtwork(models.Model):
    title = models.CharField(max_length=255)  # Artwork title
    description = models.TextField(blank=True, null=True)  # Optional description
    image = models.ImageField(upload_to='abstract_artworks/')  # Artwork image
    created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp for creation

    def __str__(self):
        return self.title

    objects = models.Manager()


class DrawingArtwork(models.Model):
    title = models.CharField(max_length=255)  # Drawing title
    description = models.TextField(blank=True, null=True)  # Optional description
    image = models.ImageField(upload_to='drawing_artworks/')  # Associated image
    created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp for creation

    objects = models.Manager()

    def __str__(self):
        return self.title


# Artist Model
from django.db import models
from django.conf import settings

class Artist(models.Model):
    CATEGORY_CHOICES = [
        ('major', 'Major'),
        ('upcoming', 'Upcoming'),
        ('trending', 'Trending')
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, unique=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='artist_profiles/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_major = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    blockchain_address = models.CharField(max_length=42, blank=True, help_text="Artist's blockchain wallet address")
    medium = models.CharField(
        max_length=50,
        choices=[
            ('painting', 'Painting'),
            ('photography', 'Photography'),
            ('drawing', 'Drawing'),
            ('mixed', 'Mixed Media'),
        ],
        default='painting',
        help_text="Artist's primary medium for icon display"
    )

    objects = models.Manager()

    def __str__(self):
        return f"Artist Profile: {self.user}"

    class Meta:
        ordering = ['user']

class Flower(models.Model):
    count = models.IntegerField(default=0)

    objects = models.Manager()


class FineArt(models.Model):
    STYLE_CHOICES = [
        ('realism', 'Realism'),
        ('abstract', 'Abstract'),
        ('impressionism', 'Impressionism'),
        ('surrealism', 'Surrealism'),
        ('expressionism', 'Expressionism'),
        ('minimalism', 'Minimalism'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='finearts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='finearts/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='finearts_created')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    style = models.CharField(max_length=50, choices=STYLE_CHOICES, default='other')
    is_for_sale = models.BooleanField(default=False)
    flowers = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NFT Fields
    is_nft = models.BooleanField(default=False)
    nft_contract_address = models.CharField(max_length=255, blank=True, null=True)
    nft_token_id = models.CharField(max_length=255, blank=True, null=True)
    blockchain = models.CharField(
        max_length=100,
        choices=[('ethereum', 'Ethereum'), ('polygon', 'Polygon'), ('solana', 'Solana'), ('other', 'Other')],
        blank=True,
        null=True,
    )
    mint_date = models.DateTimeField(blank=True, null=True)
    nft_url = models.URLField(blank=True, null=True)
    nft_metadata = models.JSONField(blank=True, null=True, help_text="Metadata of the NFT")
    copyright_hash = models.CharField(max_length=255, blank=True, null=True)

    objects = models.Manager()

    def save(self, *args, **kwargs):
        if self.mint_date:
            if isinstance(self.mint_date, str):
                self.mint_date = timezone.make_aware(timezone.datetime.fromisoformat(self.mint_date))
            elif timezone.is_naive(self.mint_date):
                self.mint_date = timezone.make_aware(self.mint_date)

        if self.is_nft and self.nft_contract_address and self.nft_token_id:
            self.nft_url = f"https://opensea.io/assets/{self.nft_contract_address}/{self.nft_token_id}"
            self.nft_metadata = self.fetch_nft_metadata()

        super().save(*args, **kwargs)

    def fetch_nft_metadata(self):
        if self.nft_contract_address and self.nft_token_id:
            api_url = f"https://api.opensea.io/api/v1/asset/{self.nft_contract_address}/{self.nft_token_id}/"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching NFT metadata: {e}")
        return None

    def __str__(self):
        return self.title



    class Meta:
        verbose_name = "Fine Art"
        verbose_name_plural = "Fine Arts"


class ConceptualMixedMedia(models.Model):
    STYLE_CHOICES = [
        ('conceptual', 'Conceptual Art'),
        ('mixed_media', 'Mixed Media'),
        ('installation', 'Installation Art'),
        ('performance', 'Performance Art'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conceptual_mixed_media')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='conceptual_mixed_media/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='conceptual_mixed_media_created')
    thumbnail = models.ImageField(upload_to="cinematography_thumbnails/", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    style = models.CharField(max_length=50, choices=STYLE_CHOICES, default='other')
    is_for_sale = models.BooleanField(default=False)
    flowers = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NFT Fields
    is_nft = models.BooleanField(default=False)
    nft_contract_address = models.CharField(max_length=255, blank=True, null=True)
    nft_token_id = models.CharField(max_length=255, blank=True, null=True)
    blockchain = models.CharField(
        max_length=100,
        choices=[('ethereum', 'Ethereum'), ('polygon', 'Polygon'), ('solana', 'Solana'), ('other', 'Other')],
        blank=True,
        null=True,
    )
    mint_date = models.DateTimeField(blank=True, null=True)
    nft_url = models.URLField(blank=True, null=True)
    nft_metadata = models.JSONField(blank=True, null=True, help_text="Metadata of the NFT")
    copyright_hash = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.mint_date:
            if isinstance(self.mint_date, str):
                self.mint_date = timezone.make_aware(timezone.datetime.fromisoformat(self.mint_date))
            elif timezone.is_naive(self.mint_date):
                self.mint_date = timezone.make_aware(self.mint_date)

        if self.is_nft and self.nft_contract_address and self.nft_token_id:
            self.nft_url = f"https://opensea.io/assets/{self.nft_contract_address}/{self.nft_token_id}"
            self.nft_metadata = self.fetch_nft_metadata()

        super().save(*args, **kwargs)

    def fetch_nft_metadata(self):
        if self.nft_contract_address and self.nft_token_id:
            api_url = f"https://api.opensea.io/api/v1/asset/{self.nft_contract_address}/{self.nft_token_id}/"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching NFT metadata: {e}")
        return None

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Conceptual & Mixed Media"
        verbose_name_plural = "Conceptual & Mixed Media"


class AbstractArt(models.Model):
    STYLE_CHOICES = [
        ('geometric', 'Geometric'),
        ('lyrical', 'Lyrical'),
        ('minimalist', 'Minimalist'),
        ('cubism', 'Cubism'),
        ('surreal', 'Surreal'),
        ('expressionist', 'Expressionist'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='abstractarts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='abstractarts/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='abstractarts_created')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    style = models.CharField(max_length=50, choices=STYLE_CHOICES, default='other')
    is_for_sale = models.BooleanField(default=False)
    flowers = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NFT Fields
    is_nft = models.BooleanField(default=False)
    nft_contract_address = models.CharField(max_length=255, blank=True, null=True)
    nft_token_id = models.CharField(max_length=255, blank=True, null=True)
    blockchain = models.CharField(
        max_length=100,
        choices=[('ethereum', 'Ethereum'), ('polygon', 'Polygon'), ('solana', 'Solana'), ('other', 'Other')],
        blank=True,
        null=True,
    )
    mint_date = models.DateTimeField(blank=True, null=True)
    nft_url = models.URLField(blank=True, null=True)
    nft_metadata = models.JSONField(blank=True, null=True, help_text="Metadata of the NFT")
    copyright_hash = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.mint_date:
            if isinstance(self.mint_date, str):
                self.mint_date = timezone.make_aware(timezone.datetime.fromisoformat(self.mint_date))
            elif timezone.is_naive(self.mint_date):
                self.mint_date = timezone.make_aware(self.mint_date)

        if self.is_nft and self.nft_contract_address and self.nft_token_id:
            self.nft_url = f"https://opensea.io/assets/{self.nft_contract_address}/{self.nft_token_id}"
            self.nft_metadata = self.fetch_nft_metadata()

        super().save(*args, **kwargs)

    def fetch_nft_metadata(self):
        if self.nft_contract_address and self.nft_token_id:
            api_url = f"https://api.opensea.io/api/v1/asset/{self.nft_contract_address}/{self.nft_token_id}/"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching NFT metadata: {e}")
        return None

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Abstract Art"
        verbose_name_plural = "Abstract Arts"

class FashionArt(models.Model):
    CATEGORY_CHOICES = [
        ('avant_garde', 'Avant-Garde & Experimental Fashion'),
        ('textile_fabric', 'Textile & Fabric Art'),
        ('digital_3d_printed', 'Digital & 3D-Printed Fashion'),
        ('accessories_jewelry', 'Accessories & Jewelry Design'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fashionarts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='fashionarts/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fashionarts_created')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='avant_garde')
    is_for_sale = models.BooleanField(default=False)
    flowers = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NFT Fields
    is_nft = models.BooleanField(default=False)
    nft_contract_address = models.CharField(max_length=255, blank=True, null=True)
    nft_token_id = models.CharField(max_length=255, blank=True, null=True)
    blockchain = models.CharField(
        max_length=100,
        choices=[('ethereum', 'Ethereum'), ('polygon', 'Polygon'), ('solana', 'Solana'), ('other', 'Other')],
        blank=True,
        null=True,
    )
    mint_date = models.DateTimeField(blank=True, null=True)
    nft_url = models.URLField(blank=True, null=True)
    nft_metadata = models.JSONField(blank=True, null=True, help_text="Metadata of the NFT")
    copyright_hash = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.mint_date:
            if isinstance(self.mint_date, str):
                self.mint_date = timezone.make_aware(timezone.datetime.fromisoformat(self.mint_date))
            elif timezone.is_naive(self.mint_date):
                self.mint_date = timezone.make_aware(self.mint_date)

        if self.is_nft and self.nft_contract_address and self.nft_token_id:
            self.nft_url = f"https://opensea.io/assets/{self.nft_contract_address}/{self.nft_token_id}"
            self.nft_metadata = self.fetch_nft_metadata()

        super().save(*args, **kwargs)

    def fetch_nft_metadata(self):
        if self.nft_contract_address and self.nft_token_id:
            api_url = f"https://api.opensea.io/api/v1/asset/{self.nft_contract_address}/{self.nft_token_id}/"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching NFT metadata: {e}")
        return None

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Fashion Art"
        verbose_name_plural = "Fashion Arts"


class VirtualInteractiveArt(models.Model):
    ART_TYPE_CHOICES = [
        ('vr_art', 'Virtual Reality (VR) Art'),
        ('ar_art', 'Augmented Reality (AR) Art'),
        ('projection_mapping', 'Projection Mapping & Light Installations'),
        ('ai_driven', 'AI-Driven Sound & Visuals'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='virtualinteractivearts')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='virtualinteractivearts/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='virtualinteractivearts_created')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    art_type = models.CharField(max_length=50, choices=ART_TYPE_CHOICES, default='vr_art')
    is_for_sale = models.BooleanField(default=False)
    flowers = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NFT Fields
    is_nft = models.BooleanField(default=False)
    nft_contract_address = models.CharField(max_length=255, blank=True, null=True)
    nft_token_id = models.CharField(max_length=255, blank=True, null=True)
    blockchain = models.CharField(
        max_length=100,
        choices=[('ethereum', 'Ethereum'), ('polygon', 'Polygon'), ('solana', 'Solana'), ('other', 'Other')],
        blank=True,
        null=True,
    )
    mint_date = models.DateTimeField(blank=True, null=True)
    nft_url = models.URLField(blank=True, null=True)
    nft_metadata = models.JSONField(blank=True, null=True, help_text="Metadata of the NFT")
    copyright_hash = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.mint_date:
            if isinstance(self.mint_date, str):
                self.mint_date = timezone.make_aware(timezone.datetime.fromisoformat(self.mint_date))
            elif timezone.is_naive(self.mint_date):
                self.mint_date = timezone.make_aware(self.mint_date)

        if self.is_nft and self.nft_contract_address and self.nft_token_id:
            self.nft_url = f"https://opensea.io/assets/{self.nft_contract_address}/{self.nft_token_id}"
            self.nft_metadata = self.fetch_nft_metadata()

        super().save(*args, **kwargs)

    def fetch_nft_metadata(self):
        if self.nft_contract_address and self.nft_token_id:
            api_url = f"https://api.opensea.io/api/v1/asset/{self.nft_contract_address}/{self.nft_token_id}/"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching NFT metadata: {e}")
        return None

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Virtual & Interactive Art"
        verbose_name_plural = "Virtual & Interactive Arts"

class DrawingArt(models.Model):
    ART_TYPE_CHOICES = [
        ('design_illustration', 'Design & Illustration'),
        ('editorial_book_illustration', 'Editorial & Book Illustration'),
        ('concept_art_character_design', 'Concept Art & Character Design'),
        ('typography_graphic_design', 'Typography & Graphic Design'),
        ('motion_design_animation', 'Motion Design & Animation'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='artworks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='artworks/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='artworks_created')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    art_type = models.CharField(max_length=50, choices=ART_TYPE_CHOICES, default='design_illustration')
    is_for_sale = models.BooleanField(default=False)
    flowers = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NFT Fields
    is_nft = models.BooleanField(default=False)
    nft_contract_address = models.CharField(max_length=255, blank=True, null=True)
    nft_token_id = models.CharField(max_length=255, blank=True, null=True)
    blockchain = models.CharField(
        max_length=100,
        choices=[('ethereum', 'Ethereum'), ('polygon', 'Polygon'), ('solana', 'Solana'), ('other', 'Other')],
        blank=True,
        null=True,
    )
    mint_date = models.DateTimeField(blank=True, null=True)
    nft_url = models.URLField(blank=True, null=True)
    nft_metadata = models.JSONField(blank=True, null=True, help_text="Metadata of the NFT")
    copyright_hash = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.mint_date:
            if isinstance(self.mint_date, str):
                self.mint_date = timezone.make_aware(timezone.datetime.fromisoformat(self.mint_date))
            elif timezone.is_naive(self.mint_date):
                self.mint_date = timezone.make_aware(self.mint_date)

        if self.is_nft and self.nft_contract_address and self.nft_token_id:
            self.nft_url = f"https://opensea.io/assets/{self.nft_contract_address}/{self.nft_token_id}"
            self.nft_metadata = self.fetch_nft_metadata()

        super().save(*args, **kwargs)

    def fetch_nft_metadata(self):
        if self.nft_contract_address and self.nft_token_id:
            api_url = f"https://api.opensea.io/api/v1/asset/{self.nft_contract_address}/{self.nft_token_id}/"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching NFT metadata: {e}")
        return None

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Drawing Artwork"
        verbose_name_plural = "Drawing Artworks"

class Gallery(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    wallet_address = models.CharField(max_length=255, null=True, blank=True)
    blockchain = models.CharField(max_length=100, choices=[
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('solana', 'Solana'),
        ('other', 'Other')
    ], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Artwork(models.Model):
    ART_TYPE_CHOICES = [
        ('fine_arts', 'Fine Arts'),
        ('photography_cinematics', 'Photography & Cinematics'),
        ('abstract_art', 'Abstract Art'),
        ('conceptual_mixed_media', 'Conceptual & Mixed Media'),
        ('fashion_wearable_art', 'Fashion & Wearable Art'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='artworks/')
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='artworks_created')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    art_type = models.CharField(max_length=50, choices=ART_TYPE_CHOICES, default='design_illustration')
    is_for_sale = models.BooleanField(default=False)
    flowers = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    blockchain = models.CharField(max_length=100, choices=[('ethereum', 'Ethereum'), ('polygon', 'Polygon'), ('solana', 'Solana'), ('other', 'Other')], blank=True, null=True)
    mint_date = models.DateTimeField(blank=True, null=True)
    nft_contract_address = models.CharField(max_length=255, blank=True, null=True)
    nft_token_id = models.CharField(max_length=255, blank=True, null=True)
    is_nft = models.BooleanField(default=False)
    nft_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True  # Makes this an abstract base class

    def __str__(self):
        return self.title

class SecureFile(models.Model):
    name = models.CharField(max_length=255)
    encrypted_content = models.BinaryField()  # Store encrypted data as binary

    def save(self, *args, **kwargs):
        if self.name:
            self.encrypted_content = encrypt_data(self.name)  # Encrypt before saving
        super().save(*args, **kwargs)

    def get_decrypted_content(self):
        """Decrypt the stored encrypted data"""
        return decrypt_data(self.encrypted_content)

class ArtworkGallery(models.Model):
    artwork = models.ForeignKey(FineArt, on_delete=models.CASCADE)
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    flowers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='flowered_artworks', blank=True)
    blockchain = models.CharField(max_length=100, choices=[
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('solana', 'Solana'),
        ('other', 'Other')
    ], blank=True, null=True)
    copyright_hash = models.CharField(max_length=255, null=True, blank=True)

    def total_flowers(self):
        return self.flowers.count()

    def __str__(self):
        return self.title

class CinematographyGallery(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    gallery = models.ForeignKey("Gallery", on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    blockchain = models.CharField(
        max_length=100,
        choices=[
            ("ethereum", "Ethereum"),
            ("polygon", "Polygon"),
            ("solana", "Solana"),
            ("other", "Other"),
        ],
        blank=True,
        null=True,
    )
    copyright_hash = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.cinematography.title} in {self.gallery.name}"

class Exhibition(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    blockchain = models.CharField(max_length=100, choices=[
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('solana', 'Solana'),
        ('other', 'Other')
    ], blank=True, null=True)
    copyright_hash = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Appreciations(models.Model):
    artwork = models.ForeignKey(ArtGallery, on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    blockchain = models.CharField(max_length=100, choices=[
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('solana', 'Solana'),
        ('other', 'Other')
    ], blank=True, null=True)
    transaction_hash = models.CharField(max_length=255, null=True, blank=True)

class Subscription(models.Model):
    subscriber = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    blockchain = models.CharField(max_length=100, choices=[
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('solana', 'Solana'),
        ('other', 'Other')
    ], blank=True, null=True)
    subscription_token_id = models.CharField(max_length=255, null=True, blank=True)


class FloweredArtwork(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='flowered_by_user'
    )
    related_artwork = models.ForeignKey(  # Renamed from 'artwork'
        ArtworkGallery,
        on_delete=models.CASCADE,
        related_name='related_flowered_set'
    )
    flowered_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

class FlowerGiver(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Dynamically points to the user model
    artwork = models.ForeignKey(ArtworkGallery, on_delete=models.CASCADE)
    has_given = models.BooleanField(default=False)  # Track if user has given a flower
    flowers_given = models.PositiveIntegerField(default=0)

    objects = models.Manager()

    def __str__(self):
        return f"{self.user} - {self.flowers_given} flowers"


class ArtCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ArtSubcategory(models.Model):
    category = models.ForeignKey(ArtCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class NFTTransaction(models.Model):
    artwork = models.ForeignKey(ArtworkGallery, on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bought_nfts')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sold_nfts')
    transaction_hash = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=50)
    blockchain = models.CharField(max_length=100, choices=[
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('solana', 'Solana'),
        ('other', 'Other')
    ], blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class ProfileManager(models.Manager):
    def active_profiles(self):
        return self.filter(is_active=True)

class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return self.name



class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)  # Name of the subscription plan
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price of the plan
    duration_days = models.IntegerField()  # Duration of the plan in days
    created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto timestamp for updates
    features = models.TextField(default='No features specified')  # Description of features
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)  # Stripe Price ID

    def __str__(self):
        return self.name





class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    def is_valid(self):
        """Check if subscription is still active"""
        return self.is_active and self.end_date and self.end_date > now()

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"


# Profile Model
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)  # Profile picture
    bio = models.TextField(blank=True, null=True)  # Bio
    post_count = models.PositiveIntegerField(default=0)  # Total number of posts
    total_flowers = models.PositiveIntegerField(default=0)  # Total flowers received
    is_major = models.BooleanField(default=False)  # Major artist flag
    is_active = models.BooleanField(default=True)
    objects = ProfileManager()

    def clean(self):
        self.total_flowers = self.total_flowers or 0
        self.is_major = self.total_flowers > 100

        """Validates the profile and automatically sets is_major based on total_flowers."""
        if self.total_flowers > 100:
            self.is_major = True
        else:
            self.is_major = False

        if self.total_flowers < 0:
            raise ValidationError("Total flowers cannot be negative.")

        super().clean()

    def save(self, *args, **kwargs):
        """Ensure the profile is validated before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class BlockchainWallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, unique=True)
    private_key = models.TextField()  # Encrypt before storing!
    created_at = models.DateTimeField(auto_now_add=True)
    encrypted_private_key = models.TextField()

    def __str__(self):
        return f"{self.user.username} - {self.address}"

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.address}"

class EthereumTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Track the sender
    to_address = models.CharField(max_length=255)  # Receiver's wallet address
    amount = models.DecimalField(max_digits=18, decimal_places=8)  # Amount sent
    txn_hash = models.CharField(max_length=255, unique=True)  # Blockchain transaction hash
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("confirmed", "Confirmed")], default="pending")
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when transaction was created

    def __str__(self):
        return f"Tx {self.txn_hash} - {self.amount} ETH"


class Painting(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='paintings/')
    premiere_end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    objects = models.Manager()


# Configure your OpenAI API key
openai.api_key = "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"

class PostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    caption = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    flowers = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    # Other fields...
    def __str__(self):
        return self.content[:50]

    objects = PostManager()

    def generate_caption(self):
        """Generate an AI-based caption using the post's content and title."""
        try:
            # Customize the prompt for better caption generation
            prompt = (
                f"You're an AI expert in generating captions for artistic expression. "
                f"Given the title: '{self.title}' and content: '{self.content}', "
                "write a creative and engaging caption suitable for a social media post."
            )

            # Use OpenAI's GPT model to generate the caption
            response = openai.Completion.create(
                engine="text-davinci-003",  # Or use 'gpt-4' if available
                prompt=prompt,
                max_tokens=50,  # Adjust token limit for brevity
                temperature=0.7  # Adjust for more creativity (0.7 is a good balance)
            )

            # Extract and set the generated caption
            self.caption = response.choices[0].text.strip()
            return self.caption

        except Exception as e:
            # Handle errors (fallback to a default caption if AI fails)
            self.caption = "Check out this amazing post!"
            print(f"AI Caption Generation Error: {e}")
            return self.caption


class FlowerGiverManager:
    def __init__(self, user):
        self.user = user



    def give_flower(self, artwork):
        """
        Gives a flower to an artwork from the current user.
        Prevents duplicate flower-giving if needed.
        """
        if not artwork:
            return {"success": False, "message": "Artwork does not exist."}

        # Prevent duplicate flowers (optional)
        existing_flower = Appreciation.objects.filter(user=self.user, artwork=artwork).first()
        if existing_flower:
            return {"success": False, "message": "You have already given a flower to this artwork."}

        # Create a new appreciation (flower)
        flower = Appreciation.objects.create(user=self.user, artwork=artwork)
        return {"success": True, "message": "Flower given successfully!", "flower_id": flower.id}


def give_flower_view(request, artwork_id):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "User must be logged in."}, status=403)

    try:
        artwork = Artwork.objects.get(id=artwork_id)
    except Artwork.DoesNotExist:
        return JsonResponse({"success": False, "message": "Artwork not found."}, status=404)

    flower_manager = FlowerGiverManager(request.user)
    result = flower_manager.give_flower(artwork)
    return JsonResponse(result)


@csrf_exempt
def signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            full_name = data.get("full_name", "").strip()

            if not full_name or " " not in full_name:
                return JsonResponse({"error": "Please enter your full name."}, status=400)

            first_name, last_name = full_name.split(" ", 1)  # Splitting full name into first & last name

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already taken!"}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already in use!"}, status=400)

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            return JsonResponse({"success": "Account created successfully!"})

        except Exception as e:
            return JsonResponse({"error": "Something went wrong!"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

class Like(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return self.message


class AestheticMoment(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)  # Video field
    caption = models.TextField()  # Caption for the video

    objects = models.Manager()

    def __str__(self):
        return f"{self.user.username}'s aesthetic moment: {self.caption[:20]}"  # Show first 20 chars of caption



class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    BLOCKCHAIN_CHOICES = [
        ('ethereum', 'Ethereum'),
        ('polygon', 'Polygon'),
        ('solana', 'Solana'),
        ('bitcoin', 'Bitcoin'),
    ]
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    is_artist = models.BooleanField(default=False)  # Flag to indicate if the user is an artist
    total_flowers = models.PositiveIntegerField(default=0)  # Flowers received (likes)
    is_major = models.BooleanField(default=False)  # Flag for major artists
    # Other fields
    wallet_address = models.CharField(max_length=255, blank=True, null=True,
    help_text="User's blockchain wallet address")
    blockchain_type = models.CharField(
        max_length=50,
        choices=BLOCKCHAIN_CHOICES,
        blank=True,
        null=True,
        help_text="Type of blockchain the user is associated with"
    )
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",  # Unique related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",  # Unique related_name
        blank=True,
    )

    SUBSCRIPTION_CHOICES = [
        ('free', "Free"),
        ('basic', 'Basic'),
        ('premium', 'Premium')
    ]
    subscription_plan = models.CharField(max_length=10, choices=SUBSCRIPTION_CHOICES, default='free')
    subscription_start_date = models.DateTimeField(null= True, blank=True)
    subscription_end_date = models.DateTimeField(null= True, blank=True)

    objects = CustomUserManager()

    def is_active_subscription(self):
        if self.subscription_end_date:
            return self.subscription_end_date
        return False



class Meta:
    def __init__(self):
        pass

    constraints = []