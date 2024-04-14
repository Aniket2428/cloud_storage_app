# Use a Python base image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Define envirzonment variable
ENV FLASK_APP=app.py

# Expose port 8080
EXPOSE 8080

# Command to run the Flask application
CMD ["python3", "app.py"]
