"""
Reference Code - Complete URL Processing Pipeline
==================================================
Downloads satellite images from URLs and runs complete processing:
1. Download images from URLs
2. Calculate vegetation indices
3. Generate time series statistics
4. Calculate water balance (if configured)

Usage:
    python run_all.py urls.txt [--field-name FIELD_NAME]
    
Or provide URLs directly:
    python run_all.py --urls "url1" "url2" "url3"

Example urls.txt:
    https://example.com/image1.tif
    https://example.com/image2.tif
"""

import os
import sys
import time
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Import from reference code modules
from calculate_indices import load_planet_image, calculate_all_indices, export_index_geotiff
from generate_timeseries import generate_all_timeseries
from calculate_water_balance import process_all_fields


def download_file(url, output_path):
    """Download a file from URL with progress bar"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"  📥 Downloading: {output_path.name}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            if total_size > 0:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="    ") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print(f"  ✓ Downloaded successfully\n")
        return output_path
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Failed to download: {e}\n")
        if output_path.exists():
            output_path.unlink()
        return None


def extract_info_from_filename(filename):
    """Extract date and unique identifier from Planet filename"""
    # Filename format: YYYYMMDD_HHMMSS_XX_XXXX_...
    parts = filename.split('_')
    if len(parts) >= 4:
        date_str = parts[0]  # YYYYMMDD
        time_str = parts[1]  # HHMMSS
        unique_id = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"  # Full unique identifier
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return formatted_date, unique_id
    return None, None


def process_url(url, field_name, cache_dir, export_base):
    """Download and process a single URL - each URL gets unique folder"""
    filename = url.split('/')[-1]
    date, unique_id = extract_info_from_filename(filename)
    
    if not date or not unique_id:
        print(f"  ⚠️  Could not extract date/ID from filename: {filename}")
        return None
    
    print(f"\n{'='*70}")
    print(f"📷 Processing: {filename}")
    print(f"📅 Date: {date}")
    print(f"🆔 Unique ID: {unique_id}")
    print(f"{'='*70}")
    
    # Download file to unique cache location
    cache_path = Path(cache_dir) / field_name / unique_id
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_file = cache_path / filename
    
    downloaded_file = download_file(url, cache_file)
    
    if not downloaded_file:
        return None
    
    try:
        # Process the image
        print("  🔄 Processing image...")
        print("  📊 Calculating indices...")
        bands_data = load_planet_image(str(downloaded_file))
        indices = calculate_all_indices(bands_data)
        
        # Export indices to unique date-time folder (no overwriting)
        # Format: exports/Field_Name/YYYY-MM-DD_HHMMSS_XX_XXXX/
        export_path = Path(export_base) / field_name / unique_id
        export_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n  💾 Exporting to: {export_path}")
        for index_name, index_array in indices.items():
            output_file = export_path / f"{index_name}.tif"
            export_index_geotiff(index_array, str(output_file), bands_data['metadata'])
            print(f"   ✓ {index_name}.tif")
        
        print(f"\n✅ Successfully processed: {filename}\n")
        
        return {
            'url': url,
            'filename': filename,
            'date': date,
            'unique_id': unique_id,
            'status': 'success',
            'indices_exported': list(indices.keys())
        }
        
    except Exception as e:
        print(f"  ❌ Error processing: {e}")
        import traceback
        traceback.print_exc()
        return {
            'url': url,
            'filename': filename,
            'date': date,
            'unique_id': unique_id,
            'status': 'error',
            'error': str(e)
        }


def load_urls_from_file(filepath):
    """Load URLs from a text file (one URL per line)"""
    urls = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(
        description='Process satellite images from URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process URLs from a file
  python run_all.py urls.txt
  
  # Process URLs from a file with custom field name
  python run_all.py urls.txt --field-name MyField
  
  # Process URLs directly from command line
  python run_all.py --urls "https://example.com/image1.tif" "https://example.com/image2.tif"
  
  # Don't keep cached files
  python run_all.py urls.txt --no-cache
        """
    )
    
    parser.add_argument('file', nargs='?', help='Text file containing URLs (one per line)')
    parser.add_argument('--urls', nargs='+', help='URLs to process (space-separated)')
    parser.add_argument('--field-name', default='Field_URLs', help='Field name for exports (default: Field_URLs)')
    parser.add_argument('--cache-dir', default='cache', help='Directory for cached downloads (default: cache)')
    parser.add_argument('--export-dir', default='exports', help='Directory for exports (default: exports)')
    parser.add_argument('--no-cache', action='store_true', help='Delete cached files after processing')
    
    args = parser.parse_args()
    
    # Get URLs from file or command line
    if args.urls:
        urls = args.urls
    elif args.file:
        if not os.path.exists(args.file):
            print(f"❌ Error: File not found: {args.file}")
            sys.exit(1)
        urls = load_urls_from_file(args.file)
    else:
        parser.print_help()
        sys.exit(1)
    
    if not urls:
        print("❌ Error: No URLs provided")
        sys.exit(1)
    
    # Print header
    print(f"\n{'='*70}")
    print(f"  🛰️  SATELLITE IMAGE PROCESSING FROM URLS")
    print(f"{'='*70}")
    print(f"📁 Field Name: {args.field_name}")
    print(f"🔗 URLs to process: {len(urls)}")
    print(f"💾 Cache directory: {args.cache_dir}")
    print(f"📂 Export directory: {args.export_dir}")
    print(f"🗑️  Keep cache: {not args.no_cache}")
    print(f"{'='*70}")
    
    start_time = time.time()
    results = []
    
    # Process each URL
    print(f"\n{'='*70}")
    print(f"  STEP 1/3: DOWNLOADING & CALCULATING INDICES")
    print(f"{'='*70}")
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing URL")
        result = process_url(url, args.field_name, args.cache_dir, args.export_dir)
        if result:
            results.append(result)
    
    step1_time = time.time() - start_time
    print(f"\n✓ Step 1 completed in {step1_time:.1f} seconds")
    print(f"  - Images processed: {len(results)}/{len(urls)}")
    
    # Generate time series
    print(f"\n{'='*70}")
    print(f"  STEP 2/3: GENERATING TIME SERIES STATISTICS")
    print(f"{'='*70}\n")
    
    step2_start = time.time()
    # Use absolute path for exports directory
    export_dir_abs = Path(args.export_dir).resolve()
    if export_dir_abs.exists():
        generate_all_timeseries(str(export_dir_abs))
    else:
        print(f"⚠️  Warning: Export directory not found: {export_dir_abs}")
    
    step2_time = time.time() - step2_start
    print(f"\n✓ Step 2 completed in {step2_time:.1f} seconds")
    
    # Calculate water balance
    print(f"\n{'='*70}")
    print(f"  STEP 3/3: CALCULATING WATER BALANCE")
    print(f"{'='*70}\n")
    
    step3_start = time.time()
    try:
        process_all_fields(str(export_dir_abs))
    except Exception as e:
        print(f"⚠️  Water balance calculation skipped: {e}")
    
    step3_time = time.time() - step3_start
    print(f"\n✓ Step 3 completed in {step3_time:.1f} seconds")
    
    # Clean up cache if requested
    if args.no_cache:
        print(f"\n{'='*70}")
        print(f"  🗑️  CLEANING UP CACHE")
        print(f"{'='*70}\n")
        cache_path = Path(args.cache_dir) / args.field_name
        if cache_path.exists():
            import shutil
            shutil.rmtree(cache_path)
            print(f"  ✓ Removed cache directory: {cache_path}")
    
    # Print summary
    elapsed_time = time.time() - start_time
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful
    
    print(f"\n{'='*70}")
    print(f"  ✅ PROCESSING COMPLETE!")
    print(f"{'='*70}")
    print(f"\nField: {args.field_name}")
    print(f"\nTiming Summary:")
    print(f"  Step 1 (Indices):      {step1_time:.1f}s")
    print(f"  Step 2 (Time Series):  {step2_time:.1f}s")
    print(f"  Step 3 (Water Balance): {step3_time:.1f}s")
    print(f"  {'─'*38}")
    print(f"  Total Time:            {elapsed_time:.1f}s ({elapsed_time/60:.1f} minutes)")
    print(f"\n📊 Processing Results:")
    print(f"  Total URLs: {len(urls)}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"\n📁 Output Files:")
    print(f"  - {args.export_dir}/{args.field_name}/[unique_id]/[indices].tif")
    print(f"  - {args.export_dir}/{args.field_name}_dates.json")
    print(f"  - {args.export_dir}/{args.field_name}_timeseries.json")
    print(f"  - {args.export_dir}/{args.field_name}_water_balance.json")
    print(f"{'='*70}\n")
    
    # Save processing summary
    summary = {
        'field_name': args.field_name,
        'total_urls': len(urls),
        'successful': successful,
        'failed': failed,
        'processing_time_seconds': elapsed_time,
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    summary_file = Path(args.export_dir) / f"{args.field_name}_processing_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"📄 Processing summary saved: {summary_file}\n")


if __name__ == '__main__':
    main()
