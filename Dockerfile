# Use Kali Linux as the base image
FROM kalilinux/kali-rolling

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file initially
COPY requirements.txt .

# Update and install Python, pip, and required packages
RUN apt-get update && \
    apt-get install -y python3 python3-pip nmap sqlmap nikto && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application
COPY . .

# Create a non-root user and switch to it
RUN useradd -m appuser
USER appuser

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run main.py when the container launches
CMD ["python3", "main.py"]