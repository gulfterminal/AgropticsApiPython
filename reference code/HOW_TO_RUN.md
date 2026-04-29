# How to Run the Complete Pipeline from Scratch

## Overview
This guide shows you how to process satellite images from URLs through the complete pipeline:
1. Download images from URLs
2. Calculate vegetation indices
3. Generate time series statistics
4. Calculate water balance (FAO-56 model)

---

## Prerequisites

### Required Python Libraries
```bash
pip install numpy rasterio requests tqdm pandas
```

### Required Files
- `urls.txt` - List of image URLs (one per line)
- `field_config.json` - Field configuration (crop type, planting date, etc.)
- `cropParameters_updated.json` - Crop parameters database
- `calculate_indices.py` - Vegetation indices calculation
- `generate_timeseries.py` - Time series statistics
- `calculate_water_balance.py` - Water balance calculation
- `run_all.py` - Main orchestration script

---

## Step 1: Prepare Your URLs File

Create or edit `urls.txt` with your satellite image URLs (one per line):

```
https://example.com/image1.tif
https://example.com/image2.tif
https://example.com/image3.tif
```

**Example (current urls.txt):**
```
https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif
https://raw.githubusercontent.com/gulfterminal-GIS/restructured-Agroptics/main/20250329_180758_07_2508_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif
```

---

## Step 2: Configure Your Field

Edit `field_config.json` to add or update your field configuration:

```json
{
  "Field_Test": {
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

**Important Parameters:**
- `cropType`: Must match a crop in `cropParameters_updated.json`
- `region`: Geographic region (affects crop coefficients)
- `plantingMonth`: Month of planting (lowercase)
- `soilType`: Soil type (loam, clay, sand, etc.)
- `plantingDate`: Actual planting date (YYYY-MM-DD)
- `firstIrrigDate`: First irrigation date
- `irrigDepth`: Irrigation depth in mm
- `mad`: Management Allowed Depletion (0-1)

---

## Step 3: Run the Complete Pipeline

### Option A: Process URLs from File (Recommended)

```bash
cd "reference code"
python run_all.py urls.txt --field-name Field_Test
```

### Option B: Process URLs Directly from Command Line

```bash
cd "reference code"
python run_all.py --urls "https://example.com/image1.tif" "https://example.com/image2.tif" --field-name MyField
```

### Option C: Custom Directories

```bash
cd "reference code"
python run_all.py urls.txt --field-name Field_Test --cache-dir ../cache --export-dir ../exports
```

### Option D: Don't Keep Cache Files

```bash
cd "reference code"
python run_all.py urls.txt --field-name Field_Test --no-cache
```

---

## Step 4: Understanding the Output

### Console Output
You'll see progress for each step:
```
======================================================================
  🛰️  SATELLITE IMAGE PROCESSING FROM URLS
======================================================================
📁 Field Name: Field_Test
🔗 URLs to process: 2
💾 Cache directory: cache
📂 Export directory: exports
======================================================================

======================================================================
  STEP 1/3: DOWNLOADING & CALCULATING INDICES
======================================================================

[1/2] Processing URL
📷 Processing: 20250329_180511_67_2516_3B_AnalyticMS_SR_8b_harmonized_clip_file_format.tif
📅 Date: 2025-03-29
🆔 Unique ID: 20250329_180511_67_2516
  📥 Downloading...
  ✓ Downloaded successfully
  🔄 Processing image...
  📊 Calculating indices...
  💾 Exporting to: exports/Field_Test/20250329_180511_67_2516/
   ✓ NDVI.tif
   ✓ SAVI.tif
   ✓ FC.tif
   ✓ GCI.tif
   ✓ RECI.tif
   ✓ MSAVI.tif
✅ Successfully processed

======================================================================
  STEP 2/3: GENERATING TIME SERIES STATISTICS
======================================================================
...

======================================================================
  STEP 3/3: CALCULATING WATER BALANCE
======================================================================
...

======================================================================
  ✅ PROCESSING COMPLETE!
======================================================================
```

### Generated Files

#### 1. Indices (GeoTIFF files)
```
exports/Field_Test/20250329_180511_67_2516/
  ├── NDVI.tif
  ├── SAVI.tif
  ├── FC.tif
  ├── GCI.tif
  ├── RECI.tif
  └── MSAVI.tif

exports/Field_Test/20250329_180758_07_2508/
  ├── NDVI.tif
  ├── SAVI.tif
  ├── FC.tif
  ├── GCI.tif
  ├── RECI.tif
  └── MSAVI.tif
```

#### 2. Dates List
**File:** `exports/Field_Test_dates.json`
```json
[
  "2025-03-29",
  "2025-03-29"
]
```

#### 3. Time Series Statistics
**File:** `exports/Field_Test_timeseries.json`
```json
[
  {
    "fieldName": "Field_Test",
    "timeSeries": [
      {
        "date": "2025-03-29",
        "folder": "20250329_180511_67_2516",
        "indices": {
          "NDVI": {
            "mean": 0.2018,
            "min": 0.1095,
            "max": 0.2884,
            "std": 0.0236,
            "p25": 0.1872,
            "p50": 0.2008,
            "p75": 0.2152,
            "count": 3444,
            "width": 43,
            "height": 82
          },
          ...
        }
      },
      ...
    ]
  }
]
```

#### 4. Water Balance Results
**File:** `exports/Field_Test_water_balance.json`
```json
[
  {
    "Date": "2025-03-29",
    "UniqueID": "20250329_180511_67_2516",
    "ETo": 3.5,
    "ETr": 5.0,
    "Kcb_Ensemble": 0.286,
    "ETc_Ensemble": 1.429,
    "Dr": 1.429,
    "fDr": 0.055,
    "DaysSincePlanting": 1,
    "RootDepth_m": 0.2,
    ...
  },
  ...
]
```

#### 5. Processing Summary
**File:** `exports/Field_Test_processing_summary.json`
```json
{
  "field_name": "Field_Test",
  "total_urls": 2,
  "successful": 2,
  "failed": 0,
  "processing_time_seconds": 45.3,
  "timestamp": "2025-04-29T10:30:00",
  "results": [...]
}
```

---

## Step 5: Verify Results

Run the verification script:

```bash
python check_results.py
```

**Expected Output:**
```
Water Balance Results for Field_Test:
Total entries: 2

Entry 1:
  Date: 2025-03-29
  Unique ID: 20250329_180511_67_2516
  ETo: 3.5 mm
  Kcb_Ensemble: 0.286
  ETc_Ensemble: 1.43 mm
  Dr: 1.43 mm

Entry 2:
  Date: 2025-03-29
  Unique ID: 20250329_180758_07_2508
  Kcb_Ensemble: 0.309
  ETc_Ensemble: 1.55 mm
```

---

## Clean Start (Delete Previous Results)

If you want to start completely fresh:

### Windows:
```bash
# Delete cache
rmdir /s /q cache\Field_Test

# Delete exports
rmdir /s /q exports\Field_Test
del exports\Field_Test_*.json
```

### Linux/Mac:
```bash
# Delete cache
rm -rf cache/Field_Test

# Delete exports
rm -rf exports/Field_Test
rm exports/Field_Test_*.json
```

Then run the pipeline again from Step 3.

---

## Troubleshooting

### Error: "No such file or directory: urls.txt"
- Make sure you're in the `reference code` directory
- Or provide the full path: `python run_all.py "C:/path/to/urls.txt"`

### Error: "Crop parameters not found"
- Check that `cropType`, `region`, `plantingMonth`, and `soilType` in `field_config.json` match entries in `cropParameters_updated.json`

### Error: "Failed to download"
- Check your internet connection
- Verify the URLs are accessible
- Try opening the URL in a web browser

### No water balance output
- Make sure your field is configured in `field_config.json`
- Check that the field name matches exactly (case-sensitive)
- Verify the planting date is before the image dates

---

## Advanced Usage

### Process Multiple Fields

Add multiple fields to `field_config.json`:
```json
{
  "Field_Test": {...},
  "Field_10": {...},
  "Field_11": {...}
}
```

Then process each field separately:
```bash
python run_all.py urls_field_test.txt --field-name Field_Test
python run_all.py urls_field_10.txt --field-name Field_10
python run_all.py urls_field_11.txt --field-name Field_11
```

### Custom Field Name

Use any field name you want:
```bash
python run_all.py urls.txt --field-name MyCustomField
```

Just make sure to add `MyCustomField` to `field_config.json` first.

---

## Quick Reference

### Minimum Command
```bash
cd "reference code"
python run_all.py urls.txt
```

### Full Command with All Options
```bash
cd "reference code"
python run_all.py urls.txt \
  --field-name Field_Test \
  --cache-dir ../cache \
  --export-dir ../exports \
  --no-cache
```

### Help
```bash
python run_all.py --help
```

---

## What Each Step Does

1. **Download & Calculate Indices** (~30 seconds per image)
   - Downloads TIF files from URLs
   - Calculates 6 vegetation indices (NDVI, SAVI, FC, GCI, RECI, MSAVI)
   - Exports each index as a GeoTIFF file

2. **Generate Time Series** (~1 second)
   - Reads all exported indices
   - Calculates statistics (mean, min, max, std, percentiles)
   - Creates time series JSON files

3. **Calculate Water Balance** (~1 second)
   - Loads crop parameters
   - Calculates Kcb (crop coefficient) using multiple methods
   - Calculates ETc (crop evapotranspiration)
   - Calculates soil water depletion
   - Generates water balance JSON file

**Total Time:** ~1-2 minutes for 2 images

---

## Notes

- Each image gets a unique folder based on its timestamp (no overwriting)
- Images from the same date are preserved separately
- The UniqueID field in water balance output distinguishes same-date images
- Cache files can be deleted after processing (use `--no-cache`)
- All outputs are in JSON format for easy integration with other tools
