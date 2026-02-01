# Crisis Response Chatbot - Docker Deployment

A professional emergency response chatbot system built with Rasa, Python, and Streamlit, deployed using Docker containers.

## 🚨 System Architecture

This system consists of three main services:
- **Crisis Rasa Server** (Port 5005): NLU and dialogue management
- **Crisis Action Server** (Port 5055): Custom Python actions and risk assessment
- **Crisis Frontend** (Port 8501): Streamlit web interface

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available for containers
- Ports 5005, 5055, and 8501 available

### 1. Build and Run
```bash
# Make the build script executable
chmod +x build-and-run.sh

# Build and start all services
./build-and-run.sh
```

### 2. Access the Chatbot
- **Web Interface**: http://localhost:8501
- **Rasa API**: http://localhost:5005
- **Action Server**: http://localhost:5055

## 📋 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Build all images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 🛠️ Development Commands

```bash
# View logs for specific service
docker-compose logs -f crisis-rasa-server
docker-compose logs -f crisis-action-server  
docker-compose logs -f crisis-frontend

# Restart a specific service
docker-compose restart crisis-rasa-server

# Rebuild and restart
docker-compose up --build -d

# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v
```

## 🔧 Troubleshooting

### Service Won't Start
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs crisis-rasa-server

# Rebuild specific service
docker-compose build --no-cache crisis-rasa-server
docker-compose up -d crisis-rasa-server
```

### Port Conflicts
If ports are already in use, modify `docker-compose.yml`:
```yaml
services:
  crisis-frontend:
    ports:
      - "8502:8501"  # Change external port
```

### Memory Issues
Increase Docker memory allocation:
- Docker Desktop: Settings > Resources > Memory > 6GB+

## 📊 Crisis Types Supported

1. **🏠 Earthquake**: Shaking detection, aftershock preparation, safety protocols
2. **🌊 Flood**: Water level assessment, evacuation planning, safety guidance  
3. **🔥 Fire**: Smoke detection, evacuation routes, emergency protocols
4. **⚡ Power Outage**: Medical equipment dependency, safety protocols

## 🎯 Key Features

- **Professional 911-Style Assessment**: Follows emergency dispatch protocols
- **Risk Scoring Engine**: Quantified risk assessment (0-100 scale)
- **Vulnerability-Aware**: Prioritizes children, elderly, disabled, pregnant
- **Location Integration**: Geocoding and shelter suggestions via OpenStreetMap
- **Multi-Level Fallback**: Stress-aware conversation recovery
- **Human Handoff**: Seamless escalation to emergency services

## 📁 Project Structure

```
crisis_response_system/
├── docker-compose.yml          # Main orchestration
├── docker/                     # Docker configurations
│   ├── Dockerfile.rasa        
│   ├── Dockerfile.actions
│   └── Dockerfile.streamlit
├── rasa_project/              # Rasa chatbot files
│   ├── domain.yml             # Intents, entities, responses
│   ├── nlu.yml               # Training data
│   ├── stories.yml           # Conversation flows
│   ├── rules.yml             # Deterministic behavior
│   ├── config.yml            # ML pipeline config
│   ├── actions.py            # Custom Python actions
│   ├── endpoints.yml         # Service endpoints
│   └── requirements-actions.txt
└── frontend/                  # Streamlit interface
    ├── streamlit_app.py      
    └── requirements-frontend.txt
```

## 🔐 Security Notes

- Services communicate over internal Docker network
- No sensitive data persisted in containers
- Location data processed securely via OpenStreetMap
- No API keys required for basic functionality

## 📈 Performance

- **Training Time**: 1-2 minutes initial startup
- **Response Time**: <500ms for most interactions
- **Memory Usage**: ~2GB total across all services
- **Concurrent Users**: Supports 10+ simultaneous sessions

## 🆘 Emergency Protocols

This system follows professional emergency management standards:
- **Immediate Danger Assessment**: Priority safety evaluation
- **Vulnerability Weighting**: Special consideration for high-risk individuals
- **Risk-Based Response**: Scaled guidance based on threat level
- **Human Escalation**: Automatic handoff for critical situations

## 📞 Real Emergency Disclaimer

**⚠️ IMPORTANT**: This is a training system for educational purposes. 

**For real emergencies, always call:**
- 🇪🇺 **Europe**: 112
- 🇺🇸 **US/Canada**: 911

