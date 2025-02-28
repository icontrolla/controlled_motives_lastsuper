from web3 import Web3
from django.conf import settings

# Connect to Ethereum blockchain
web3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_RPC_URL))

def send_eth_transaction(to_address, value_in_eth):
    """Send Ethereum transaction and return the transaction hash."""
    sender_address = settings.WALLET_ADDRESS
    private_key = settings.WALLET_PRIVATE_KEY

    # Convert ETH to Wei
    value_in_wei = web3.to_wei(value_in_eth, 'ether')

    # Create transaction
    txn = {
        'to': to_address,
        'value': value_in_wei,
        'gas': 21000,  # Standard gas for ETH transfer
        'gasPrice': web3.to_wei(50, 'gwei'),
        'nonce': web3.eth.get_transaction_count(sender_address),
        'chainId': 1  # Ethereum Mainnet (Goerli = 5)
    }

    # Sign and send transaction
    signed_txn = web3.eth.account.sign_transaction(txn, private_key)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return txn_hash.hex()
