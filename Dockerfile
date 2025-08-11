FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for the MCP proxy
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py config.json launch_system.sh ./

# Make launch script executable
RUN chmod +x launch_system.sh

# Expose port (if needed for web interface)
EXPOSE 8080

# Default command
CMD ["python", "main.py"]