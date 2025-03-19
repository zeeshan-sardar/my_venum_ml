from venumML.linear_models.regression.linear_regression import EncryptedLinearRegression
from venumML.venum_tools import encrypt_array, decrypt_array
from venumML.venumpy import small_glwe as vp 
from google.cloud import storage
import json

# Initialize the secret context
ctx = vp.SecretContext()
ctx.precision = 6

# Function to download and load JSON from GCP bucket
def load_json_from_bucket(bucket_name, file_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    # Download the file as a string and parse JSON
    json_data = blob.download_as_string()
    return json.loads(json_data)

# Specify your bucket name and file paths
bucket_name = "eml_training"  # Replace with your GCP bucket name
x_train_file = "X_train_ct.json"    # Path to X_train file in the bucket
y_train_file = "y_train_ct.json"    # Path to y_train file in the bucket

# Load X_train and y_train from the bucket
X_train = load_json_from_bucket(bucket_name, x_train_file)
y_train = load_json_from_bucket(bucket_name, y_train_file)

# Initialize and train the encrypted linear regression model
model_enc = EncryptedLinearRegression(ctx)
model_enc.encrypted_fit(ctx, X_train, y_train, lr=0.03)

print("Model coeff.", decrypt_array(model_enc._encrypted_coef_))