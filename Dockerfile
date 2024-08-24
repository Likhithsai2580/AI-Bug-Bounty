# Use Kali Linux as the base image
FROM kalilinux/kali-rolling

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Update and install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install additional tools (these are usually pre-installed in Kali, but ensuring they're there)
RUN apt-get install -y \
    nmap \
    sqlmap \
    nikto \
    && rm -rf /var/lib/apt/lists/*

# Make port 80 available to the world outside this container
EXPOSE 80

# Run main.py as root when the container launches
CMD ["python3", "main.py"]