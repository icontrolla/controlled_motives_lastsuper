from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Post, Profile,
    AestheticMoment, ArtGallery, Painting,
    ThriftStoreItem, AbstractArtwork, DrawingArtwork,
     UserSubscription, ArtCategory, ArtSubcategory, FineArt,
    ConceptualMixedMedia, AbstractArt, FashionArt, VirtualInteractiveArt,
    CinematographyGallery, Artist

)
from .utils import calculate_feedback_metrics
from .models import Feedback
from django.utils.html import format_html
from .utils import generate_artistic_caption
from .models import SubscriptionPlan
from .models import CustomUser
from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import  Gallery, ArtworkGallery, Exhibition, Appreciations, Subscription, NFTTransaction


admin.site.register(Gallery)
admin.site.register(ArtworkGallery)
admin.site.register(Exhibition)
admin.site.register(Appreciations)
admin.site.register(Subscription)
admin.site.register(NFTTransaction)
admin.site.register(AestheticMoment)
admin.site.register(ArtGallery)
admin.site.register(Painting)
admin.site.register(ThriftStoreItem)
admin.site.register(AbstractArtwork)
admin.site.register(DrawingArtwork)
admin.site.register(Artist)



@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'created_at', 'updated_at']

    def get_start_date(self, obj):
        return obj.start_date

    get_start_date.short_description = 'Start Date'



@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'is_active']
    list_filter = ['plan', 'start_date', 'end_date']

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_artist', 'is_staff', 'is_major')
    list_filter = ('is_artist', 'is_staff', 'is_major')
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Artist Info', {'fields': ('bio', 'profile_picture', 'is_artist', 'is_major', 'wallet_address', 'blockchain_type')}),
    )

# ArtistProfile Admin
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'is_featured', 'is_major', 'is_trending')
    search_fields = ('user__username', 'user__email')
    list_editable = ('is_featured', 'is_major', 'is_trending')





@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'comment', 'created_at', 'is_helpful', 'is_visible', 'source', 'is_flagged')
    search_fields = ('user__username', 'comment')
    list_filter = ('rating', 'created_at', 'is_visible', 'source', 'is_flagged')
    actions = ['mark_as_helpful', 'flag_as_inappropriate', 'unflag_feedback']

    @staticmethod
    def get_feedback_stats():
        feedback_metrics = calculate_feedback_metrics()
        return format_html(
            '<p>Total Feedback: {}</p><p>Helpful Feedback: {}</p><p>Helpful Percentage: {}%</p>',
            feedback_metrics['total_feedback'],
            feedback_metrics['helpful_feedback'],
            feedback_metrics['helpful_percentage']
        )

    # Adding feedback stats as an admin action or widget
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['feedback_stats'] = self.get_feedback_stats()
        return super().changelist_view(request, extra_context=extra_context)

    @staticmethod
    def process_feedback():
        feedback_metrics = calculate_feedback_metrics()
        if feedback_metrics['helpful_percentage'] > 80:
            # Do something if the feedback is overwhelmingly positive
            print("Great feedback! Keep up the good work!")
        else:
            # Do something else if feedback is lower
            print("Consider improving the content or responses.")

# Registering the Feedback model with the custom admin



class ArtSubcategoryInline(admin.TabularInline):
    model = ArtSubcategory
    extra = 1

class ArtCategoryAdmin(admin.ModelAdmin):
    inlines = [ArtSubcategoryInline]

admin.site.register(ArtCategory, ArtCategoryAdmin)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('caption', 'user','created_at', 'title')
    list_filter = ('created_at', 'caption')  # Optional filters
    search_fields = ('content', 'created_at')


@admin.register(FineArt)
class FineArtAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'style', 'is_for_sale', 'price', 'is_featured', 'is_trending')
    search_fields = ('title', 'artist__username', 'style')
    list_filter = ('is_for_sale', 'is_featured', 'is_trending', 'style')

@admin.register(AbstractArt)
class AbstractArtAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'style', 'is_for_sale', 'price', 'is_featured', 'is_trending')
    search_fields = ('title', 'artist__username', 'style')
    list_filter = ('is_for_sale', 'is_featured', 'is_trending', 'style')

    def is_trending_display(self, obj):
        return bool(obj.is_trending)

    is_trending_display.boolean = True  # Ensure Django treats it as boolean

    def is_nft_display(self, obj):
        return bool(obj.is_nft)

    is_nft_display.boolean = True



@admin.register(FashionArt)
class FashionArtAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'category', 'is_for_sale', 'price', 'is_featured', 'is_trending')
    search_fields = ('title', 'artist__username', 'category')
    list_filter = ('is_for_sale', 'is_featured', 'is_trending', 'category')


class DrawingArtAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'art_type', 'is_for_sale', 'price', 'is_featured', 'is_trending')
    search_fields = ('title', 'artist__username', 'art_type')
    list_filter = ('is_for_sale', 'is_featured', 'is_trending', 'art_type')

@admin.register(VirtualInteractiveArt)
class VirtualInteractiveArtAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'art_type', 'is_for_sale', 'price', 'is_featured', 'is_trending')
    search_fields = ('title', 'artist__username', 'art_type')
    list_filter = ('is_for_sale', 'is_featured', 'is_trending', 'art_type')


@admin.register(ConceptualMixedMedia)
class ConceptualMixedMediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'style', 'is_for_sale', 'price', 'is_featured', 'is_trending')
    search_fields = ('title', 'artist__username', 'style')
    list_filter = ('is_for_sale', 'is_featured', 'is_trending', 'style')

@admin.register(CinematographyGallery)
class CinematographyGalleryAdmin(admin.ModelAdmin):
    list_display = ("title", "gallery", "added_at", "blockchain")  # Columns to display in the admin list view
    search_fields = ("title", "gallery__name")  # Enables search functionality
    list_filter = ("blockchain", "added_at")