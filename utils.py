from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import openai
from web3 import Web3
import requests
import os
from cryptography.fernet import Fernet
import base64
from django.db.models import Avg, Count, Q

# Artistic Caption Generator
def generate_artistic_caption(prompt="Describe this artwork in a poetic and creative way."):
    try:
        # Load OpenAI API key
        openai.api_key = settings.OPENAI_API_KEY
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error generating artistic caption: {e}"

def calculate_feedback_metrics():
    from .models import Feedback
    total_feedback = Feedback.objects.count()
    if total_feedback == 0:
        return {
            "average_rating": 0,
            "positive_percentage": 0,
            "negative_percentage": 0,
            "total_feedback": 0,
        }
    average_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg']
    positive_feedback = Feedback.objects.filter(rating__gte=4).count()
    negative_feedback = Feedback.objects.filter(rating__lte=2).count()

    positive_percentage = (positive_feedback / total_feedback) * 100
    negative_percentage = (negative_feedback / total_feedback) * 100

    return {
        "average_rating": round(average_rating, 2),
        "positive_percentage": round(positive_percentage, 2),
        "negative_percentage": round(negative_percentage, 2),
        "total_feedback": total_feedback,
    }
# Send Login Email
def send_login_email(user, request=None):
    try:
        subject = 'Welcome Back to Controlled Motives'
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]

        # Load email template with user context
        context = {'user': user}
        html_content = render_to_string('emails/login_email.html', context)

        email = EmailMultiAlternatives(subject, '', from_email, to_email)
        email.attach_alternative(html_content, 'text/html')
        email.send()
    except Exception as e:
        raise Exception(f"Error sending login email: {e}")


# Web3 Configuration
web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'))

SECRET_KEY = base64.urlsafe_b64encode(os.urandom(32))
cipher = Fernet(SECRET_KEY)

def encrypt_private_key(private_key):
    """Encrypts a private key using Fernet."""
    return cipher.encrypt(private_key.encode()).decode()

def decrypt_private_key(encrypted_key):
    """Decrypts a private key using Fernet."""
    return cipher.decrypt(encrypted_key.encode()).decode()

# Mint NFT Function
def mint_nft(artwork, artist_wallet_address):
    try:
        # Load sensitive data from environment variables
        contract_address = os.getenv("SMART_CONTRACT_ADDRESS")
        private_key = os.getenv("PRIVATE_KEY")

        if not contract_address or not private_key:
            raise EnvironmentError("Smart contract address or private key not set in environment.")

        # Validate artist wallet address
        if not Web3.isAddress(artist_wallet_address):
            raise ValueError("Invalid artist wallet address.")

        # Load contract ABI
        contract_abi = [...]  # Replace with your actual ABI

        # Create contract instance
        contract = web3.eth.contract(address=Web3.toChecksumAddress(contract_address), abi=contract_abi)

        # Metadata URI for the artwork
        metadata_uri = f"https://your-metadata-api/{artwork.id}/metadata.json"

        # Prepare mint transaction
        nonce = web3.eth.get_transaction_count(Web3.toChecksumAddress(artist_wallet_address))
        transaction = contract.functions.mintNFT(
            artist_wallet_address, metadata_uri
        ).build_transaction({
            'to': 'SELLER_WALLET_ADDRESS',
            'value': web3.toWei(artwork.price, 'ether'),
            'gas': 2000000,
            'gasPrice': web3.toWei('50', 'gwei'),
            'nonce': nonce,
            'chainId': 1,  # Mainnet
        })

        # Sign and send the transaction
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        return web3.toHex(tx_hash)
    except Exception as e:
        raise Exception(f"Error minting NFT: {e}")


# Upload Metadata to IPFS
def upload_metadata_to_ipfs(artwork):
    try:
        # Load Pinata credentials
        pinata_api_key = os.getenv("PINATA_API_KEY")
        pinata_secret_api_key = os.getenv("PINATA_SECRET_API_KEY")

        if not pinata_api_key or not pinata_secret_api_key:
            raise EnvironmentError("Pinata API credentials not set in environment.")

        url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
        headers = {
            "pinata_api_key": pinata_api_key,
            "pinata_secret_api_key": pinata_secret_api_key,
        }

        # Prepare metadata
        metadata = {
            "name": artwork.title,
            "description": f"Artwork by {artwork.artist.name}",
            "image": f"https://your-server/{artwork.image.url}",  # Update with actual image URL logic
        }

        # Upload metadata to Pinata
        response = requests.post(url, json=metadata, headers=headers)

        if response.status_code == 200:
            return response.json()["IpfsHash"]  # Returns the CID
        else:
            raise Exception(f"Failed to upload metadata to IPFS: {response.text}")
    except Exception as e:
        raise Exception(f"Error uploading metadata to IPFS: {e}")
