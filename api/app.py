"""
Agroptics Processing API
========================
RESTful API for satellite image processing and irrigation calculations.

This API exposes the reference code functionality as REST endpoints,
allowing backend teams to integrate satellite image processing into their applications.

Tech Stack:
- FastAPI (modern, fast, auto-documented)
- Pydantic (request/response validation)
- Async support for better performance

Endpoints:
1. POST /api/v1/process/indices - Calculate vegetation indices from TIF URL
2. POST /api/v1/process/timeseries - Generate time series from multiple images
3. POST /api/v1/process/water-balance - Calculate water balance parameters
4. POST /api/v1/process/complete - Run complete pipeline (all steps)
5. GET /api/v1/health - Health check
6. GET /api/v1/docs - API documentation (auto-generated)
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import traceback

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field, validator
import uvicorn

# Add parent directory to path to import reference code modules
sys.path.insert(0, str(Path(__file__).parent.parent / "reference code"))

from calculate_indices import load_planet_image, calculate_all_indices, export_index_geotiff
from generate_timeseries import calculate_statistics
from calculate_water_balance import (
    load_crop_parameters,
    calculate_kcb_andy, calculate_kcb_ndvi, calculate_kcb_savi,
    calculate_kcb_fc, calculate_kcb_ensemble, calculate_kcb_fao56,
    calculate_root_depth, calculate_taw, calculate_awc
)

# Initialize FastAPI app
app = FastAPI(
    title="Agroptics Processing API",
    description="Satellite image processing and irrigation calculations API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class IndicesRequest(BaseModel):
    """Request model for calculating vegetation indices"""
    image_url: HttpUrl = Field(..., description="URL to Planet 8-band GeoTIFF image")
    field_name: Optional[str] = Field("field", description="Field identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "image_url": "https://example.com/image.tif",
                "field_name": "Field_10"
            }
        }


class BatchIndicesRequest(BaseModel):
    """Request model for calculating indices from multiple URLs"""
    image_urls: List[HttpUrl] = Field(..., description="List of image URLs to process")
    field_name: Optional[str] = Field("field", description="Field identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "image_urls": [
                    "https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif",
                    "https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180758_07_2508_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif"
                ],
                "field_name": "Field_Test"
            }
        }


class BatchIndicesResponse(BaseModel):
    """Response model for batch indices processing"""
    success: bool
    field_name: str
    total_images: int
    processed_images: int
    failed_images: int
    results: List[Dict[str, Any]]
    processing_time_seconds: float


class IndicesResponse(BaseModel):
    """Response model for vegetation indices"""
    success: bool
    field_name: str
    date: str
    unique_id: str
    indices: Dict[str, Dict[str, float]] = Field(..., description="Statistics for each index")
    processing_time_seconds: float
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
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
                    }
                },
                "processing_time_seconds": 2.5
            }
        }


class WaterBalanceRequest(BaseModel):
    """Request model for water balance calculation"""
    field_name: str = Field(..., description="Field identifier")
    indices: Dict[str, float] = Field(..., description="Mean values for NDVI, SAVI, FC")
    date: str = Field(..., description="Image date (YYYY-MM-DD)")
    crop_config: Dict[str, Any] = Field(..., description="Crop configuration")
    
    @validator('indices')
    def validate_indices(cls, v):
        required = ['NDVI', 'SAVI', 'FC']
        for idx in required:
            if idx not in v:
                raise ValueError(f"Missing required index: {idx}")
        return v
    
    @validator('crop_config')
    def validate_crop_config(cls, v):
        required = ['cropType', 'region', 'plantingMonth', 'soilType', 'plantingDate', 'mad', 'irrigDepth']
        for field in required:
            if field not in v:
                raise ValueError(f"Missing required field: {field}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
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
        }


class WaterBalanceResponse(BaseModel):
    """Response model for water balance"""
    success: bool
    field_name: str
    date: str
    water_balance: Dict[str, Any]
    processing_time_seconds: float


class CompleteProcessRequest(BaseModel):
    """Request model for complete pipeline processing"""
    image_urls: List[HttpUrl] = Field(..., description="List of image URLs to process")
    field_name: str = Field(..., description="Field identifier")
    crop_config: Dict[str, Any] = Field(..., description="Crop configuration")
    
    class Config:
        schema_extra = {
            "example": {
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
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def download_image(url: str, output_path: Path) -> bool:
    """Download image from URL"""
    import requests
    try:
        response = requests.get(str(url), stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def extract_info_from_url(url: str) -> tuple:
    """Extract date and unique ID from Planet filename in URL"""
    filename = url.split('/')[-1]
    parts = filename.split('_')
    if len(parts) >= 4:
        date_str = parts[0]
        unique_id = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return formatted_date, unique_id, filename
    return None, None, filename


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns API status and version information.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/process/indices", response_model=IndicesResponse)
async def calculate_indices_from_url(request: IndicesRequest):
    """
    Calculate vegetation indices from a satellite image URL
    
    This endpoint:
    1. Downloads the image from the provided URL
    2. Calculates 6 vegetation indices (NDVI, SAVI, FC, GCI, RECI, MSAVI)
    3. Returns statistics for each index
    
    **Indices Calculated:**
    - NDVI: Normalized Difference Vegetation Index
    - SAVI: Soil Adjusted Vegetation Index
    - FC: Fractional Cover
    - GCI: Green Chlorophyll Index
    - RECI: Red Edge Chlorophyll Index
    - MSAVI: Modified Soil Adjusted Vegetation Index
    
    **Statistics Returned:**
    - mean, min, max, std (standard deviation)
    - p25, p50, p75 (25th, 50th, 75th percentiles)
    - count (number of valid pixels)
    """
    start_time = datetime.now()
    temp_dir = None
    
    try:
        # Extract info from URL
        date, unique_id, filename = extract_info_from_url(str(request.image_url))
        if not date or not unique_id:
            raise HTTPException(status_code=400, detail="Invalid filename format in URL")
        
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        image_path = temp_dir / filename
        
        # Download image
        if not download_image(str(request.image_url), image_path):
            raise HTTPException(status_code=400, detail="Failed to download image from URL")
        
        # Load and process image
        bands_data = load_planet_image(str(image_path))
        indices = calculate_all_indices(bands_data)
        
        # Calculate statistics for each index
        indices_stats = {}
        for index_name, index_array in indices.items():
            stats = calculate_statistics(index_array)
            indices_stats[index_name] = stats
        
        # Calculate processing time
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "field_name": request.field_name,
            "date": date,
            "unique_id": unique_id,
            "indices": indices_stats,
            "processing_time_seconds": round(elapsed, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Cleanup temporary files
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/v1/process/indices/batch", response_model=BatchIndicesResponse)
async def calculate_indices_from_multiple_urls(request: BatchIndicesRequest):
    """
    Calculate vegetation indices from multiple satellite image URLs
    
    This endpoint processes multiple images in parallel and returns results for all.
    Perfect for processing a time series of images at once.
    
    **Use this when:**
    - You have multiple images to process
    - You want to process a time series
    - You want faster batch processing
    
    **Response includes:**
    - Individual results for each image
    - Success/failure count
    - Total processing time
    """
    start_time = datetime.now()
    
    results = []
    failed_count = 0
    
    for url in request.image_urls:
        temp_dir = None
        try:
            # Extract info from URL
            date, unique_id, filename = extract_info_from_url(str(url))
            if not date or not unique_id:
                failed_count += 1
                results.append({
                    "url": str(url),
                    "success": False,
                    "error": "Invalid filename format in URL"
                })
                continue
            
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp())
            image_path = temp_dir / filename
            
            # Download image
            if not download_image(str(url), image_path):
                failed_count += 1
                results.append({
                    "url": str(url),
                    "success": False,
                    "error": "Failed to download image"
                })
                continue
            
            # Load and process image
            bands_data = load_planet_image(str(image_path))
            indices = calculate_all_indices(bands_data)
            
            # Calculate statistics for each index
            indices_stats = {}
            for index_name, index_array in indices.items():
                stats = calculate_statistics(index_array)
                indices_stats[index_name] = stats
            
            results.append({
                "url": str(url),
                "success": True,
                "date": date,
                "unique_id": unique_id,
                "indices": indices_stats
            })
            
        except Exception as e:
            failed_count += 1
            results.append({
                "url": str(url),
                "success": False,
                "error": str(e)
            })
        
        finally:
            # Cleanup temporary files
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Calculate processing time
    elapsed = (datetime.now() - start_time).total_seconds()
    
    return {
        "success": True,
        "field_name": request.field_name,
        "total_images": len(request.image_urls),
        "processed_images": len(request.image_urls) - failed_count,
        "failed_images": failed_count,
        "results": results,
        "processing_time_seconds": round(elapsed, 2)
    }


@app.post("/api/v1/process/water-balance", response_model=WaterBalanceResponse)
async def calculate_water_balance_from_indices(request: WaterBalanceRequest):
    """
    Calculate water balance parameters from vegetation indices
    
    This endpoint:
    1. Loads crop parameters based on crop type and region
    2. Calculates Kcb (basal crop coefficient) using 6 methods
    3. Calculates ETc (crop evapotranspiration)
    4. Calculates soil water depletion and irrigation needs
    
    **Kcb Methods:**
    - Andy's method (polynomial from NDVI)
    - NDVI method (linear from NDVI)
    - SAVI method (linear from SAVI)
    - FC method (linear from Fractional Cover)
    - Ensemble (average of Andy, NDVI, FC)
    - FAO-56 (growth stage based)
    
    **Water Balance Parameters:**
    - ETo, ETr: Reference evapotranspiration
    - Kcb: Basal crop coefficient (6 methods)
    - ETc: Crop evapotranspiration (6 methods)
    - AWC: Available Water Content
    - TAW: Total Available Water
    - Dr: Root zone depletion
    - fDr: Fraction of depletion
    """
    start_time = datetime.now()
    
    try:
        # Load crop parameters
        crop_params = load_crop_parameters(
            request.crop_config['cropType'],
            request.crop_config['region'],
            request.crop_config['plantingMonth'],
            request.crop_config['soilType']
        )
        
        # Calculate days since planting
        planting_date = datetime.strptime(request.crop_config['plantingDate'], "%Y-%m-%d")
        image_date = datetime.strptime(request.date, "%Y-%m-%d")
        days_since_planting = (image_date - planting_date).days
        
        # Get indices
        ndvi = request.indices['NDVI']
        savi = request.indices['SAVI']
        fc = request.indices['FC']
        
        # Calculate Kcb using multiple methods
        kcb_andy = max(0, min(1.3, calculate_kcb_andy(ndvi)))
        kcb_ndvi = max(0, min(1.3, calculate_kcb_ndvi(ndvi)))
        kcb_savi = max(0, min(1.3, calculate_kcb_savi(savi)))
        kcb_fc = max(0, min(1.3, calculate_kcb_fc(fc)))
        kcb_ensemble = max(0, min(1.3, calculate_kcb_ensemble(kcb_andy, kcb_ndvi, kcb_fc)))
        kcb_fao56 = calculate_kcb_fao56(days_since_planting, crop_params)
        
        # Default ETr value (in production, this comes from weather API)
        etr = 5.0  # mm/day
        eto = 3.5  # mm/day
        
        # Calculate ETc for each method
        etc_andy = etr * kcb_andy
        etc_ndvi = etr * kcb_ndvi
        etc_savi = etr * kcb_savi
        etc_fc = etr * kcb_fc
        etc_ensemble = etr * kcb_ensemble
        etc_fao56 = etr * kcb_fao56
        
        # Calculate root depth and water parameters
        zr = calculate_root_depth(days_since_planting, kcb_fao56, crop_params)
        taw = calculate_taw(zr, crop_params)
        awc = calculate_awc(taw, request.crop_config['mad'])
        
        # Build water balance result
        water_balance = {
            "Date": request.date,
            "DaysSincePlanting": days_since_planting,
            "ETo": round(eto, 3),
            "ETr": round(etr, 3),
            "Kcb_Andy": round(kcb_andy, 3),
            "Kcb_NDVI": round(kcb_ndvi, 3),
            "Kcb_SAVI": round(kcb_savi, 3),
            "Kcb_FC": round(kcb_fc, 3),
            "Kcb_Ensemble": round(kcb_ensemble, 3),
            "Kcb_FAO56": round(kcb_fao56, 3),
            "ETc_Andy": round(etc_andy, 3),
            "ETc_NDVI": round(etc_ndvi, 3),
            "ETc_SAVI": round(etc_savi, 3),
            "ETc_FC": round(etc_fc, 3),
            "ETc_Ensemble": round(etc_ensemble, 3),
            "ETc_FAO56": round(etc_fao56, 3),
            "AWC": round(awc, 3),
            "TAW": round(taw, 3),
            "RootDepth_m": round(zr, 3)
        }
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "field_name": request.field_name,
            "date": request.date,
            "water_balance": water_balance,
            "processing_time_seconds": round(elapsed, 2)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/api/v1/process/complete")
async def process_complete_pipeline(request: CompleteProcessRequest):
    """
    Run complete processing pipeline for multiple images
    
    This endpoint:
    1. Downloads all images from URLs
    2. Calculates vegetation indices for each image
    3. Generates time series statistics
    4. Calculates water balance for each date
    5. Returns complete results
    
    **Use this endpoint when:**
    - You have multiple images to process
    - You want complete time series and water balance
    - You want a single API call for the entire pipeline
    
    **Response includes:**
    - Time series data (dates and statistics)
    - Water balance for each date
    - Processing summary
    """
    start_time = datetime.now()
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        
        # Process each image
        results = []
        for url in request.image_urls:
            date, unique_id, filename = extract_info_from_url(str(url))
            if not date or not unique_id:
                continue
            
            # Download and process
            image_path = temp_dir / filename
            if not download_image(str(url), image_path):
                continue
            
            # Calculate indices
            bands_data = load_planet_image(str(image_path))
            indices = calculate_all_indices(bands_data)
            
            # Calculate statistics
            indices_stats = {}
            for index_name, index_array in indices.items():
                stats = calculate_statistics(index_array)
                indices_stats[index_name] = stats
            
            results.append({
                "date": date,
                "unique_id": unique_id,
                "indices": indices_stats
            })
        
        # Sort by date
        results.sort(key=lambda x: x['date'])
        
        # Generate time series
        dates = [r['date'] for r in results]
        timeseries = [{
            "fieldName": request.field_name,
            "timeSeries": results
        }]
        
        # Calculate water balance for each date
        water_balance_results = []
        crop_params = load_crop_parameters(
            request.crop_config['cropType'],
            request.crop_config['region'],
            request.crop_config['plantingMonth'],
            request.crop_config['soilType']
        )
        
        planting_date = datetime.strptime(request.crop_config['plantingDate'], "%Y-%m-%d")
        
        for result in results:
            image_date = datetime.strptime(result['date'], "%Y-%m-%d")
            days_since_planting = (image_date - planting_date).days
            
            # Get mean indices
            ndvi = result['indices']['NDVI']['mean']
            savi = result['indices']['SAVI']['mean']
            fc = result['indices']['FC']['mean']
            
            # Calculate Kcb using all methods
            kcb_andy = max(0, min(1.3, calculate_kcb_andy(ndvi)))
            kcb_ndvi = max(0, min(1.3, calculate_kcb_ndvi(ndvi)))
            kcb_savi = max(0, min(1.3, calculate_kcb_savi(savi)))
            kcb_fc = max(0, min(1.3, calculate_kcb_fc(fc)))
            kcb_ensemble = max(0, min(1.3, calculate_kcb_ensemble(kcb_andy, kcb_ndvi, kcb_fc)))
            kcb_fao56 = calculate_kcb_fao56(days_since_planting, crop_params)
            
            # Reference ET (in production, get from weather API)
            etr = 5.0  # mm/day
            eto = 3.5  # mm/day
            
            # Calculate ETc for all methods
            etc_andy = etr * kcb_andy
            etc_ndvi = etr * kcb_ndvi
            etc_savi = etr * kcb_savi
            etc_fc = etr * kcb_fc
            etc_ensemble = etr * kcb_ensemble
            etc_fao56 = etr * kcb_fao56
            
            # Root depth and water parameters
            zr = calculate_root_depth(days_since_planting, kcb_fao56, crop_params)
            taw = calculate_taw(zr, crop_params)
            awc = calculate_awc(taw, request.crop_config['mad'])
            
            # Simplified depletion (in production, track cumulative)
            dr = etc_ensemble  # Simplified
            fdr = dr / taw if taw > 0 else 0
            fdr = max(0, min(1, fdr))
            
            water_balance_results.append({
                "Date": result['date'],
                "UniqueID": result['unique_id'],
                "DaysSincePlanting": days_since_planting,
                "ETo": round(eto, 3),
                "ETr": round(etr, 3),
                "Kcb_Andy": round(kcb_andy, 3),
                "Kcb_NDVI": round(kcb_ndvi, 3),
                "Kcb_SAVI": round(kcb_savi, 3),
                "Kcb_FC": round(kcb_fc, 3),
                "Kcb_Ensemble": round(kcb_ensemble, 3),
                "Kcb_FAO56": round(kcb_fao56, 3),
                "ETc_Andy": round(etc_andy, 3),
                "ETc_NDVI": round(etc_ndvi, 3),
                "ETc_SAVI": round(etc_savi, 3),
                "ETc_FC": round(etc_fc, 3),
                "ETc_Ensemble": round(etc_ensemble, 3),
                "ETc_FAO56": round(etc_fao56, 3),
                "AWC": round(awc, 3),
                "TAW": round(taw, 3),
                "Dr": round(dr, 3),
                "fDr": round(fdr, 3),
                "RootDepth_m": round(zr, 3),
                "Interpolated": 0,
                "Predicted": 0
            })
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "field_name": request.field_name,
            "total_images": len(request.image_urls),
            "processed_images": len(results),
            "dates": dates,
            "timeseries": timeseries,
            "water_balance": water_balance_results,
            "processing_time_seconds": round(elapsed, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Cleanup
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    # Run with: python app.py
    # Or: uvicorn app:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
