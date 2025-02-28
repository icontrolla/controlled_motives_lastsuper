from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views
from django.contrib import admin
from .views import ArtistLoginView, stripe_webhook
from allauth.socialaccount import urls as social_urls

app_name = 'profiles'

urlpatterns = [
    # Default route to the loading page
    path('', views.loading_view, name='loading'),
    path('home/', views.home, name='home'),
    path('artists/', views.artist_page, name='artist'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('about/', views.about_page, name='about'),
    # Authentication routes
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('login/', views.login_view, name='login'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('artist_signup/', views.artist_signup, name='artist_signup'),
    path('artist_login/', ArtistLoginView.as_view(), name='artist_login'),

    # Profile-related routes
    path('profiles/<int:user_id>/', views.profile_view, name='profiles'),
    path('my-profile/', views.profile, name='my_profile'),
    path('artist-profile/<int:artist_id>/', views.artist_profile, name='artist_profile'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),

    # Post-related routes
    path('create/', views.create_post, name='create_post'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('api/artworks/', views.artwork_list, name="artwork-list"),
    # Artwork and Store
    path('thrift/', views.thrift_item_detail, name='thrift_store'),
    path('thrift/item/<int:item_id>/', views.thrift_item_detail, name='thrift_item_detail'),
    path('artwork/<int:artwork_id>/', views.artwork_detail, name='artwork_detail'),
    path('buy_artwork/<int:artwork_id>/', views.buy_artwork, name='buy_artwork'),
    path('process-payment/<int:artwork_id>/<int:price>/', views.process_payment, name='process_payment'),

    # Notifications and search
    path('notifications/', views.notification_page, name='notifications'),
    path('search/', views.search, name='search'),
    path('artist_dashboard/', views.artist_dashboard, name='artist_dashboard'),
    path("transactions/", views.transaction_history, name="transaction_history"),
    path("send-eth/", views.send_eth_view, name="send_eth"),

    path('wallet/', views.wallet_page, name='wallet_page'),

    path('save_wallet/', views.save_wallet, name='save_wallet'),
    # Gallery and Moments
    path('moment/<int:moment_id>/', views.moment_detail, name='moment_detail'),
    path('gallery/', views.gallery, name='gallery'),
    path('painting/<int:painting_id>/', views.painting_detail, name='painting_detail'),
    path('drawing/<int:drawing_id>/', views.drawing_detail, name='drawing_detail'),

    # Flowers and Feedback
    path('toggle-flower/<int:artwork_id>/', views.toggle_flower, name='toggle_flower'),
    path('api/give-flower/', views.toggle_flower, name='give_flower'),
    path('feedback/add/', views.add_feedback, name='add_feedback'),

    # Subscriptions and Payments
    path('checkout/<int:plan_id>/', views.create_checkout_session, name='checkout'),
    path('subscribe/success/', views.subscribe_success, name='subscribe_success'),
    path('subscriptions/', views.subscription_view, name='subscriptions'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('webhook/stripe', stripe_webhook, name='stripe-webhook'),
    path('create-stripe-product/', views.create_stripe_product, name='create_stripe_product'),

    path('create-ethereum-wallet/', views.create_ethereum_wallet, name='create_ethereum_wallet'),
    path('fine-arts/', views.fine_art_list, name='fine_art_list'),
    path('fine-arts/<int:art_id>/', views.fine_art_detail, name='fine_art_detail'),

path("encrypt/", views.encrypt_view, name="encrypt"),
    path("decrypt/<int:file_id>/", views.decrypt_view, name="decrypt"),
]

# Include AllAuth social authentication URLs
urlpatterns += social_urls.urlpatterns

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
