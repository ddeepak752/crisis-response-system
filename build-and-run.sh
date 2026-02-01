#!/bin/bash

# Crisis Response Chatbot - Docker Build and Run Script
# Usage: ./build-and-run.sh

set -e  # Exit on any error

echo "🚨 Crisis Response Chatbot - Docker Setup"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "✅ Docker and docker-compose are available"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p rasa_project/models
mkdir -p frontend
chmod -R 755 rasa_project
chmod -R 755 frontend

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build --no-cache

echo "🚀 Starting Crisis Response Chatbot services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

echo "Checking Action Server..."
if curl -s -f http://localhost:5055/health > /dev/null; then
    echo "✅ Action Server is running on port 5055"
else
    echo "⚠️  Action Server not ready yet (this is normal, it may take longer to start)"
fi

echo "Checking Rasa Server..."
if curl -s -f http://localhost:5005/status > /dev/null; then
    echo "✅ Rasa Server is running on port 5005"
else
    echo "⚠️  Rasa Server not ready yet (training may still be in progress)"
fi

echo "Checking Streamlit Frontend..."
if curl -s -f http://localhost:8501/_stcore/health > /dev/null; then
    echo "✅ Streamlit Frontend is running on port 8501"
else
    echo "⚠️  Streamlit Frontend not ready yet"
fi

echo ""
echo "🎉 Crisis Response Chatbot Services Started!"
echo ""
echo "📱 Access your chatbot at: http://localhost:8501"
echo "🔧 Rasa API available at: http://localhost:5005"
echo "⚙️  Action Server at: http://localhost:5055"
echo ""
echo "📋 Useful Commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart:       docker-compose restart"
echo "   Rebuild:       docker-compose up --build -d"
echo ""
echo "⚠️  Note: First startup may take 2-3 minutes for Rasa training to complete."

# Show real-time logs for a few seconds
echo "📄 Recent logs (showing last 20 lines from each service):"
docker-compose logs --tail=20

echo ""
echo "🚀 Your Crisis Response Chatbot is ready!"
echo "   Visit: http://localhost:8501"
