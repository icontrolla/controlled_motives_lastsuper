from rest_framework import serializers
from .models import ArtGallery  # Import your model

class ArtGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtGallery
        fields = '__all__'
