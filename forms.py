from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile, Post
from .models import Artist
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomUser
from django.apps import apps

CustomUser = apps.get_model('profiles', 'CustomUser')

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2',  'wallet_address', 'blockchain_type']

    def clean_username(self):
        username = self.cleaned_data['username']
        user = get_user_model()  # Access the custom user model
        if user.objects.filter(username=username).exists():  # Use the correct manager
            raise forms.ValidationError("Username already exists")
        return username

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'wallet_address', 'blockchain_type']


class ArtistLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ArtistSignupForm(forms.ModelForm):

    CATEGORY_CHOICES = [
        ('painter', 'Painter'),
        ('sculptor', 'Sculptor'),
        ('photographer', 'Photographer'),
        ('digital_artist', 'Digital Artist'),
        ('other', 'Other'),
    ]

    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")
    bio = forms.CharField(widget=forms.Textarea, required=False)
    profile_picture = forms.ImageField(required=True)  # Profile image
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)  # Artist category
    wallet_address = forms.CharField(max_length=255, required=False)
    blockchain_type = forms.ChoiceField(choices=CustomUser.BLOCKCHAIN_CHOICES, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'bio', 'profile_picture',
                  'wallet_address', 'blockchain_type', 'category', 'is_major']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user = get_user_model()
        if user.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose a different one.")
        return username

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        # Create user
        user = get_user_model().objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        artist = super().save(commit=False)
        artist.user = user
        if commit:
            artist.save()
        return artist
    
    

class ImagePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'caption', 'content']


class VideoPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'caption']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']


class EditUserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture']


class PostForm(forms.ModelForm):
    auto_generate_caption = forms.BooleanField(required=False, label="Let AI generate a caption")

    class Meta:
        model = Post
        fields = ['title', 'content', 'caption', 'image','auto_generate_caption'
                  ]

from .models import Artwork

class FlowerForm(forms.ModelForm):
    artist = forms.ModelChoiceField(queryset=CustomUser.objects.all(), required=True)

    class Meta:
        model = Artwork
        fields = ['title', 'artist', 'description']


class ArtistProfileForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['bio', 'profile_picture', 'category', 'is_featured', 'is_trending']

class ArtworkForm(forms.ModelForm):
    class Meta:
        model = Artwork
        fields = [
            'title', 'description', 'image', 'price', 'category',
            'is_featured', 'is_trending', 'nft_contract_address',
            'nft_token_id', 'blockchain', 'is_nft', 'mint_date', 'nft_url'
        ]
        widgets = {
            'mint_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }