# Docker Deployment Guide: Moving to Another PC

This guide explains how to take your `synthetix 4.0` project and run it on a different computer using Docker.

## Prerequisites on the Destination PC
1. **Docker Desktop** (or Docker Engine) must be installed.
2. The computer should have internet access (unless using the Offline Transfer method).

---

## Method 1: Docker Hub (Recommended)
This is the standard way to share images. It's like uploading a video to YouTube and watching it on another device.

### 1. Tag and Push (On your PC)
Open your terminal in the project folder and run:
```bash
# Log in to your Docker Hub account
docker login

# Build the image
docker build -t your-username/synthetix-app:latest .

# Push it to the cloud
docker push your-username/synthetix-app:latest
```

### 2. Pull and Run (On the Other PC)
```bash
# Pull the image from the cloud
docker pull your-username/synthetix-app:latest

# Run the container
docker run -p 8000:8000 your-username/synthetix-app:latest
```

---

## Method 2: Offline Transfer (USB/Local Network)
If you don't want to use an online registry, you can export the image as a file.

### 1. Export the Image (On your PC)
```bash
# Build the image locally
docker build -t synthetix-local:latest .

# Save it to a .tar file
docker save -o synthetix-app.tar synthetix-local:latest
```
Copy `synthetix-app.tar` to a USB drive or send it to the other PC.

### 2. Import and Run (On the Other PC)
```bash
# Load the image from the file
docker load -i synthetix-app.tar

# Run the container
docker run -p 8000:8000 synthetix-local:latest
```

---

## Running with Docker Compose
Since your project already has a [docker-compose.yml](file:///c:/Users/DELL/OneDrive/Desktop/synthetix%204.0/docker-compose.yml), you can also just share the source code and run:

1. Copy the entire `synthetix 4.0` folder to the other PC.
2. Open a terminal in that folder on the other PC.
3. Run:
   ```bash
   docker-compose up --build
   ```
This will automatically build the image and start the service with the defined volumes and environment variables.

> [!TIP]
> **Port Mapping:** The app runs on port `8000` inside the container. We map it to `8000` on the PC (`-p 8000:8000`). You can access the API at `http://localhost:8000`.

> [!IMPORTANT]
> **Data Persistence:** If you use `docker run`, your data files inside the container might be lost when the container is deleted. Use Method 3 (Docker Compose) if you want to keep data synced with local folders.
