import json
import logging
from typing import Dict, Union, List
import rasterio
from rasterio.mask import mask
import requests
import os
import zipfile
from rasterio.warp import transform_geom
from .colorization import apply_colormap
import numpy as np
import matplotlib.pyplot as plt

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

def process_config(config_file: str) -> str:
    """Process the configuration file and create cropped outputs."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Get geometry and URLs
        geometry_feature = get_geometry_from_config(config)
        urls = get_urls_from_config(config)
        
        # Download and crop each TIFF
        cropped_bands = {}
        output_files = []
        
        # Band numbering starts from 1 to match specifications
        for idx, url in enumerate(urls, start=1):
            local_file = os.path.join('uploads', f"band_{idx}.tif")
            downloaded_file = download_tiff(url, local_file)
            
            cropped_data, out_meta = crop_tiff(
                downloaded_file, 
                geometry_feature["geometry"]
            )
            
            # Store cropped data with band numbers starting from 1
            band_name = f"band_{idx}"
            cropped_bands[band_name] = cropped_data[0]
            
            # Save cropped band
            output_file = os.path.join('results', f"cropped_{idx}.tif")
            with rasterio.open(output_file, "w", **out_meta) as dest:
                dest.write(cropped_data[0][np.newaxis, :, :])
            output_files.append(output_file)
            
            os.remove(downloaded_file)
            
        # Process band arithmetic if specified in effects
        if "effects" in config and "arithmatic" in config["effects"]:
            from .band_factory import BandArithmeticFactory
            
            # Validate required number of bands
            method = config["effects"]["arithmatic"]
            required_bands = BandArithmeticFactory.get_required_bands(method)
            if len(cropped_bands) < required_bands:
                raise ValueError(f"{method} requires {required_bands} bands, but only {len(cropped_bands)} provided")
            
            # Calculate the index using bands
            result = BandArithmeticFactory.process_bands(
                method,
                cropped_bands,
                metadata=config.get("metadata", {})
            )
            
            # Save the arithmetic result
            arithmetic_file = os.path.join('results', "band_arithmetic_result.tif")
            out_meta.update({"count": 1})
            with rasterio.open(arithmetic_file, "w", **out_meta) as dest:
                dest.write(result[np.newaxis, :, :])
            output_files.append(arithmetic_file)
            
            # Apply colormap if specified
            if "colormap" in config["effects"]:
                colormap_name = config["effects"]["colormap"]
                # Get min, max, steps from config or use defaults
                min_val = config["effects"].get("min", float(np.min(result)))
                max_val = config["effects"].get("max", float(np.max(result)))
                steps = config["effects"].get("steps", 256)
                # Apply colormap
                colorized_result = apply_colormap(result, colormap_name, min_val, max_val, steps)
                # Save the colorized image
                colorized_output_file = os.path.join('results', "band_arithmetic_result.png")
                plt.imsave(colorized_output_file, colorized_result)
                output_files.append(colorized_output_file)
        
        # Zip results
        zip_filename = os.path.join('results', "cropped_results.zip")
        zip_results(output_files, zip_filename)
        
        # Clean up output files
        for file in output_files:
            os.remove(file)
            
        logger.info(f"Processing complete. Results saved in {zip_filename}")
        return zip_filename
        
    except Exception as e:
        logger.error(f"Error processing config file: {str(e)}")
        raise