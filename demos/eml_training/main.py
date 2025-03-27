import base64
import json
import requests
import tempfile
from venumML.venumpy import small_glwe as vp 
import functions_framework
from google.cloud import pubsub_v1
from google.cloud import storage

publisher = pubsub_v1.PublisherClient()
reencrypt_topic = "projects/vaultree-ml-team/topics/loss_pre"

VAULT_ADDR = "https://your-vault-address:8200"
VAULT_SECRET_PATH = "secret/ml_keys"
VAULT_TOKEN = "your-vault-token"
BUCKET_NAME = "eml_training"
BUCKET_PATH = "secret_context.json"

def load_saved_key():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(BUCKET_PATH)
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        blob.download_to_filename(temp_file.name)
        with open(temp_file.name, 'r') as ctx_file:
            ctx_json = json.dumps(json.load(ctx_file))
            ctx = vp.SecretContext.from_json(ctx_json)
            ctx.precision = 6
    return ctx

def dummy_pre_reencrypt(ctx, encrypted_data):
    return encrypted_data

@functions_framework.cloud_event
def process_pubsub_event(cloud_event):
    try:
        print(cloud_event.data["data"])
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        message_data = json.loads(pubsub_message)
        encryption_key = load_saved_key()
        ctx = encryption_key
        encrypted_loss = message_data["encrypted_loss"]
        print(f"Received encrypted loss: {encrypted_loss}")
        reencrypted_loss = dummy_pre_reencrypt(ctx, encrypted_loss)
        reencrypted_message = json.dumps({"reencrypted_loss": reencrypted_loss})
        publisher.publish(reencrypt_topic, reencrypted_message.encode("utf-8"))
        print(f"Re-encrypted loss published: {reencrypted_message}")
    except Exception as e:
        print(f"Error processing message: {e}")
        raise




# import base64
# import json
# import requests
# from venumML.venumpy import small_glwe as vp 
# import functions_framework
# from google.cloud import pubsub_v1

# # Pub/Sub client to publish messages
# publisher = pubsub_v1.PublisherClient()
# reencrypt_topic = "projects/vaultree-ml-team/topics/loss_pre"

# # Vault settings
# VAULT_ADDR = "https://your-vault-address:8200"
# VAULT_SECRET_PATH = "secret/ml_keys"
# VAULT_TOKEN = "your-vault-token"  # Ideally, use GCP IAM authentication instead of a static token.
# CTX_LOCAL_PATH = "./secret_context.json"
# BUCKET_NAME = "eml_training" 
# BUCKET_PATH = "secret_context.json"

# def load_saved_key():
#     """Triggered by a change to a Cloud Storage bucket."""
    
#     # Create a client instance
#     storage_client = storage.Client()
    
#     # Specify the file path
#     file_path = "gs://eml_training/secret_context.json"
    
#     # Get the bucket
#     bucket = storage_client.bucket(BUCKET_NAME)
    
#     # Get the blob (file)
#     blob = bucket.blob(file_path)
    
#     # Download the file to a temporary location
#     temp_file_path = "/tmp/" + blob.name.split("/")[-1]
#     blob.download_to_filename(temp_file_path)
    
#     # Load the saved context
#     with open(temp_file_path, 'r') as ctx_file:
#         ctx_json = json.dumps(json.load(ctx_file))
#         ctx = vp.SecretContext.from_json(ctx_json)  # Assuming from_json exists
#         ctx.precision = 6  # Ensure precision matches
#     return ctx


# def get_keys_from_vault():
#     """Fetch encryption and re-encryption keys from HashiCorp Vault."""
#     headers = {"X-Vault-Token": VAULT_TOKEN}
#     response = requests.get(f"{VAULT_ADDR}/v1/{VAULT_SECRET_PATH}", headers=headers)

#     if response.status_code == 200:
#         data = response.json()["data"]
#         return data["encryption_key"], data["reencryption_key"]
#     else:
#         raise Exception(f"Failed to fetch keys from Vault: {response.text}")

# def dummy_pre_reencrypt(ctx, encrypted_data):
#     """Dummy PRE re-encryption function that returns the same ciphertext."""
#     return encrypted_data  # No actual transformation in this dummy scheme.
    
# @functions_framework.cloud_event
# def process_pubsub_event(cloud_event):
#     """Cloud Function triggered by Pub/Sub to re-encrypt loss values."""
#     try:
#         # Decode Pub/Sub message
#         pubsub_message = base64.b64decode(cloud_event['data']).decode('utf-8')
#         message_data = json.loads(pubsub_message)

#         # Fetch keys from Vault
#         # encryption_key, reencryption_key = get_keys_from_vault()

#         encryption_key = load_saved_key()


#         # Initialize SecretContext with fetched key
#         # ctx = vp.SecretContext(encryption_key)
#         ctx = encryption_key

   

#         # Extract encrypted loss value
#         encrypted_loss = message_data["encrypted_loss"]
#         print(encrypted_loss)

#         # Dummy re-encrypt
#         reencrypted_loss = dummy_pre_reencrypt(ctx, encrypted_loss)

#         # Publish to another topic
#         reencrypted_message = json.dumps({"reencrypted_loss": reencrypted_loss})
#         publisher.publish(reencrypt_topic, reencrypted_message.encode("utf-8"))

#         print(f"Re-encrypted loss published: {reencrypted_message}")

#     except Exception as e:
#         print(f"Error processing message: {e}")
