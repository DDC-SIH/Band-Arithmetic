import json
import logging
from typing import Dict, Union, List
import rasterio
from rasterio.mask import mask
import requests
import os
import zipfile
from rasterio.warp import transform_geom

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def aoi_to_polygon(aoi: Dict) -> Dict:
    """Convert AOI bounds to polygon geometry."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [aoi["west"], aoi["north"]],
            [aoi["east"], aoi["north"]],
            [aoi["east"], aoi["south"]],
            [aoi["west"], aoi["south"]],
            [aoi["west"], aoi["north"]]
        ]]
    }

def get_geometry_from_config(config: Dict) -> Dict:
    """Extract geometry from config, handling both AOI and polygon cases."""
    if "aoi" in config:
        return {
            "type": "Feature",
            "geometry": aoi_to_polygon(config["aoi"]),
            "properties": {
                "created": config["aoi"].get("created", ""),
                "coordinateSystem": config["aoi"].get("coordinateSystem", "EPSG:4326"),
                "units": config["aoi"].get("units", "degrees")
            }
        }
    elif "polygon" in config:
        return config["polygon"]
    else:
        raise ValueError("Neither AOI nor polygon found in config")

def get_urls_from_config(config: Dict) -> List[str]:
    """Extract URLs from config."""
    if "urls" not in config:
        raise ValueError("No URLs found in config")
    return config["urls"]

def download_tiff(url: str, local_filename: str) -> str:
    """Download TIFF file from URL."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return local_filename
    else:
        raise Exception(f"Failed to download {url}")

def crop_tiff(input_tiff: str, geometry: Dict) -> tuple:
    """Crop a TIFF file based on the geometry."""
    try:
        with rasterio.open(input_tiff) as src:
            # Transform geometry to match raster's CRS
            transformed_geometry = transform_geom(
                'EPSG:4326',
                src.crs,
                geometry
            )
            
            out_image, out_transform = mask(src, [transformed_geometry], crop=True)
            out_meta = src.meta.copy()
            
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
            return out_image, out_meta
    except Exception as e:
        logger.error(f"Error cropping raster: {str(e)}")
        raise

def zip_results(files_to_zip: List[str], output_zip: str) -> None:
    """Zip specified files."""
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            zipf.write(file, os.path.basename(file))

def process_config(config_file: str) -> None:
    """Process the configuration file and create cropped outputs."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Get geometry and URLs
        geometry_feature = get_geometry_from_config(config)
        urls = get_urls_from_config(config)
        
        # Download and crop each TIFF
        output_files = []
        for idx, url in enumerate(urls):
            # Download
            local_file = f"band_{idx}.tif"
            downloaded_file = download_tiff(url, local_file)
            
            # Crop
            cropped_data, out_meta = crop_tiff(
                downloaded_file, 
                geometry_feature["geometry"]
            )
            
            # Save cropped output
            output_file = f"cropped_band_{idx}.tif"
            with rasterio.open(output_file, "w", **out_meta) as dest:
                dest.write(cropped_data)
            
            output_files.append(output_file)
            os.remove(downloaded_file)  # Clean up downloaded file
        
        # Zip results
        zip_filename = "cropped_results.zip"
        zip_results(output_files, zip_filename)
        
        # Clean up cropped files after zipping
        for file in output_files:
            os.remove(file)
            
        logger.info(f"Processing complete. Results saved in {zip_filename}")
        
    except Exception as e:
        logger.error(f"Error processing config file: {str(e)}")
        raise

def main():
    try:
        process_config('inputwithoutband.json')
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
