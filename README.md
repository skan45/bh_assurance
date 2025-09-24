# BH Assurance Chatbot

## Project Overview

This project presents the design and development of an intelligent chatbot for BH Assurance, providing clients with simplified access to their insurance contracts and claims declarations, while enabling non-clients to discover available insurance offerings.

### Objectives

The chatbot aims to:
- **Enhance Customer Experience**: Provide 24/7 access to insurance information through natural language interactions
- **Streamline Contract Management**: Allow clients to easily query and retrieve their contract details
- **Simplify Claims Processing**: Enable clients to check claim status and submit new claims through conversational interface
- **Drive Business Growth**: Help prospects explore insurance products and services to generate new leads
- **Reduce Support Costs**: Automate common inquiries to reduce workload on customer service teams

### Target Users

#### Existing Clients
- Access personal insurance contracts
- Check policy details and coverage information
- View and track claims status
- Update personal information
- Request policy modifications

#### Prospects (Non-clients)
- Explore available insurance products
- Get personalized insurance recommendations
- Request quotes and information
- Schedule consultations with agents
- Learn about BH Assurance services

### Key Features

- **Natural Language Processing**: Understands and responds to queries in natural French language
- **Multi-modal Interaction**: Handles both text-based conversations and document analysis
- **Personalized Responses**: Provides tailored information based on user profile and history
- **Secure Data Access**: Ensures protected access to sensitive insurance information
- **Real-time Processing**: Delivers instant responses powered by advanced AI agents
- **Context Awareness**: Maintains conversation context for coherent multi-turn interactions

## System Requirements

### Hardware Requirements
- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4 CPU cores, 8GB RAM, 20GB free disk space
- **Storage**: At least 10GB for Docker images and data

### Software Prerequisites
- Docker and Docker Compose (latest version)
- Python 3.8 or higher
- Git for version control
- Bash shell environment (Linux/macOS/WSL)

## Project Setup and Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd bh-assurance-chatbot
```

### 2. Automated Setup Script

The project includes an automated setup script (`script.sh`) that handles the complete installation and data loading process:

```bash
#!/bin/bash
set -e

# Start Docker services
sudo docker compose up -d --build

# Activate Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run pre-KG scripts
python3 process_PDF/load_to_qdrant.py
python3 KG/create_KG.py
python3 KG/enhance_KG.py
python3 KG/add_mapping.py

# Run migration with retry
python3 database/migrate_db.py
```

### 3. Running the Setup

Make the script executable and run it:

```bash
# Make script executable
chmod +x script.sh

# Run the complete setup
./script.sh
```

### 4. Setup Process Overview

The automated script performs the following operations:

1. **Docker Services Initialization**
   - Builds and starts all required containers (Neo4j, Qdrant, PostgreSQL, etc.)
   - Sets up network configuration and volumes

2. **Python Environment Setup**
   - Creates a virtual environment
   - Installs all required Python dependencies from `requirements.txt`

3. **Data Processing Pipeline**
   - `load_to_qdrant.py`: Processes PDF documents and loads embeddings into Qdrant vector database
   - `create_KG.py`: Builds the initial knowledge graph in Neo4j
   - `enhance_KG.py`: Enriches the knowledge graph with additional relationships and properties
   - `add_mapping.py`: Creates mappings between different data sources

4. **Database Migration**
   - `migrate_db.py`: Sets up the relational database schema and initial data

### 5. Verification

After successful installation, verify the setup:

```bash
# Check Docker containers status
sudo docker compose ps

# Verify Neo4j is running
curl http://localhost:7474

# Verify Qdrant is accessible
curl http://localhost:6333/collections

# Check application logs
sudo docker compose logs -f
```

### 6. Troubleshooting

**Common Issues:**

- **Insufficient Resources**: Ensure your system meets the minimum hardware requirements
- **Port Conflicts**: Make sure ports 7474, 6333, 5432, and 8000 are available
- **Permission Issues**: Run Docker commands with appropriate permissions (sudo if required)
- **Network Issues**: Check internet connectivity for downloading Docker images and Python packages

**Debug Mode:**

```bash
# Run with verbose output
bash -x script.sh

# Check individual container logs
sudo docker compose logs <service-name>
```
