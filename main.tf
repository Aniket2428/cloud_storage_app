provider "google" {
  project = "your-project-id" # Replace with your GCP project ID
  region  = "us-central1"     # Update with your desired GCP region
}

resource "google_compute_instance" "flask_instance" {
  name         = "flask-instance"
  machine_type = "n1-standard-1"   # Update with your desired machine type
  zone         = "us-central1-a"   # Update with your desired zone
  tags         = ["http-server"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-10"  # Update with your desired OS image
    }
  }

  network_interface {
    network = "default"
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y python3 python3-pip git
    pip3 install flask
    git clone https://github.com/your_username/your_flask_app.git /opt/your_flask_app
     nohup python3 /opt/your_flask_app/app.py --host=0.0.0.0 --port=8080 &
  EOF
}
