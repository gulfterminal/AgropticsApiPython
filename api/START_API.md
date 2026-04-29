# Quick Start Guide

## Step 1: Start the API Server

Open a terminal in the `api` folder and run:

```bash
python app.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 2: Test the API

Open your browser and go to:
- **Interactive Docs:** http://localhost:8000/api/v1/docs
- **Health Check:** http://localhost:8000/api/v1/health

## Step 3: Try Your First Request

### Option A: Use the Interactive Docs (Easiest)

1. Go to http://localhost:8000/api/v1/docs
2. Click on "POST /api/v1/process/indices"
3. Click "Try it out"
4. Use this example:

```json
{
  "image_url": "https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif",
  "field_name": "Field_Test"
}
```

5. Click "Execute"
6. See the results!

### Option B: Use cURL (Command Line)

```bash
curl -X POST "http://localhost:8000/api/v1/process/indices" ^
  -H "Content-Type: application/json" ^
  -d "{\"image_url\": \"https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif\", \"field_name\": \"Field_Test\"}"
```

### Option C: Use Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/process/indices",
    json={
        "image_url": "https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif",
        "field_name": "Field_Test"
    }
)

print(response.json())
```

## Expected Response

```json
{
  "success": true,
  "field_name": "Field_Test",
  "date": "2025-03-29",
  "unique_id": "20250329_180511_67_2516",
  "indices": {
    "NDVI": {
      "mean": 0.2018,
      "min": 0.1095,
      "max": 0.2884,
      ...
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

## Troubleshooting

### Error: "Address already in use"
Another process is using port 8000. Change the port:
```bash
python app.py --port 8001
```

### Error: "Module not found"
Make sure you're in the correct directory:
```bash
cd "AA GT Restructured files/api"
python app.py
```

### Error: "Cannot import calculate_indices"
The API needs access to the reference code. Make sure the folder structure is:
```
AA GT Restructured files/
├── api/
│   └── app.py
└── reference code/
    ├── calculate_indices.py
    ├── generate_timeseries.py
    └── calculate_water_balance.py
```
