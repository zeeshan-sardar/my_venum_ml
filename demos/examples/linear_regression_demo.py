from venumML.linear_models.regression.linear_regression import EncryptedLinearRegression
from venumML.venum_tools import encrypt_array, decrypt_array
from venumML.venumpy import small_glwe as vp 
from google.cloud import storage
import numpy as np
import json

# Initialize the secret context
ctx = vp.SecretContext()
ctx.precision = 6

# Function to download JSON file from GCP bucket to VM local filesystem
def load_json_from_bucket(bucket_name, file_path, local_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    # Download the file to the specified local path on the VM
    blob.download_to_filename(local_path)
    print(f"Downloaded {file_path} to {local_path}")
    return local_path  # Return the local file path

# Function to deserialize JSON file into Ciphertext objects (1D or 2D)
def deserialize_json(ctx, file_path):
    print(file_path)
    # Read the JSON file from the local filesystem
    with open(file_path, 'r') as file:
        json_string = file.read()
    parsed_json = json.loads(json_string)
    
    # Debug output to inspect structure
    print("Parsed JSON type:", type(parsed_json))
    if isinstance(parsed_json, list) and parsed_json:  # Non-empty list
        print("First element type:", type(parsed_json[0]))
        if isinstance(parsed_json[0], list):  # 2D array
            # print("Parsed JSON sample (first row, first 2 items):", parsed_json[0][:2])
            return [
                [vp.Ciphertext.from_json(ctx, json.dumps(item)) for item in row]
                for row in parsed_json
            ]
        else:  # 1D array
            # print("Parsed JSON sample (first 2 items):", parsed_json[:2])
            return [vp.Ciphertext.from_json(ctx, json.dumps(item)) for item in parsed_json]
    else:
        raise ValueError("Invalid JSON structure: expected a 1D or 2D list")

# Specify your bucket name and file paths
bucket_name = "eml_training"  # Replace with your GCP bucket name
x_train_bucket_path = "X_train_ct.json"
y_train_bucket_path = "y_train_ct.json"
ctx_bucket_path = "secret_context.json"

# Local paths on the VM
x_train_local_path = "/home/zeeshan.sardar/my_venum_ml/demos/examples/X_train_ct.json"  # Adjust path as needed
y_train_local_path = "/home/zeeshan.sardar/my_venum_ml/demos/examples/y_train_ct.json"  # Adjust path as needed
ctx_local_path = "/home/zeeshan.sardar/my_venum_ml/demos/examples/secret_context.json"

# Download files from bucket to VM
load_json_from_bucket(bucket_name, x_train_bucket_path, x_train_local_path)
load_json_from_bucket(bucket_name, y_train_bucket_path, y_train_local_path)
load_json_from_bucket(bucket_name, ctx_bucket_path, ctx_local_path)

# Load the saved context
with open(ctx_local_path, 'r') as ctx_file:
    ctx_json = json.dumps(json.load(ctx_file))
    ctx = vp.SecretContext.from_json(ctx_json)  # Assuming from_json exists
    ctx.precision = 6  # Ensure precision matches


# Deserialize X_train and y_train from local files
X_train = np.array(deserialize_json(ctx, x_train_local_path))
y_train = np.array(deserialize_json(ctx, y_train_local_path))

print(decrypt_array(X_train))

# Initialize and train the encrypted linear regression model
model_enc = EncryptedLinearRegression(ctx)
model_enc.encrypted_fit(ctx, X_train, y_train, lr=0.03)

print("Model coeff.", decrypt_array(model_enc._encrypted_coef_))