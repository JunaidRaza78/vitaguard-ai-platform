# Agentic AI Family Health Manager

> An intelligent, autonomous healthcare management platform with RAG-based medical chatbot for modern families.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.15%2B-008CC1.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

The Agentic AI Family Health Manager is a comprehensive healthcare management system that centralizes medical records, automates health tasks, and provides AI-powered insights through a conversational chatbot interface. Built with a microservices architecture, it leverages Neo4j knowledge graphs, vector databases, and large language models to deliver personalized, intelligent health management.

### Key Features

- **Centralized Health Records**: Consolidate medical records, lab reports, prescriptions, and vaccination history
- **RAG-Based Medical Chatbot**: Natural language interface to query health data and receive medical information
- **Intelligent Medication Management**: Track medications with drug interaction detection and adherence monitoring
- **Automated Scheduling**: Smart appointment booking with calendar integration and reminders
- **AI Health Insights**: Predictive analytics, risk assessment, and personalized recommendations
- **Family-Centric Design**: Manage health data for entire family with relationship modeling
- **HIPAA Compliant**: Enterprise-grade security and privacy protection

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  React.js Web App │ React Native Mobile │ PWA │ Chat Interface  │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                     Kong API Gateway (8000)                      │
│     Authentication │ Rate Limiting │ Load Balancing │ WebSocket │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Microservices Layer                   │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ User Service │ Health Graph │ Document Proc│ Notification (8004)│
│    (8001)    │ Service(8002)│ Service(8003)│                    │
├──────────────┼──────────────┼──────────────┼────────────────────┤
│ Appointment  │ Medication   │ Analytics    │ AI Insights (8008) │
│ Service(8005)│ Service(8006)│ Service(8007)│                    │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│           Medical Chatbot Service (8009) ⭐ NEW                  │
│  RAG Pipeline │ Intent Classification │ Knowledge Retrieval     │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                          Data Layer                              │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Neo4j (7687) │ PostgreSQL   │ MongoDB      │ Redis (6379)       │
│ Knowledge    │ Transactional│ Documents &  │ Cache & Sessions   │
│ Graph        │ Data         │ Chat History │                    │
├──────────────┼──────────────┼──────────────┼────────────────────┤
│ Pinecone/    │ Elasticsearch│ AWS S3       │ RabbitMQ (5672)    │
│ Weaviate     │ Search (9200)│ File Storage │ Message Queue      │
│ Vector DB    │              │              │                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    External Integrations                         │
│  OpenAI GPT-4 │ Anthropic Claude │ Twilio │ SendGrid │ Calendar │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **API Gateway**: Kong 3.4+
- **Message Queue**: RabbitMQ 3.12+

### Databases
- **Neo4j 5.15+**: Knowledge graph for health relationships
- **PostgreSQL 17**: Transactional data and authentication
- **MongoDB 7.0+**: Document storage and chat conversations
- **Redis 7.2+**: Caching, sessions, and conversation memory
- **Pinecone/Weaviate/ chroma**: Vector database for medical knowledge embeddings
- **Elasticsearch 8.x**: Full-text search

### AI/ML Stack
- **LLMs**: OpenAI GPT-4 Turbo, Anthropic Claude 3 Opus deepseek-r1:8b
- **Embeddings**: text-embedding-ada-002 (OpenAI), all-MiniLM-L6-v2
- **Orchestration**: LangChain/LangGraph 0.1+
- **OCR**: Tesseract, Google Vision API
- **Vector Search**: FAISS, HNSW

### Infrastructure
- **Containerization**: Docker 24+
- **Orchestration**: Kubernetes 1.28+
- **Cloud**: AWS (EKS, S3, RDS, ElastiCache)
- **IaC**: Terraform, Ansible
- **CI/CD**: GitHub Actions / GitLab CI
- **Monitoring**: Prometheus, Grafana, ELK Stack

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Neo4j 5.15+
- PostgreSQL 15+
- MongoDB 7.0+
- Redis 7.2+

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/agentic-ai-family-health-manager.git
cd agentic-ai-family-health-manager
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Install dependencies**
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

4. **Start infrastructure services**
```bash
docker-compose up -d neo4j postgres mongodb redis rabbitmq elasticsearch
```

5. **Initialize databases**
```bash
# Run database migrations
python scripts/init_databases.py

# Seed initial data (optional)
python scripts/seed_data.py
```

6. **Start microservices**
```bash
# Option 1: Start all services with Docker Compose
docker-compose up

# Option 2: Start services individually for development
python services/user_service/main.py
python services/health_graph_service/main.py
python services/chatbot_service/main.py
# ... other services
```

7. **Start frontend**
```bash
cd frontend
npm run dev
```

8. **Access the application**
- Web App: http://localhost:3000
- API Gateway: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## Project Structure

```
agentic-ai-family-health-manager/
├── services/
│   ├── user_service/              # Port 8001
│   ├── health_graph_service/      # Port 8002
│   ├── document_processing/       # Port 8003
│   ├── notification_service/      # Port 8004
│   ├── appointment_service/       # Port 8005
│   ├── medication_service/        # Port 8006
│   ├── analytics_service/         # Port 8007
│   ├── ai_insights_service/       # Port 8008
│   └── chatbot_service/           # Port 8009 ⭐
│       ├── app/
│       │   ├── api/
│       │   │   ├── endpoints/
│       │   │   │   ├── chat.py
│       │   │   │   ├── conversations.py
│       │   │   │   └── feedback.py
│       │   │   └── routes.py
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── intents.py
│       │   │   └── prompts.py
│       │   ├── models/
│       │   │   ├── conversation.py
│       │   │   └── message.py
│       │   ├── services/
│       │   │   ├── intent_classifier.py
│       │   │   ├── entity_extractor.py
│       │   │   ├── context_builder.py
│       │   │   ├── retriever.py
│       │   │   ├── generator.py
│       │   │   └── safety_validator.py
│       │   └── utils/
│       ├── tests/
│       ├── requirements.txt
│       └── main.py
├── shared/
│   ├── database/
│   │   ├── neo4j_client.py
│   │   ├── postgres_client.py
│   │   ├── mongo_client.py
│   │   └── redis_client.py
│   ├── models/
│   ├── utils/
│   └── events/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── hooks/
│   └── package.json
├── infrastructure/
│   ├── docker/
│   │   └── docker-compose.yml
│   ├── kubernetes/
│   │   ├── deployments/
│   │   ├── services/
│   │   └── ingress/
│   └── terraform/
├── scripts/
│   ├── init_databases.py
│   ├── seed_data.py
│   └── load_knowledge_base.py
├── docs/
│   ├── api/
│   ├── architecture/
│   └── deployment/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Medical Chatbot Service

The RAG-based medical chatbot is the crown jewel of the system, providing natural language access to health data.

### Capabilities

- **12 Intent Categories**: Query records, explain lab results, medication info, vaccination queries, symptom discussion, treatment precautions, trend analysis, family health, health education, appointments, emergency detection, prescription refills
- **Entity Extraction**: Conditions, medications, tests, body parts, symptoms, time references, family members, vital signs, measurements
- **Dual Retrieval**:
  - Personal health data from Neo4j knowledge graph
  - Medical knowledge from vector database (500K+ documents)
- **Safety Features**: Emergency detection, harmful advice prevention, medical disclaimers, HIPAA compliance
- **Multi-language Support**: English, Spanish (more coming)

### Example Queries

```
User: "What were my cholesterol levels in my last blood test?"
Bot: Retrieves lab results from Neo4j and explains the values with context

User: "What are the side effects of metformin?"
Bot: Searches drug database and provides comprehensive information with citations

User: "Show me my blood pressure trends over the last 6 months"
Bot: Queries time-series data and generates analytical summary with visualization data

User: "Does diabetes run in my family?"
Bot: Traverses family graph relationships and identifies genetic patterns

User: "I have chest pain and shortness of breath"
Bot: Detects emergency symptoms and escalates with emergency contact information
```

### API Endpoints

#### Chat API
```bash
# Send a message
POST /api/v1/chat/message
{
  "conversationId": "optional-uuid",
  "message": "What were my recent lab results?",
  "language": "en",
  "includeHistory": true
}

# Get conversations
GET /api/v1/chat/conversations?userId={userId}&limit=10&offset=0

# Get conversation details
GET /api/v1/chat/conversations/{conversationId}

# Submit feedback
POST /api/v1/chat/feedback
{
  "conversationId": "uuid",
  "messageId": "uuid",
  "rating": "thumbs_up",
  "comment": "Very helpful explanation!"
}
```

## Neo4j Knowledge Graph Schema

### Key Node Types
- **User**: User profiles with demographics
- **Family**: Family groups
- **HealthRecord**: Medical records, lab reports, prescriptions
- **Condition**: Medical conditions with ICD-10 codes
- **Medication**: Drugs with interactions
- **Doctor**: Healthcare providers
- **Hospital**: Medical facilities
- **Appointment**: Scheduled visits
- **VitalSign**: Tracked vitals
- **Conversation**: Chat conversations ⭐
- **ChatMessage**: Individual chat messages ⭐

### Important Relationships
- `MEMBER_OF`: User → Family
- `HAS_RECORD`: User → HealthRecord
- `HAS_CONDITION`: User → Condition
- `TAKES`: User → Medication
- `INTERACTS_WITH`: Medication ↔ Medication
- `SCHEDULED`: User → Appointment
- `HAD_CONVERSATION`: User → Conversation ⭐
- `ASKED_ABOUT`: ChatMessage → HealthRecord ⭐
- `DISCUSSED_MEDICATION`: ChatMessage → Medication ⭐

## Environment Variables

Create a `.env` file with the following variables:

```env
# Application
APP_ENV=development
APP_NAME="Agentic AI Family Health Manager"
SECRET_KEY=your-secret-key-here
DEBUG=true

# API Gateway
API_GATEWAY_URL=http://localhost:8000

# Databases
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=health_manager
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=health_manager

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Vector Database
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=medical-knowledge

# LLM APIs
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Message Queue
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# External Services
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourapp.com

# AWS (if using)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=health-manager-files

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

## Security & Compliance

### HIPAA Compliance
- ✅ Encrypted data at rest (AES-256)
- ✅ Encrypted data in transit (TLS 1.3)
- ✅ Access control and audit logging
- ✅ Business Associate Agreement with OpenAI
- ✅ Data retention policies
- ✅ Breach notification procedures
- ✅ Minimum necessary standard

### Security Features
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Security headers

## Testing

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific service tests
pytest tests/unit/chatbot_service

# Run end-to-end tests
pytest tests/e2e
```

## Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Deploy infrastructure
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/configmaps/
kubectl apply -f infrastructure/kubernetes/secrets/

# Deploy services
kubectl apply -f infrastructure/kubernetes/deployments/
kubectl apply -f infrastructure/kubernetes/services/
kubectl apply -f infrastructure/kubernetes/ingress/

# Check deployment status
kubectl get pods -n health-manager
kubectl get services -n health-manager
```

### Terraform (Cloud Infrastructure)
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Monitoring & Observability

### Metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

### Logging
- **Kibana**: http://localhost:5601
- Centralized logging with ELK stack

### Tracing
- **Jaeger**: http://localhost:16686
- Distributed tracing for all services

### Alerts
- PagerDuty for critical alerts
- Slack for warnings
- Email for daily summaries

## Performance

### Target Metrics
- **API Response Time**: <200ms (p95)
- **Chatbot Response**: <3s end-to-end
- **Database Queries**: <50ms (Neo4j), <100ms (Postgres)
- **Vector Search**: <100ms
- **Throughput**: 100+ messages/second
- **Concurrent Users**: 1000+
- **Uptime**: 99.9%

### Optimization Strategies
- Redis caching (80%+ hit rate target)
- Database connection pooling
- Query optimization and indexing
- Horizontal pod autoscaling
- CDN for static assets
- Response streaming for chatbot

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Write unit tests for new features
- Update documentation
- Add type hints
- Run linters (`black`, `flake8`, `mypy`)
