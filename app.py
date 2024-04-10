from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, flash, session
from urllib.parse import quote
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient

from mongo import mongo, init_mongo

app = Flask(__name__)

# Replace with your Azure Storage account details
account_name = 'cloudstorageapp'
account_key = 'HNTkshHozHqfSYh7nqoK9M+vH+q3lvg5SySlQz2SkDCnwSVXghKWpHs6GSfHbJEAqGpIdc6dWC9W+AStRAlGLA=='

# Initialize the Azure Blob Storage client
connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
mongo_uri = "mongodb+srv://storage:Abhey123@cluster0.i4dedvi.mongodb.net/database"

upload_message = ""

app.config["MONGO_URI"] = mongo_uri
app.config['SECRET_KEY'] = os.urandom(24)

init_mongo(app)


# Define a route for the root URL
@app.route('/')
def index():
    return render_template('signup.html')  # Redirect to signup page when accessing root URL


@app.route('/homepage')
def homepage():
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    containers = list_containers()
    print(containers)
    return render_template('containers.html', containers=containers, username=session.get('username'))


@app.route('/<path:container_name>')
def list_container_files(container_name):
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    files = list_files(container_name)
    print(files)
    return render_template('index.html', files=files, container_name=container_name, message=upload_message)


@app.route('/<path:container_name>/upload', methods=['POST'])
def upload_file(container_name):
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    azure_blob_name = secure_filename(file.filename)
    upload_file_to_azure(file, container_name, azure_blob_name)
    files = list_files(container_name)
    print(files)
    upload_message = "Uploaded Successfully."
    return render_template('index.html', files=files, container_name=container_name, message=upload_message)


@app.route('/<path:container_name>/download/<file_name>')
def download_file(container_name, file_name):
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    local_file_path = os.path.join('temp', quote(file_name))
    download_file_from_azure(file_name, container_name, local_file_path)
    # download_file_from_azure(file_name, container_name, local_file_path)
    return send_file(local_file_path, as_attachment=True)


@app.route('/<path:container_name>/delete/<file_name>')
def delete_file(container_name, file_name):
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    # local_file_path = os.path.join('temp', quote(file_name))
    delete_blob_from_azure(container_name, file_name, connection_string)
    files = list_files(container_name)
    print(files)
    upload_message = "Deleted Successfully."
    return render_template('index.html', files=files, container_name=container_name, message=upload_message)


@app.route('/create_container', methods=['POST'])
def create_blob_container():
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    container_name = request.form['containerName']
    print(container_name)
    if not container_name:
        return 'Container name cannot be empty'
    if not container_name.islower():
        return 'Container name must be all lowercase'
    if not container_name.isalnum():
        return 'Container name must contain only alphanumeric characters'

    try:
        container_client = create_container(container_name)
        return redirect(request.referrer)
    except Exception as e:
        return f'Error creating container: {str(e)}', 500


@app.route('/delete_container/<path:container_name>', methods=['GET'])
def delete_container(container_name):
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    try:
        # Azure Blob Storage connection string
        # Create BlobServiceClient using connection string
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Delete the container
        blob_service_client.delete_container(container_name)

        return redirect(request.referrer)
    except Exception as e:
        return f"Error occurred: {e}"


# Route to list all containers
@app.route('/list_containers', methods=['GET'])
def list_blob_containers():
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    try:
        containers = list_containers()
        return jsonify(containers), 200
    except Exception as e:
        return f'Error listing containers: {str(e)}', 500


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate password and confirm password
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('signup'))

        # Check if username or email already exists
        existing_user = mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            flash('Username or email already exists. Please choose different ones.', 'error')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Store user data in the database
        try:
            mongo.db.users.insert_one({'username': username, 'email': email, 'password': hashed_password})
            flash('Account created successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('An error occurred while creating your account. Please try again later.', 'error')
            app.logger.error(f"Error creating user: {e}")

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username exists in the database
        user = mongo.db.users.find_one({'username': username})
        if not user:
            flash('No user found with this username. Please sign up first.', 'error')
            return redirect(url_for('login'))

        # Validate password
        if not check_password_hash(user['password'], password):
            flash('Invalid password. Please try again.', 'error')
            return redirect(url_for('login'))

        # Login successful
        session['logged_in'] = True
        session['username'] = username  # Optionally store username in session
        flash('Login successful!', 'success')
        return redirect(url_for('homepage'))

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  # Clear username from session if stored
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# def refreshScreen(container_name):
#     files = list_files(container_name)
#     print(files)
#     return render_template('index.html', files=files,container_name=container_name)


def list_files(container_name):
    container_client = blob_service_client.get_container_client(container_name)
    blobs = [blob.name for blob in container_client.list_blobs()]
    return blobs


# Function to create a container in Azure Blob Storage
def create_container(container_name):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.create_container(container_name)
    return redirect(request.referrer)


# Function to list all containers in Azure Blob Storage
def list_containers():
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    containers = blob_service_client.list_containers()
    return [container.name for container in containers]


def upload_file_to_azure(file, container_name, azure_blob_name):
    if not session.get('logged_in'):
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

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


# Route to create a container

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
