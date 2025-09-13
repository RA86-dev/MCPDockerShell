################################
# Linux Only
################################
# Check if linux
if [ "$(uname)" != "Linux" ]; then
    echo "This script is only for Linux"
    exit 1
fi

# Check if docker is installed
if ! [ -x "$(command -v docker)" ]; then
    echo "Docker is not installed."
    echo "Please install docker and try again."
    exit 1
fi

# Check if docker compose is installed
if ! [ -x "$(command -v docker compose)" ]; then
    echo "Docker Compose is not installed."
    echo "Please install docker compose and try again."
    exit 1
fi
git clone https://github.com/RA86-dev/MCPDockerShell.git
cd MCPDockerShell
echo "Building and starting the server... This may take up to 10 minutes."
docker compose up -d --build
echo "Server is running at http://localhost:8000"