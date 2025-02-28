import json
from datetime import datetime, timedelta, timezone
import stripe
from django.utils.timesince import timesince
from web3 import Web3
from web3 import Account
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
from .models import BlockchainWallet, ArtworkGallery
import base64
from cryptography.fernet import Fernet
from .services import send_eth_transaction
from .models import Feedback, CinematographyGallery
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from djstripe.models import Event
from djstripe.models import Price
from dotenv import load_dotenv
from djstripe.models import Product
from .forms import ArtistLoginForm, EditUserForm
from .forms import ArtistSignupForm
from .forms import PostForm
from .forms import ProfileForm
from .models import Artwork
from .forms import ArtworkForm
from .models import Flower, FlowerGiver
from .models import Like
from .models import Notification
from .models import Post, Moment
from .models import Profile
from django.contrib.auth.views import LoginView
from .models import SubscriptionPlan, UserSubscription
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
CustomUser = get_user_model()
from eth_account import Account
from django.http import JsonResponse

from .models import (
    Artist,
    AestheticMoment,
    ArtGallery,
    Painting,
    AbstractArtwork,
    DrawingArtwork,
    ArtCategory,
    FineArt,
    BlockchainWallet,
AbstractArt, ConceptualMixedMedia, FashionArt, VirtualInteractiveArt,
EthereumTransaction
)



stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY
Account.enable_unaudited_hdwallet_features()


load_dotenv()


SECRET_KEY_FERNET = os.getenv("SECRET_KEY_FERNET")
if not SECRET_KEY_FERNET:
    SECRET_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode()
    print(f"Generated SECRET_KEY: {SECRET_KEY}")  # Debugging

cipher = Fernet(SECRET_KEY_FERNET.encode())

@login_required
def create_ethereum_wallet(request):
    """Create a new Ethereum wallet for a user if they don’t have one"""
    user = request.user

    if not user.id:
        return render(request, 'create-wallet.html', {'message': 'User does not exist in the database.'})

    # Check if the user already has a wallet
    existing_wallet = BlockchainWallet.objects.filter(user=user).first()
    if existing_wallet:
        return render(request, "create-wallet.html", {
            "message": "You already have a wallet!",
            "wallet": {"address": existing_wallet.address}
        })

    # Generate a new Ethereum wallet
    account = Account.create()
    private_key = account.key.hex()  # Private key (must be encrypted)
    public_address = account.address  # Public Ethereum address

    # Encrypt the private key before storing
    encrypted_private_key = cipher.encrypt(private_key.encode()).decode()

    # Save wallet details to the database
    wallet = BlockchainWallet.objects.create(
        user=user,
        address=public_address,
        encrypted_private_key=encrypted_private_key  # Store encrypted key
    )

    print(f"Wallet created for {user.username}: {wallet.address}")

    return render(request, "home.html", {
        "message": "Wallet created successfully!",
        "wallet": {"address": wallet.address}
    })

@login_required
def wallet_page(request):
    user = request.user
    wallet = BlockchainWallet.objects.filter(user=user).first()
    return render(request, "create_wallet.html", {
        "wallet": wallet
    })

def subscription_view(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, "subscriptions.html", {"plans": plans})

def subscribe(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    if request.method == "POST":
        # Create or update user subscription
        subscription, created_at = UserSubscription.objects.get_or_create(user=request.user)
        subscription.plan = plan
        subscription.start_date = now()
        subscription.end_date = now() + timedelta(days=plan.duration_days)
        subscription.is_active = True
        subscription.save()
        return render(request, 'subscribe_success.html', {'plan': plan})

    return render(request, "subscriptions.html", {"plan": plan})

@login_required
def cancel_subscription(request):
    subscription = UserSubscription.objects.filter(user=request.user, is_active=True).first()
    if subscription:
        subscription.is_active = False
        subscription.end_date = now()
        subscription.save()
        messages.success(request, "Subscription canceled successfully!")
    else:
        messages.error(request, "No active subscription found.")
    return redirect("subscription_status")

def subscription_required(plan):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Login required")
            if request.user.subscription_plan != plan or not request.user.is_active_subscription():
                return HttpResponseForbidden("Subscription required")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY

@csrf_exempt  # Only needed if using POST/PUT without CSRF token
def artwork_list(request):
    if request.method == "GET":
        artworks = Artwork.objects.values()  # Convert queryset to list
        return JsonResponse({"artworks": artworks}, safe=False)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

@subscription_required('premium')
def premium_content(request):
    return render(request, 'premium_content.html')

def add_notification(user, message):
    Notification.objects.create(user=user, message=message)


@login_required
def notification_page(request):
    # Fetch notifications for the logged-in user
    notifications = Notification.objects.filter(recipient=request.user)

    # Mark all notifications as read when the user visits the page
    notifications.update(is_read=True)

    return render(request, 'notifications.html', {'notifications': notifications})


def artist_page(request):
    # Fetch all artists, prefetching for efficiency if extended later
    artists = Artist.objects.all()

    context = {
        'artists': artists,
        'page_title': 'Meet Our Artists',  # Dynamic title for template
    }
    return render(request, 'artist.html', context)

def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.DJSTRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        Event.process(event)  # Process the event without assignment
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    return HttpResponse(status=200)


@login_required
def subscribe_success(request):
    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('/subscribe/cancel/')

    # Retrieve the session from Stripe
    session = stripe.checkout.Session.retrieve(session_id)

    # Ensure user subscription exists
    subscription = UserSubscription.objects.filter(stripe_checkout_session_id=session_id, user=request.user).first()
    if not subscription:
        return redirect('/subscribe/cancel/')

    # Get the plan and activate subscription
    plan = subscription.plan
    subscription.is_active = True
    subscription.start_date = now()
    subscription.end_date = now() + timedelta(days=plan.duration_days)
    subscription.stripe_subscription_id = session_id  # Store Stripe session ID
    subscription.save()

    return render(request, 'subscribe_success.html', {"plan": plan})

    for artwork in Artwork.objects.all():
        time_diff = datetime.now(timezone.utc) - artwork.created_at

    if time_diff.total_seconds() < 60:
        artwork.time_ago = "Just now"
    else:
        artwork.time_ago = timesince(artwork.created_at) + " ago"

def process_payment(request, artwork_id, price):
    try:
        # Handle payment form submission
        if request.method == 'POST':
            # Get token from Stripe checkout or other payment method
            token = request.POST.get('stripeToken')
            if not token:
                messages.error(request, "Payment token is missing. Please try again.")
                return redirect(reverse('buy_artwork', kwargs={'artwork_id': artwork_id}))

            # Validate price to prevent manipulation
            artwork = Artwork.objects.get(id=artwork_id)
            if artwork.price != price or not artwork.is_available:
                messages.error(request, "Invalid price or the artwork is no longer available.")
                return redirect('artwork_list')

            # Create a payment intent with Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(price * 100),  # Convert price to cents
                currency='usd',
                payment_method_data={
                    'type': 'card',
                    'card': {'token': token},
                },
                confirm=True,
            )

            # Check if the payment is successful
            if intent.status == 'succeeded':
                # Update the artwork's status to mark it as sold
                artwork.is_available = False
                artwork.save()

                # Optionally, store the transaction info, send email, etc.

                messages.success(request, "Payment successful! Thank you for your purchase.")
                return redirect('thank_you')  # Redirect to a thank you page

            else:
                messages.error(request, "Payment failed. Please try again.")
                return redirect(reverse('buy_artwork', kwargs={'artwork_id': artwork_id}))

        else:
            # Render the payment page for GET requests
            return render(request, 'process_payment.html', {'artwork_id': artwork_id, 'price': price})

    except stripe.error.CardError as e :
        # Handle card errors (e.g., declined, insufficient funds, etc.)
        messages.error(request, f"Card error: {e.user_message}")
        return redirect(reverse('buy_artwork', kwargs={'artwork_id': artwork_id}))

    except stripe.error.StripeError :
        # Handle general Stripe errors
        messages.error(request, "Payment processing error. Please try again later.")
        return redirect(reverse('buy_artwork', kwargs={'artwork_id': artwork_id}))

    except Exception as e:
        # Handle any other unforeseen exceptions
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect(reverse('buy_artwork', kwargs={'artwork_id': artwork_id}))


@login_required
def create_checkout_session(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    # Create a new Stripe Checkout Session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        success_url=request.build_absolute_uri('/subscribe/success/') + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri('/subscribe/cancel/'),
        customer_email=request.user.email,
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': plan.name,
                },
                'unit_amount': int(plan.price * 100),  # Convert dollars to cents
            },
            'quantity': 1,
        }],
    )

    # Save session ID to track payment
    subscription, _ = UserSubscription.objects.get_or_create(user=request.user)
    subscription.stripe_checkout_session_id = checkout_session.id
    subscription.save()

    return redirect(checkout_session.url)

class UserProfileView(View):
    @staticmethod
    def get(request, user_id):
        user = get_object_or_404(User, id=user_id)
        return render(request, 'profiles/profile.html', {'user': user})

# Art Gallery Detail View
def gallery_detail(request, gallery_id):
    gallery = get_object_or_404(ArtGallery, id=gallery_id)
    return render(request, 'profiles/gallery_detail.html', {'gallery': gallery})


# Painting Detail View
def painting_detail(request):
    paintings = Painting.objects.all()
    user_subscriptions = UserSubscription.objects.filter(user=request.user, active=True)
    user_subscription_ids = user_subscriptions.values_list('painting_id', flat=True)

    paintings_with_flags = []
    for painting in paintings:
        is_premiere_over = painting.premiere_end_date and painting.premiere_end_date < now()
        is_subscribed = painting.id in user_subscription_ids
        paintings_with_flags.append({
            'painting': painting,
            'is_premiere_over': is_premiere_over,
            'is_subscribed': is_subscribed,
        })

    context = {'paintings_with_flags': paintings_with_flags}
    return render(request, 'profiles/paintings.html', context)
    
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('profiles:home')  # Redirect to a success page
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# Thrift Store Item Detail View
def thrift_item_detail(request, item_id):
    item = get_object_or_404(ThriftStoreItem, id=item_id)
    return render(request,  'thrift_item_detail.html', {'item': item} )


# Abstract Artwork Detail View
def artwork_detail(request, artwork_id):
    artwork = get_object_or_404(AbstractArtwork, id=artwork_id)
    return render(request, 'profiles/artwork_detail.html', {'artwork': artwork})


# Drawing Artwork Detail View
def drawing_detail(request, drawing_id):
    drawing = get_object_or_404(DrawingArtwork, id=drawing_id)
    return render(request, 'profiles/drawing_detail.html', {'drawing': drawing})


def artist_signup(request):
    if request.method == 'POST':
        a_form = ArtistSignupForm(request.POST, request.FILES)
        if a_form.is_valid():
            try:
                user = a_form.save()
                user.save()
                # Set user properties
                user.is_artist = True  # Mark as an artist
                user.is_staff = True  # Grant staff access if needed


                # Add the user to the "Artists" group (optional)
                artists_group, created = Group.objects.get_or_create(name='Artists')
                user.groups.add(artists_group)

                # Create the artist profile
                ArtistProfile.objects.create(
                    user=user,
                    bio=a_form.cleaned_data.get('bio'),
                    profile_picture=a_form.cleaned_data.get('profile_picture'),
                    category = a_form.cleaned_data.get('category'),
                    is_major = a_form.cleaned_data.get('is_major', False),
                    is_trending = a_form.cleaned_data.get('is_trending', False),
                )

                login(request, user)  # Log in the user after signup
                return redirect('profiles:login')
            except IntegrityError:
                a_form.add_error('username', "An account with this username already exists.")
            
    else:
        a_form = ArtistSignupForm()
    return render(request, 'artist_signup.html', {'a_form': a_form})

@login_required
def wallet_page(request):
    user = request.user
    wallet_data = {}  # Fetch user's wallet data from DB or blockchain
    return render(request, 'wallet.html', {'wallet_data': wallet_data})

@csrf_exempt  # For development only; use CSRF protection in production
@login_required
def save_wallet(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        wallet_address = data.get('wallet_address')

        if wallet_address:
            # Save wallet address to user's profile
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.address = wallet_address
            wallet.save()
            return JsonResponse({'message': 'Wallet saved successfully!', 'address': wallet_address})

    return JsonResponse({'error': 'Invalid request'}, status=400)


class ArtistLoginView(LoginView):
    template_name = 'profiles/artist_login.html'
    form_class = ArtistLoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('artist_dashboard')  # Replace with your artist dashboard URL

@login_required
def artist_dashboard(request):
    # Fetch featured artists
    featured_artists = User.objects.filter(is_featured=True)

    return render(request, 'artist_dashboard.html', {
        'featured_artists': featured_artists,
    })

def about_page(request):
    context = {
        'page_title': 'About Controlled Motives',  # Customize as needed
    }
    return render(request, 'about.html', context)



def home(request):
    # Fetch featured artists
    featured_artists = Artist.objects.filter(is_featured=True).order_by('-created_at')[:5]

    # Fetch major artists
    major_artists = Artist.objects.filter(is_major=True).order_by('-created_at')[:5]

    # Fetch trending artworks
    artworks = ArtGallery.objects.all()  # Querying all artworks, not instantiating an object
    trending_artworks = sorted(
        artworks,
        key=lambda artwork: (
                    artwork.flowers / ((timezone.now() - artwork.created_at).days + 1)) if artwork.created_at else 0,
        reverse=True
    )[:10]  # Get top 10 trending artworks

    # Fetch recent posts
    recent_posts = Post.objects.all().order_by('-created_at')[:8]

    # Fetch aesthetic moments
    aesthetic_moments = Moment.objects.order_by('-created_at')
    thrift_store_items = ThriftStoreItem.objects.all()

    # Combine all data into a single context dictionary
    context = {
        'featured_artists': featured_artists,
        'major_artists': major_artists,
        'trending_artworks': trending_artworks,
        'recent_posts': recent_posts,
        'aesthetic_moments': aesthetic_moments,
        'art_galleries': ArtGallery.objects.all(),
        'paintings': Painting.objects.all(),
        'thrift_store_items': ThriftStoreItem.objects.all(),
        'abstract_artworks': AbstractArtwork.objects.all(),
        'drawing_artworks': DrawingArtwork.objects.all(),
    }

    return render(request, 'home.html', {'artworks': artworks})


def gallery_view(request):
    fine_arts = FineArt.objects.all()
    cinematography = CinematographyGallery.objects.all()
    abstract_art = AbstractArt.objects.all()
    conceptual_art = ConceptualMixedMedia.objects.all()
    fashion_art = FashionArt.objects.all()
    virtual_reality_art = VirtualInteractiveArt.objects.all()
    thrift_store_items = ThriftStoreItem.objects.all()


    context = {
        "fine_arts": fine_arts,
        "cinematography": cinematography,
        "abstract_art": abstract_art,
        "conceptual_art": conceptual_art,
        "fashion_art": fashion_art,
        "virtual_reality_art": virtual_reality_art,
        'drawing_artworks': DrawingArtwork,
        'thrift_store_items': thrift_store_items
    }

    return render(request, "gallery.html", context)

def moment_detail(request, moment_id):
    # Fetch the specific AestheticMoment object or return a 404 if not found
    moment = get_object_or_404(AestheticMoment, id=moment_id)
    return render(request, 'profiles/moment_detail.html', {'moment': moment})


def trending_artworks_view(request):
    trending_artworks = Artwork.objects.filter(trending=True)
       
    return render(request, 'trending_artworks.html', {'trending_artworks': trending_artworks})

def subscription_plans(request):
    products = Product.objects.filter(active=True).prefetch_related("prices")
    return render(request, "subscriptions.html", {"products": products})



@login_required
def buy_artwork(request, artwork_id):
    try:
        # Retrieve the artwork or return a 404 error if it doesn't exist
        artwork = get_object_or_404(Artwork, id=artwork_id)

        # Check if the artwork is available for purchase
        if not artwork.is_available:
            messages.error(request, "This artwork is no longer available.")
            return redirect('process_payment')  # Adjust the redirection URL if needed

        # Ensure the artwork has a valid price
        if artwork.price is None or not isinstance(artwork.price, (int, float)):
            messages.error(request, "This artwork does not have a valid price.")
            return redirect('home')  # Redirect to a safe page (e.g., the home page)

        # Convert the price to an integer (if it's a float)
        price = int(artwork.price)

        # Redirect to the payment processing page with proper arguments
        return redirect('process-payment', artwork_id=artwork.id, price=price)

    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('home.html')  # Redirect to a fallback page (e.g., the home page)


@login_required
def create_post(request):
    if request.method == 'POST':
        file_type = 'video' if 'video' in request.FILES else 'image' if 'image' in request.FILES else None

        if file_type:
            c_form = PostForm(request.POST, request.FILES)
            if c_form.is_valid():
                post = c_form.save(commit=False)
                post.user = request.user

                if file_type == 'video':
                    post.video = request.FILES['video']
                    post.caption = request.POST.get('title', 'Untitled Video')
                    post.content = request.POST.get('description', 'No description provided.')

                elif file_type == 'image':
                    post.image = request.FILES['image']
                    post.caption = request.POST.get('title', 'Untitled Image')
                    if request.POST.get('auto_generate_caption'):
                        post.generate_caption()  # AI-generated caption logic
                    else:
                        post.content = request.POST.get('caption', 'No caption provided.')

                post.save()
                messages.success(request, f"Your {file_type} has been successfully uploaded!")
                return redirect('profiles:profile', user_id=request.user.id)

        messages.error(request, "Please select a valid file for upload.")

    # Default form (GET request)
    c_form = PostForm()
    return render(request, 'create_post.html', {'c_form': c_form})


# Correct redirect

@login_required
def delete_post(request, post_id):
    if request.method == 'POST':
        # Use filter instead of get to retrieve and delete posts if needed
        post = Post.objects.filter(id=post_id).first()
        if post:
            post.delete()
            return HttpResponseRedirect(reverse('profile'))
        else:
            return HttpResponseRedirect(reverse('profile'))

def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)
    notifications.update(is_read=True)  # Mark all as read
    return render(request, 'notifications.html', {'notifications': notifications})

def search_users(request):
    query = request.GET.get('query', '')  # Get the search query from the GET request
    users = User.objects.filter(username__icontains=query) if query else []
    return render(request, 'search_results.html', {'query': query, 'users': users})

def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        # Check if the user already liked the post
        if Like.objects.filter(user=user, post=post).exists():
            return JsonResponse({'error': 'You already liked this post.'}, status=400)

        # Add the like
        Like.objects.create(user=user, post=post)

        # Create a notification
        if user != post.user:  # Don't notify the post owner if they liked their own post
            Notification.objects.create(
                recipient=post.user,
                sender=user,
                post=post,
                message=f'{user.username} liked your post.'
            )

        # Return the updated like count
        return JsonResponse({'likes_count': post.likes.count()})
    return JsonResponse({'error': 'Invalid request.'}, status=400)

def gallery(request):
    categories = ArtCategory.objects.prefetch_related("subcategories").all()
    return render(request, "gallery.html", {"categories": categories})

def fine_art_list(request):
    fine_arts = FineArt.objects.all()  # You can filter this as needed
    return render(request, 'fine_arts/list.html', {'fine_arts': fine_arts})

def fine_art_detail(request, art_id):
    fine_art = FineArt.objects.get(id=art_id)
    return render(request, 'gallery.html', {'fine_art': fine_art})





@login_required
def send_eth_view(request):
    if request.method == "POST":
        user = request.user
        to_address = request.POST.get("to_address")
        amount = float(request.POST.get("amount", 0.01))

        txn_hash = send_eth_transaction(to_address, amount)  # Function to interact with blockchain

        if txn_hash:
            transaction = EthereumTransaction.objects.create(
                user=user,
                to_address=to_address,
                amount=amount,
                txn_hash=txn_hash,
                status="pending"
            )
            return JsonResponse({"message": "Transaction stored!", "txn_hash": txn_hash})
        else:
            return JsonResponse({"error": "Transaction failed"}, status=400)

    return render(request, "send_eth.html")

@login_required
def transaction_history(request):
    transactions = EthereumTransaction.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "transactions.html", {"transactions": transactions})


def cinematic(request):
    cinematics = CinematographyGallery.objects.all()  # You can filter this as needed
    return render(request, 'gallery.html', {'cinematics': cinematics})

def cinematics(request, art_id):
    cinematics = CinematographyGallery.objects.get(id=art_id)  # You can filter this as needed
    return render(request, 'gallery.html', {'cinematics': cinematics})

def flower_list(request):
    artworks = ArtworkGallery.objects.all()
    return render(request, 'flower_list.html', {'artworks': artworks})

def encrypt_view(request):
    """Example API endpoint to encrypt and store data."""
    if request.method == "POST":
        data = request.POST.get("data")  # Get input data
        encrypted_data = encrypt_data(data)

        secure_file = SecureFile(name=data, encrypted_content=encrypted_data)
        secure_file.save()

        return JsonResponse({"message": "Data encrypted and saved!", "encrypted": str(encrypted_data)})

def decrypt_view(request, file_id):
    """Example API endpoint to decrypt stored data."""
    try:
        secure_file = SecureFile.objects.get(id=file_id)
        decrypted_data = secure_file.get_decrypted_content()
        return JsonResponse({"decrypted": decrypted_data})
    except SecureFile.DoesNotExist:
        return JsonResponse({"error": "File not found"}, status=404)

@login_required
def toggle_flower(request, artwork_id):
    artwork = get_object_or_404(Artwork, id=artwork_id)

    if request.user in artwork.flowers.all():
        artwork.flowers.remove(request.user)
        flowered = False
    else:
        artwork.flowers.add(request.user)
        flowered = True

    return JsonResponse({'flowered': flowered, 'total_flowers': artwork.total_flowers()})

def search(request):
    query = request.GET.get('q', '').strip()
    if query:
        # Search the database for matching entries
        results = Artwork.objects.filter(title__icontains=query)  # Adjust the field as needed
        data = [{"id": artwork.id, "title": artwork.title, "flowers": artwork.flowers} for artwork in results]
        return JsonResponse({"results": data})
    return JsonResponse({"results": []})


def profile(request):
    user = get_object_or_404(CustomUser, id=user_profile)
    artist = Artist.objects.get(user=user_profile)
    # Use artist_id to fetch data
    context = {
        "user": user
    }
    return render(request, 'profiles:profile.html', context)





def add_feedback(request):
    if request.method == "POST":
        # Handle the form submission (process feedback)
        messages.success(request, "Thank you for your feedback!")  # Flash message
        return redirect("profiles:home")  # Redirect to homepage
    return render(request, "add_feedback.html")


# Profile view: Display and update user profile
@login_required
def my_profile_view(request):
    try:
        artist, created = Artist.objects.get_or_create(user=request.user)
    except Artist.DoesNotExist:
        # Create a default Artist for the user
        artist = Artist.objects.create(
            user=request.user,

        )
    return redirect('profiles:artist_profile', user_id=request.user_id)

def artist_profile(request, artist_id):
    artist = get_object_or_404(User, id=artist_id)  # Replace `Artist` with the actual model
    return render(request, 'profile.html', {'artist': artist})




# Edit profile view: Allow user to edit their profile and user data

@login_required
def edit_profile_view(request):
    context = {}
    user = request.user  # Get the current logged-in user
    e_profile = getattr(user, 'profile', None)  # Safely fetch the profile or None

    if e_profile is None:
        # If the profile doesn't exist, create one
        e_profile = Profile.objects.create(user=user)

    if request.method == 'POST':
        # Handle form submission and save the changes to the profile
        d_form = ProfileForm(request.POST, request.FILES, instance=e_profile)  # Include request.FILES for file uploads
        u_form = EditUserForm(request.POST, request.FILES, instance=e_profile)
        if d_form.is_valid() and u_form.is_valid():
            d_form.save()
            u_form.save()
            return redirect('profiles:profile', user_id=user.id)  # Redirect to the profile view

    else:
        d_form = ProfileForm(instance=e_profile)  # Prepopulate the form with the existing profile data
        u_form = EditUserForm(instance=request.user.profile)

        context = {
            'd_form': d_form,
            'u_form': u_form
        }
    # Render the edit profile page with the form
    return render(request, 'edit_profile.html', context)


class CustomLoginView(LoginView):
    template_name = 'login.html'

# Login view
    # A simple profile page view (alternative to profile_view)

def loading_view(request):
    context = {
        'username': request.user.username if request.user.is_authenticated else "Guest",
    }
    return render(request, 'loading.html', context)

from .models import ThriftStoreItem  # Assuming you have a model for thrift store items




@login_required
def user_profile(request):
    user = request.user  # Get the logged-in user
    return render(request, 'profile.html', {'profile': user})

def update_profile(request):
    current_user = request.user

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=current_user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile page
    else:
        form = ProfileForm(instance=current_user)

    context = {
        'form': form,
        'user': current_user,  # This is now fine
    }
    return render(request, 'update_profile.html', context)



stripe.api_key = "your_stripe_secret_key"

def create_stripe_product():
    # Create the product
    product = stripe.Product.create(
        name="The Artisan's Circle",
        description="Featured Artworks"
    )

    # Create the price
    price = stripe.Price.create(
        unit_amount=2000,  # $20.00 in cents
        currency="usd",
        product=product.id,
    )

    return JsonResponse({
        "product_id": product.id,
        "price_id": price.id
    })
@login_required
def profile_view(request, user_id):
    # Get the user for the profile being viewed
    user = get_object_or_404(CustomUser, id=user_id)

    # Fetch the profile related to the user (if exists)
    users_profile = user.profile
    # Check if it's the logged-in user's own profile
    is_own_profile = (request.user.id == user_id)

    # Fetch posts belonging to the profile user (not the logged-in user)
    posts = Post.objects.filter(user=user).order_by("-created_at")

    # Count the posts and calculate total flowers (likes)
    post_count = posts.count()
    total_flowers = posts.aggregate(total=Sum('flowers'))['total'] or 0

    # Handle profile picture if it exists
    profile_picture = users_profile.profile_picture if users_profile and users_profile.profile_picture else None

    # Handle case where the profile does not exist (e.g., create one)
    if users_profile is None:
        users_profile = Profile.objects.create(user=user)

    f_form = None  # Initialize the form variable to avoid "referenced before assignment" errors

    # Handle profile update only for the logged-in user viewing their own profile
    if request.user == user:
        if request.method == 'POST':
            f_form = ProfileForm(request.POST, request.FILES, instance=users_profile)  # Use `users_profile`
            if f_form.is_valid():
                f_form.save()  # Save the updated profile data
                return redirect('profile_view', user_id=request.user.id)
        else:
            f_form = ProfileForm(instance=users_profile)  # Prepopulate the form for GET requests

    return render(request, 'profile.html', {
        'user_id': user_id,
        'profile': users_profile,
        'profile_picture': profile_picture,
        'f_form': f_form,
        'user': request.user,
        'user_posts': posts,
        'post_count': post_count,
        'total_flowers': total_flowers,
        'is_own_profile': is_own_profile,
    })


def create_artwork(request):
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('artwork_list')  # Replace with your desired redirect URL
    else:
        form = ArtworkForm()
    return render(request, 'artworks/create_artwork.html', {'form': form})

def update_artwork(request, pk):
    artwork = Artwork.objects.get(pk=pk)
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            form.save()
            return redirect('artwork_detail', pk=pk)  # Replace with your desired redirect URL
    else:
        form = ArtworkForm(instance=artwork)
    return render(request, 'artworks/update_artwork.html', {'form': form, 'artwork': artwork})

def artwork_list(request):
    artworks = Artwork.objects.all()
    return render(request, 'artworks/artwork_list.html', {'artworks': artworks})

def calculate_feedback_metrics():
    # Calculate total feedback count
    total_feedback = Feedback.objects.count()

    # Calculate helpful feedback count
    helpful_feedback = Feedback.objects.filter(helpful=True).count()

    # Calculate the percentage of helpful feedback
    helpful_percentage = (helpful_feedback / total_feedback * 100) if total_feedback > 0 else 0

    return {
        'total_feedback': total_feedback,
        'helpful_feedback': helpful_feedback,
        'helpful_percentage': helpful_percentage,
    }

def coming_soon(request):
    return render(request, 'coming.html')


def feedback_dashboard(request):
    # Get the feedback metrics
    feedback_metrics = calculate_feedback_metrics()

    # Render the feedback data to the template
    return render(request, 'feedback_dashboard.html', {'feedback_metrics': feedback_metrics})
