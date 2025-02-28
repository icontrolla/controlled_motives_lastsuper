import boto3

AWS_REGION = "ap-south-1"  # Replace with your AWS region
KMS_KEY_ID = "arn:aws:kms:ap-south-1:182399678050:key/676b06b0-f17a-4a38-b7c8-66eeaafd53b6"  # Replace with your KMS Key ARN

kms_client = boto3.client("kms", region_name=AWS_REGION)

def encrypt_data(data):
    """Encrypts data using AWS KMS."""
    response = kms_client.encrypt(
        KeyId=KMS_KEY_ID,
        Plaintext=data.encode("utf-8")
    )
    return response["CiphertextBlob"]

def decrypt_data(encrypted_data):
    """Decrypts data using AWS KMS."""
    response = kms_client.decrypt(
        CiphertextBlob=encrypted_data
    )
    return response["Plaintext"].decode("utf-8")
