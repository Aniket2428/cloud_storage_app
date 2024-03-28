from flask import Flask, render_template, request, redirect, url_for, send_file
from urllib.parse import quote
import os
from werkzeug.utils import secure_filename
import psycopg2
from datetime import datetime
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Replace with your Azure Storage account details
account_name = 'cloudstorageapp'
account_key = 'HNTkshHozHqfSYh7nqoK9M+vH+q3lvg5SySlQz2SkDCnwSVXghKWpHs6GSfHbJEAqGpIdc6dWC9W+AStRAlGLA=='
container_name = 'files'

# Initialize the Azure Blob Storage client
connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metadata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

conn = psycopg2.connect(
    dbname="your_database",
    user="mydb",
    password="aniket@123",
    host="localhost",
    port="9000"
)
cur = conn.cursor()

@app.route('/')
def index():
    files = list_files()
    print(files)
    return render_template('index.html', files=files)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    azure_blob_name = secure_filename(file.filename)
    upload_file_to_azure(file, container_name, azure_blob_name)

    return redirect(url_for('index'))


@app.route('/download/<file_name>')
def download_file(file_name):
    local_file_path = os.path.join('temp', quote(file_name))
    download_file_from_azure(file_name, container_name, local_file_path)
    # download_file_from_azure(file_name, container_name, local_file_path)
    return send_file(local_file_path, as_attachment=True)


@app.route('/delete/<file_name>')
def delete_file(file_name):
    # local_file_path = os.path.join('temp', quote(file_name))
    delete_blob_from_azure(container_name, file_name, connection_string)
    return refreshScreen()


def refreshScreen():
    files = list_files()
    print(files)
    return render_template('index.html', files=files)


def list_files():
    container_client = blob_service_client.get_container_client(container_name)
    blobs = [blob.name for blob in container_client.list_blobs()]
    return blobs


def upload_file_to_azure(file, container_name, azure_blob_name):
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(azure_blob_name)

    try:
        blob_client.upload_blob(file)
    except Exception as e:
        print(f"Error uploading file to Azure Blob Storage: {str(e)}")


def download_file_from_azure(file_name, container_name, local_file_path):
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(file_name)

    try:
        # Ensure the 'temp' directory exists
        os.makedirs('temp', exist_ok=True)

        # Use os.path.join for constructing the local file path
        local_file_path = os.path.join('temp', quote(file_name))

        with open(local_file_path, 'wb') as file:
            data = blob_client.download_blob()
            data.readinto(file)
    except Exception as e:
        print(f"Error downloading file from Azure Blob Storage: {str(e)}")


def delete_blob_from_azure(container_name, blob_name, connection_string):
    try:
        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Get a container client
        container_client = blob_service_client.get_container_client(container_name)

        # Delete the blob
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()

        print(f"Blob '{blob_name}' deleted successfully from container '{container_name}'.")
    except Exception as e:
        print(f"Error deleting blob '{blob_name}' from container '{container_name}': {e}")


#
# def check_container_exists(storage_connection_string, container_name):
#     try:
#         blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
#         container_client = blob_service_client.get_container_client(container_name)
#         # Attempt to get properties of the container, which will raise an error if the container does not exist
#         container_client.get_container_properties()
#         return True
#     except Exception as e:
#         return False
#
#
# def list_containers(storage_connection_string):
#     """
#     List all containers in Azure Storage.
#
#     Args:
#     storage_connection_string (str): Azure Storage connection string.
#
#     Returns:
#     list: A list of container names.
#     """
#     blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
#     containers = []
#     for container in blob_service_client.list_containers():
#         containers.append(container['name'])
#     return containers
#

# Check if container exists


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
