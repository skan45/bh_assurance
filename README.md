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
git clone https://github.com/skan45/bh_assurance.git
cd bh_assurance
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

## Software Architecture

The BH Assurance chatbot follows a microservices architecture containerized with Docker, ensuring scalability, maintainability, and efficient resource management.

### System Components

#### Core Services

**Application Service (app)**
- **Framework**: FastAPI with Gunicorn and Uvicorn workers
- **Purpose**: Main backend application handling API requests and business logic
- **Resources**: 2 CPU cores, 2GB RAM
- **Port**: 8000 (HTTP API)
- **Workers**: 2 Gunicorn workers for handling concurrent requests

**PostgreSQL Database**
- **Version**: PostgreSQL 15
- **Purpose**: Stores user accounts, session data, and relational information
- **Resources**: 2 CPU cores, 2GB RAM
- **Port**: 5432
- **Persistence**: Persistent volume for data storage

**Redis Cache**
- **Version**: Redis 7 Alpine
- **Purpose**: Session management, caching, and real-time data storage
- **Resources**: 1 CPU core, 1GB RAM
- **Port**: 6379
- **Configuration**: Auto-save every 60 seconds

**Neo4j Graph Database**
- **Version**: Neo4j 5.25.1
- **Purpose**: Knowledge graph for insurance contracts, claims, and client relationships
- **Resources**: 2 CPU cores, 4GB RAM
- **Ports**: 7687 (Bolt), 7474 (HTTP)
- **Health Check**: Cypher query validation

**Qdrant Vector Database**
- **Version**: Latest
- **Purpose**: Vector storage for semantic search and document embeddings
- **Resources**: 2 CPU cores, 4GB RAM
- **Ports**: 6333 (HTTP), 6334 (gRPC)
- **Storage**: Persistent vector storage

#### Docker Compose Configuration

```yaml
services:
  # Backend Application
  app:
    build: .
    container_name: app
    env_file: .env
    ports: ["8000:8000"]
    depends_on:
      neo4j2: {condition: service_healthy}
      postgres: {condition: service_started}
      redis: {condition: service_started}
      qdrant: {condition: service_started}
    networks: [backend]
    command: gunicorn -k uvicorn.workers.UvicornWorker app:app
    deploy:
      resources:
        limits: {cpus: '2', memory: 2G}

  # PostgreSQL Database
  postgres:
    image: postgres:15
    container_name: bh_postgres2
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    deploy:
      resources:
        limits: {cpus: '2', memory: 2G}

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: ["redis-server", "--save", "60", "1"]
    deploy:
      resources:
        limits: {cpus: '1', memory: 1G}

  # Neo4j Graph Database
  neo4j2:
    image: neo4j:5.25.1
    ports: ["7687:7687", "7474:7474"]
    environment: [NEO4J_AUTH=neo4j/azerty2002]
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p azerty2002 'RETURN 1'"]
    deploy:
      resources:
        limits: {cpus: '2', memory: 4G}

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333", "6334:6334"]
    volumes: [qdrant_data:/qdrant/storage]
    deploy:
      resources:
        limits: {cpus: '2', memory: 4G}
```

### Network Architecture

- **Backend Network**: Isolated bridge network for secure inter-service communication
- **Service Dependencies**: App service depends on all databases being healthy/started
- **Volume Persistence**: Dedicated volumes for each database ensuring data persistence

### Resource Allocation

- **Total CPU Requirements**: 9 cores across all services
- **Total Memory Requirements**: 12GB RAM
- **Storage**: Persistent volumes for databases
- **Network**: Internal Docker bridge network for service communication

<img width="792" height="679" alt="software architecture" src="https://github.com/user-attachments/assets/698a6e4a-1021-4aa4-b237-ed19ec83a41e" />


## Qdrant Agent - RAG (Retrieval-Augmented Generation)

The Qdrant agent implements a sophisticated RAG technique for semantic search and document retrieval, serving both existing clients and prospects.

### RAG Architecture

#### 1. Document Processing Pipeline
- **Ingestion**: PDF documents (contracts, policies, product catalogs) are processed
- **Text Extraction**: Content extraction with metadata preservation
- **Chunking**: Documents split into semantic chunks for optimal embedding
- **Vectorization**: Text chunks converted to high-dimensional vectors using sentence transformers

#### 2. Vector Storage Strategy
- **Collections**: Separate collections for different document types
- **Embeddings**: 384-dimensional vectors (sentence-transformers/all-MiniLM-L6-v2)
- **Metadata**: Rich metadata including document type, client access levels, content categories
- **Indexing**: HNSW (Hierarchical Navigable Small World) for fast similarity search

#### 3. Retrieval Process
1. **Query Vectorization**: User query converted to embedding vector
2. **Similarity Search**: Cosine similarity search across document collections
3. **Filtering**: Security filters applied based on user type (client/prospect)
4. **Ranking**: Results ranked by relevance score and metadata importance
5. **Context Assembly**: Top-k results assembled for generation context

#### 4. Generation Enhancement
- **Context Injection**: Retrieved documents injected into LLM context
- **Source Attribution**: Generated responses include source document references
- **Factual Grounding**: Ensures responses are grounded in actual insurance documents

### Use Cases
- **Product Discovery**: Prospects search for insurance products and services
- **Policy Information**: Clients access detailed policy documentation
- **Claims Guidance**: Document-based assistance for claims processes
- **FAQ Resolution**: Automated responses based on insurance documentation

<img width="1026" height="593" alt="qdrant-agent" src="https://github.com/user-attachments/assets/69b9a8a8-1e3c-4c10-b478-1ce2b5a6d05b" />


## Neo4j Agent - Knowledge Graph Intelligence

The Neo4j agent leverages knowledge graph technology to provide intelligent responses about insurance relationships, contracts, and client-specific data.

### Knowledge Graph Architecture

#### 1. Graph Schema Design
<img width="950" height="661" alt="neo4j schema" src="https://github.com/user-attachments/assets/0f26f000-b25c-4e7d-8989-7e4fc8119b06" />


#### 2. AI-Powered Cypher Generation
- **Natural Language Processing**: User queries analyzed for intent and entities
- **OpenAI Integration**: GPT models generate appropriate Cypher queries
- **Query Validation**: Generated queries validated for syntax and security
- **Parameter Binding**: User-specific parameters safely bound to queries

#### 3. Query Execution Pipeline
1. **Intent Recognition**: Classify user query type (contract, claim, coverage, etc.)
2. **Entity Extraction**: Identify relevant entities (client ID, contract number, dates)
3. **Cypher Generation**: AI model generates appropriate Cypher query
4. **Security Check**: Query validated against access permissions
5. **Execution**: Query executed against Neo4j database
6. **Result Processing**: Raw graph data processed for response formatting

#### 4. Response Formulation
- **AI Enhancement**: Raw Neo4j results processed through AI for natural language response
- **Context Integration**: Graph relationships provide rich context for responses
- **Personalization**: Responses tailored to specific client relationships and history

### Security and Data Isolation

#### Client Data Protection
- **Strict Access Control**: Neo4j agent exclusively serves **authenticated BH Assurance clients**
- **Query Filtering**: All Cypher queries include client-specific WHERE clauses
- **Data Isolation**: Client data completely isolated through graph security patterns
- **No Cross-Client Access**: Impossible for one client to access another's data

#### Backend Intelligence
The backend application implements sophisticated routing logic:
- **User Classification**: Automatically identifies clients vs. prospects
- **Agent Selection**: Routes queries to appropriate agent (Neo4j for clients, Qdrant for prospects/general)
- **Data Leak Prevention**: Multiple security layers prevent unauthorized data exposure
- **Session Management**: Maintains secure sessions with proper access controls

<img width="1293" height="663" alt="neo4j-agent" src="https://github.com/user-attachments/assets/d1d533c6-98e9-485a-a051-0ab6be0f0ce9" />


### Agent Coordination

The system ensures seamless operation through:
- **Smart Routing**: Backend determines appropriate agent based on user type and query context
- **Data Sovereignty**: Clear boundaries between client-specific and public information
- **Response Consistency**: Both agents maintain consistent response formatting and quality
- **Security First**: Multi-layered security prevents any data leakage between user types
