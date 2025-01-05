# Aiquisition

A data-driven platform that helps investors identify potential acquisition targets by analyzing GitHub repositories, customer reviews, and marketing efficiency metrics. The platform finds undervalued companies by identifying those with high NPS scores but inefficient marketing spend.

## Features

- GitHub repository analysis (stars, forks, commit frequency, contributor growth)
- Customer satisfaction tracking (NPS scores, review sentiment)
- Marketing efficiency analysis
- Automated scoring system for acquisition potential
- Real-time monitoring and alerts
- RESTful API for data access

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- PostgreSQL 13+
- API Keys for:
  - GitHub
  - SEMrush
  - SimilarWeb

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/yourusername/acquisition-platform.git
cd acquisition-platform
```

2. Create and configure environment variables:

```bash
cp .env.example .env

# Edit .env file with your API keys:
GITHUB_TOKEN=your_github_token
SEMRUSH_API_KEY=your_semrush_key
SIMILARWEB_API_KEY=your_similarweb_key
DATABASE_URL=postgresql://user:password@db:5432/acquisition_db
REDIS_URL=redis://redis:6379
```

3. Build and start the services:

```bash
docker-compose build
docker-compose up -d
```

4. Run database migrations:

```bash
docker-compose exec api alembic upgrade head
```

5. Access the API at `http://localhost:8000`

## API Documentation

### Authentication

All API endpoints require an API key to be included in the header:

```bash
Authorization: Bearer your_api_key
```

### Endpoints

#### Add Company to Track

```bash
POST /companies/

Request Body:
{
    "name": "CompanyName",
    "github_url": "https://github.com/company/repo",
    "website": "https://company.com"
}

Response:
{
    "id": 1,
    "name": "CompanyName",
    "github_url": "https://github.com/company/repo",
    "website": "https://company.com",
    "created_at": "2024-01-06T12:00:00Z",
    "updated_at": "2024-01-06T12:00:00Z",
    "acquisition_score": 0
}
```

#### Get Company Details

```bash
GET /companies/{company_id}

Response:
{
    "id": 1,
    "name": "CompanyName",
    "github_metrics": {
        "stars": 2500,
        "forks": 450,
        "contributors": 35,
        "commit_frequency": 85,
        "issue_response_time": 12
    },
    "review_metrics": {
        "nps_score": 82,
        "review_count": 150,
        "average_rating": 4.8,
        "sentiment_score": 85
    },
    "marketing_metrics": {
        "estimated_spend": 15000,
        "channels": {
            "organic": {"traffic": 50000},
            "paid": {"traffic": 10000}
        },
        "efficiency_score": 75
    }
}
```

#### List Companies

```bash
GET /companies/?min_score=70&skip=0&limit=10

Response:
{
    "total": 45,
    "items": [
        {
            "id": 1,
            "name": "CompanyName",
            "acquisition_score": 85,
            ...
        },
        ...
    ]
}
```

## Monitoring

Access monitoring dashboards:

- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

Default credentials for Grafana:

- Username: admin
- Password: admin

## Development

### Running Tests

```bash
# Run all tests
docker-compose exec api pytest

# Run specific test file
docker-compose exec api pytest tests/test_collectors.py

# Run with coverage report
docker-compose exec api pytest --cov=app
```

## Production Deployment

### AWS Deployment

1. Use AWS ECS for container orchestration
2. Set up Auto Scaling groups
3. Use RDS for PostgreSQL
4. Configure CloudWatch for monitoring

Example AWS CLI commands:

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name acquisition-platform

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service --cluster acquisition-platform --service-name api --task-definition api:1
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
