pip install -r requirements.txt



pip install fastapi uvicorn[standard] pydantic python-multipart



python app.py

http://localhost:8000

http://localhost:8000/api/v1/docs


{
  "image_urls": [
    "https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif",
    "https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180758_07_2508_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif"
  ],
  "field_name": "Field_Test",
  "crop_config": {
    "cropType": "sugarBeet",
    "region": "CA_Desert_USA",
    "plantingMonth": "march",
    "soilType": "loam",
    "plantingDate": "2025-03-28",
    "firstIrrigDate": "2025-06-13",
    "lastIrrigDate": "2025-09-09",
    "irrigDepth": 25.4,
    "mad": 0.4,
    "irrEfficiency": 0.85,
    "maxIrrig": 50.8
  }
}










# Agroptics Processing API

RESTful API for satellite image processing and irrigation calculations.

## Overview

This API exposes the Agroptics reference code as REST endpoints, allowing backend teams to integrate satellite image processing into their applications without dealing with Python code directly.

## Features

- **Calculate Vegetation Indices** from satellite image URLs
- **Generate Time Series Statistics** from multiple images
- **Calculate Water Balance** parameters (FAO-56 model)
- **Complete Pipeline Processing** in a single API call
- **Auto-generated Documentation** (Swagger UI)
- **Request/Response Validation** (Pydantic)
- **CORS Support** for frontend integration

## Quick Start

### 1. Install Dependencies

```bash
cd "AA GT Restructured files/api"
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python app.py
```

Or with uvicorn directly:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

- **API Base URL:** `http://localhost:8000`
- **Interactive Docs:** `http://localhost:8000/api/v1/docs`
- **Alternative Docs:** `http://localhost:8000/api/v1/redoc`
- **Health Check:** `http://localhost:8000/api/v1/health`

## API Endpoints

### 1. Health Check

**GET** `/api/v1/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-04-29T10:30:00"
}
```

---

### 2. Calculate Vegetation Indices

**POST** `/api/v1/process/indices`

Calculate 6 vegetation indices from a satellite image URL.

**Request Body:**
```json
{
  "image_url": "https://example.com/image.tif",
  "field_name": "Field_10"
}
```

**Response:**
```json
{
  "success": true,
  "field_name": "Field_10",
  "date": "2025-03-29",
  "unique_id": "20250329_180511_67_2516",
  "indices": {
    "NDVI": {
      "mean": 0.2018,
      "min": 0.1095,
      "max": 0.2884,
      "std": 0.0236,
      "p25": 0.1872,
      "p50": 0.2008,
      "p75": 0.2152,
      "count": 3444
    },
    "SAVI": {...},
    "FC": {...},
    "GCI": {...},
    "RECI": {...},
    "MSAVI": {...}
  },
  "processing_time_seconds": 2.5
}
```

**Indices Calculated:**
- **NDVI**: Normalized Difference Vegetation Index
- **SAVI**: Soil Adjusted Vegetation Index
- **FC**: Fractional Cover
- **GCI**: Green Chlorophyll Index
- **RECI**: Red Edge Chlorophyll Index
- **MSAVI**: Modified Soil Adjusted Vegetation Index

---

### 3. Calculate Water Balance

**POST** `/api/v1/process/water-balance`

Calculate water balance parameters from vegetation indices.

**Request Body:**
```json
{
  "field_name": "Field_10",
  "indices": {
    "NDVI": 0.2018,
    "SAVI": 0.2156,
    "FC": 0.0763
  },
  "date": "2025-03-29",
  "crop_config": {
    "cropType": "sugarBeet",
    "region": "CA_Desert_USA",
    "plantingMonth": "march",
    "soilType": "loam",
    "plantingDate": "2025-03-28",
    "mad": 0.4,
    "irrigDepth": 25.4
  }
}
```

**Response:**
```json
{
  "success": true,
  "field_name": "Field_10",
  "date": "2025-03-29",
  "water_balance": {
    "Date": "2025-03-29",
    "DaysSincePlanting": 1,
    "ETo": 3.5,
    "ETr": 5.0,
    "Kcb_Andy": 0.286,
    "Kcb_NDVI": 0.212,
    "Kcb_SAVI": 0.322,
    "Kcb_FC": 0.168,
    "Kcb_Ensemble": 0.222,
    "Kcb_FAO56": 0.35,
    "ETc_Andy": 1.43,
    "ETc_NDVI": 1.06,
    "ETc_SAVI": 1.61,
    "ETc_FC": 0.84,
    "ETc_Ensemble": 1.11,
    "ETc_FAO56": 1.75,
    "AWC": 10.4,
    "TAW": 26.0,
    "RootDepth_m": 0.2
  },
  "processing_time_seconds": 0.1
}
```

**Water Balance Parameters:**
- **ETo, ETr**: Reference evapotranspiration (mm/day)
- **Kcb**: Basal crop coefficient (6 methods)
- **ETc**: Crop evapotranspiration (mm/day, 6 methods)
- **AWC**: Available Water Content (mm)
- **TAW**: Total Available Water (mm)
- **Dr**: Root zone depletion (mm)
- **fDr**: Fraction of depletion (0-1)

---

### 4. Complete Pipeline Processing

**POST** `/api/v1/process/complete`

Process multiple images through the complete pipeline.

**Request Body:**
```json
{
  "image_urls": [
    "https://example.com/image1.tif",
    "https://example.com/image2.tif"
  ],
  "field_name": "Field_10",
  "crop_config": {
    "cropType": "sugarBeet",
    "region": "CA_Desert_USA",
    "plantingMonth": "march",
    "soilType": "loam",
    "plantingDate": "2025-03-28",
    "firstIrrigDate": "2025-06-13",
    "lastIrrigDate": "2025-09-09",
    "irrigDepth": 25.4,
    "mad": 0.4,
    "irrEfficiency": 0.85,
    "maxIrrig": 50.8
  }
}
```

**Response:**
```json
{
  "success": true,
  "field_name": "Field_10",
  "total_images": 2,
  "processed_images": 2,
  "dates": ["2025-03-29", "2025-03-29"],
  "timeseries": [{
    "fieldName": "Field_10",
    "timeSeries": [
      {
        "date": "2025-03-29",
        "unique_id": "20250329_180511_67_2516",
        "indices": {...}
      },
      ...
    ]
  }],
  "water_balance": [
    {
      "Date": "2025-03-29",
      "UniqueID": "20250329_180511_67_2516",
      "Kcb_Ensemble": 0.286,
      "ETc_Ensemble": 1.43,
      ...
    },
    ...
  ],
  "processing_time_seconds": 5.2
}
```

---

## Usage Examples

### Python

```python
import requests

# Calculate indices
response = requests.post(
    "http://localhost:8000/api/v1/process/indices",
    json={
        "image_url": "https://example.com/image.tif",
        "field_name": "Field_10"
    }
)

result = response.json()
print(f"NDVI mean: {result['indices']['NDVI']['mean']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

async function calculateIndices() {
  const response = await axios.post(
    'http://localhost:8000/api/v1/process/indices',
    {
      image_url: 'https://example.com/image.tif',
      field_name: 'Field_10'
    }
  );
  
  console.log('NDVI mean:', response.data.indices.NDVI.mean);
}
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/process/indices" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.tif",
    "field_name": "Field_10"
  }'
```

---

## Deployment Options

### Option 1: AWS Lambda (Serverless)

**Pros:**
- Pay per request
- Auto-scaling
- No server management

**Cons:**
- Cold start latency
- 15-minute timeout limit
- Complex setup for large dependencies

**Setup:**
1. Use AWS SAM or Serverless Framework
2. Package with Lambda layers for rasterio
3. Configure API Gateway

**Cost:** ~$0.20 per 1M requests (free tier: 1M requests/month)

---

### Option 2: Google Cloud Run (Serverless Containers)

**Pros:**
- Container-based (easy deployment)
- Auto-scaling
- Pay per use
- No cold start issues with min instances

**Cons:**
- Requires Docker knowledge
- Can be expensive with high traffic

**Setup:**
```bash
# 1. Create Dockerfile
# 2. Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/agroptics-api

# 3. Deploy to Cloud Run
gcloud run deploy agroptics-api \
  --image gcr.io/PROJECT_ID/agroptics-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Cost:** ~$0.40 per 1M requests (free tier: 2M requests/month)

---

### Option 3: Railway.app (Easiest)

**Pros:**
- Extremely easy deployment
- Free tier available
- GitHub integration
- Automatic HTTPS

**Cons:**
- Limited free tier ($5/month credit)
- Less control than AWS/GCP

**Setup:**
1. Push code to GitHub
2. Connect Railway to your repo
3. Railway auto-detects Python and deploys
4. Get public URL instantly

**Cost:** Free tier ($5 credit/month), then $0.000463/GB-hour

---

### Option 4: Heroku (Simple)

**Pros:**
- Very easy deployment
- Good documentation
- Add-ons ecosystem

**Cons:**
- No free tier anymore
- More expensive than alternatives

**Setup:**
```bash
# 1. Create Procfile
echo "web: uvicorn app:app --host 0.0.0.0 --port \$PORT" > Procfile

# 2. Deploy
heroku create agroptics-api
git push heroku main
```

**Cost:** $7/month (Eco dyno)

---

### Option 5: DigitalOcean App Platform

**Pros:**
- Simple deployment
- Predictable pricing
- Good performance

**Cons:**
- Not serverless (always running)
- Minimum $5/month

**Setup:**
1. Connect GitHub repo
2. Configure build settings
3. Deploy

**Cost:** $5-12/month

---

### Option 6: Fly.io (Recommended for Production)

**Pros:**
- Global edge deployment
- Free tier (3 shared VMs)
- Docker-based
- Fast performance

**Cons:**
- Requires Docker
- Learning curve

**Setup:**
```bash
# 1. Install flyctl
# 2. Initialize
flyctl launch

# 3. Deploy
flyctl deploy
```

**Cost:** Free tier (3 shared VMs), then $1.94/month per VM

---

## Recommended Deployment

### For Testing/Development:
**Railway.app** - Easiest, free tier, instant deployment

### For Production:
**Google Cloud Run** - Scalable, cost-effective, container-based

### For High Traffic:
**AWS Lambda + API Gateway** - Most cost-effective at scale

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for rasterio
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build
docker build -t agroptics-api .

# Run
docker run -p 8000:8000 agroptics-api
```

---

## Environment Variables

For production, configure these environment variables:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS (comma-separated origins)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Logging
LOG_LEVEL=info

# Optional: Weather API keys (for real ETr data)
WEATHER_API_KEY=your_key_here
```

---

## Performance Considerations

### Image Processing Time

- Single image (indices): ~2-5 seconds
- Complete pipeline (2 images): ~5-10 seconds
- Bottleneck: Image download from URL

### Optimization Tips

1. **Use CDN for images** - Faster downloads
2. **Cache processed results** - Avoid reprocessing
3. **Async processing** - Use background tasks for large batches
4. **Horizontal scaling** - Deploy multiple instances

---

## Security

### Production Checklist

- [ ] Configure CORS properly (don't use `allow_origins=["*"]`)
- [ ] Add API key authentication
- [ ] Rate limiting (use middleware)
- [ ] Input validation (already done with Pydantic)
- [ ] HTTPS only
- [ ] Monitor for abuse

### Add API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "your-secret-api-key"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Add to endpoints
@app.post("/api/v1/process/indices", dependencies=[Depends(verify_api_key)])
async def calculate_indices_from_url(request: IndicesRequest):
    ...
```

---

## Monitoring

### Health Check Endpoint

Use `/api/v1/health` for:
- Load balancer health checks
- Uptime monitoring (UptimeRobot, Pingdom)
- CI/CD deployment verification

### Logging

FastAPI automatically logs requests. For production:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## Testing

### Manual Testing

Use the interactive docs at `/api/v1/docs` to test endpoints directly in your browser.

### Automated Testing

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_calculate_indices():
    response = client.post(
        "/api/v1/process/indices",
        json={
            "image_url": "https://example.com/image.tif",
            "field_name": "Test"
        }
    )
    assert response.status_code == 200
```

---

## Support

For questions or issues:
1. Check the interactive docs at `/api/v1/docs`
2. Review the reference code in `../reference code/`
3. Check the main README at `../README.md`

---

## License

Same as the main Agroptics project.
