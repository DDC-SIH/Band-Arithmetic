import json
import rasterio
import numpy as np
from rasterio.mask import mask
import requests
import os
from rasterio.warp import transform_geom
import logging
import zipfile
from rasterio.features import geometry_mask
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib import colormaps
import h5py
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BandArithmetic(Enum):
    NDVI = "ndvi"
    NDWI = "ndwi"
    NBR = "nbr"
    MSAVI = "msavi"
    SAVI = "savi"
    EVI = "evi"
    BTT = "brightness_temperature"
    CLOUD = "cloud_mask"
    OLR = "olr"
    SST = "sst"
    UTH = "uth"
    AMV = "amv"
    LST = "lst"
    NDSI = "ndsi"
    FIRE = "fire"
    AOD = "aod"
    WVC = "water_vapor"
    AZIMUTH = "azimuth"

class BandCalculator:
    def __init__(self, metadata):
        """Initialize calculator with metadata"""
        self.metadata = metadata
        
    def calculate(self, bands, arithmetic_type, **kwargs):
        """Calculate the requested band arithmetic"""
        calculator = {
            BandArithmetic.NDVI.value: self._calculate_ndvi,
            BandArithmetic.BTT.value: self._calculate_brightness_temp,
            BandArithmetic.CLOUD.value: self._calculate_cloud_mask,
            BandArithmetic.OLR.value: self._calculate_olr,
            BandArithmetic.SST.value: self._calculate_sst,
            BandArithmetic.UTH.value: self._calculate_uth,
            BandArithmetic.AMV.value: self._calculate_amv,
            BandArithmetic.LST.value: self._calculate_lst,
            BandArithmetic.NDSI.value: self._calculate_ndsi,
            BandArithmetic.FIRE.value: self._calculate_fire,
            BandArithmetic.AOD.value: self._calculate_aod,
            BandArithmetic.WVC.value: self._calculate_wvc,
            BandArithmetic.AZIMUTH.value: self._calculate_azimuth
        }
        
        return calculator[arithmetic_type](bands, **kwargs)

    def _calculate_brightness_temp(self, bands, band_name):
        """Calculate brightness temperature"""
        scale_factor = float(self.metadata[f'IMG_{band_name}_lab_radiance_scale_factor'])
        add_offset = float(self.metadata[f'IMG_{band_name}_lab_radiance_add_offset'])
        return (bands[band_name] / scale_factor) + add_offset - 273.15

    def _calculate_cloud_mask(self, bands, threshold=250):
        """Calculate cloud mask using brightness temperature"""
        bt = self._calculate_brightness_temp(bands, 'TIR1')
        return bt > threshold

    def _calculate_olr(self, bands, c=1.1):
        """Calculate Outgoing Longwave Radiation"""
        tir1 = self._calculate_brightness_temp(bands, 'TIR1')
        tir2 = self._calculate_brightness_temp(bands, 'TIR2')
        return c * (tir1 + tir2)

    def _calculate_sst(self, bands):
        """Calculate Sea Surface Temperature"""
        return self._calculate_brightness_temp(bands, 'TIR2')

    def _calculate_uth(self, bands):
        """Calculate Upper Tropospheric Humidity"""
        wv = bands['WV']
        scale_factor = float(self.metadata['IMG_WV_lab_radiance_scale_factor'])
        wv_scaled = wv * scale_factor
        return 100 * (wv_scaled / (wv_scaled + 1))

    def _calculate_amv(self, bands):
        """Calculate Atmospheric Motion Vectors"""
        mir_scale = float(self.metadata['IMG_MIR_lab_radiance_scale_factor'])
        wv_scale = float(self.metadata['IMG_WV_lab_radiance_scale_factor'])
        return (bands['MIR'] * mir_scale) - (bands['WV'] * wv_scale)

    def _calculate_lst(self, bands):
        """Calculate Land Surface Temperature"""
        return self._calculate_brightness_temp(bands, 'TIR1')

    def _calculate_ndsi(self, bands):
        """Calculate Normalized Difference Snow Index"""
        vis = bands['VIS'] * float(self.metadata['IMG_VIS_lab_radiance_scale_factor'])
        swir = bands['SWIR'] * float(self.metadata['IMG_SWIR_lab_radiance_scale_factor'])
        return (vis - swir) / (vis + swir)

    def _calculate_fire(self, bands, threshold=350):
        """Detect fire hotspots"""
        return self._calculate_brightness_temp(bands, 'TIR1') > threshold

    def _calculate_aod(self, bands, epsilon=0.1):
        """Calculate Aerosol Optical Depth"""
        vis = bands['VIS'] * float(self.metadata['IMG_VIS_lab_radiance_scale_factor'])
        return vis / (vis + epsilon)

    def _calculate_wvc(self, bands, norm_factor=1.0):
        """Calculate Water Vapor Content"""
        wv = bands['WV'] * float(self.metadata['IMG_WV_lab_radiance_scale_factor'])
        return 100 * (wv / norm_factor)

    def _calculate_azimuth(self, bands, azimuth_type='satellite'):
        """Calculate calibrated azimuth"""
        scale_factor = float(self.metadata[f'{azimuth_type}_Azimuth_scale_factor'])
        return bands[f'{azimuth_type}_azimuth'] * scale_factor

def download_tiff(url, local_filename):
    """Download TIFF file from URL."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return local_filename
    else:
        raise Exception(f"Failed to download {url}")

def create_mask(geometry, out_shape, transform):
    """Create a mask from geometry"""
    mask = geometry_mask(
        [geometry],
        out_shape=out_shape,
        transform=transform,
        invert=True
    )
    return mask

def crop_tiff(input_tiff, geometry):
    """Crop a TIFF file based on the geometry."""
    try:
        with rasterio.open(input_tiff) as src:
            # Transform geometry to match raster's CRS
            transformed_geometry = transform_geom(
                'EPSG:4326',  # Source CRS (assuming geometry is in WGS84)
                src.crs,      # Target CRS from the raster
                geometry
            )
            
            logger.info(f"Raster bounds: {src.bounds}")
            logger.info(f"Geometry bounds: {transformed_geometry}")
            
            out_image, out_transform = mask(src, [transformed_geometry], crop=True)
            out_meta = src.meta.copy()
            
            # Create mask for the geometry
            mask_array = create_mask(transformed_geometry, 
                                   (out_image.shape[1], out_image.shape[2]), 
                                   out_transform)
            
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": None
            })
            return out_image[0], mask_array, out_meta
    except ValueError as e:
        logger.error(f"Error cropping raster: {str(e)}")
        raise

def calculate_ndvi(nir_array, red_array, mask_array):
    """Calculate NDVI from NIR and RED bands with masking."""
    # Convert to float to avoid integer division
    nir = nir_array.astype(float)
    red = red_array.astype(float)
    
    # Handle potential division by zero
    denominator = (nir + red)
    ndvi = np.where(
        denominator != 0,
        (nir - red) / denominator,
        0
    )
    
    # Clip values to [-1, 1] range and apply mask
    ndvi = np.clip(ndvi, -1, 1)
    # Set areas outside the polygon to nodata (transparent)
    ndvi = np.where(mask_array, ndvi, np.nan)
    return ndvi

def aoi_to_polygon(aoi):
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

def get_geometry_from_config(config):
    """Extract geometry from config, handling both AOI and polygon cases."""
    if "aoi" in config:
        return aoi_to_polygon(config["aoi"])
    elif "polygon" in config:
        return config["polygon"]["geometry"]
    else:
        raise ValueError("Neither AOI nor polygon found in config")

def apply_colormap(ndvi_array, mask_array, config):
    """Apply specified colormap to NDVI values with custom settings"""
    colormap_name = config["effects"]["colormap"].lower()
    vmin = config["effects"].get("min", -1)
    vmax = config["effects"].get("max", 1)
    
    # Get the specified colormap
    try:
        cmap = colormaps[colormap_name]
    except KeyError:
        logger.warning(f"Colormap {colormap_name} not found, using viridis")
        cmap = colormaps["viridis"]
    
    # Create normalized data in range [0,1] for colormap
    norm = Normalize(vmin=vmin, vmax=vmax)
    normalized_ndvi = norm(ndvi_array)
    
    # Apply colormap
    colored = cmap(normalized_ndvi)
    
    # Convert to uint8 for RGB
    rgb_image = (colored[:, :, :3] * 255).astype(np.uint8)
    
    # Add alpha channel based on mask and valid NDVI values
    alpha = np.where(mask_array & ~np.isnan(ndvi_array), 255, 0).astype(np.uint8)
    
    # Stack RGB and alpha
    rgba_image = np.dstack((rgb_image, alpha))
    
    return rgba_image

def zip_results(files_to_zip, output_zip):
    """Zip specified files."""
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            zipf.write(file, os.path.basename(file))

def main():
    # Load JSON configuration
    with open('input.json', 'r') as f:
        config = json.load(f)
    
    try:
        # Load metadata from HDF5 file
        with h5py.File('data.h5', 'r') as f:
            metadata = dict(f.attrs)
        
        # Initialize band calculator
        calculator = BandCalculator(metadata)
        
        # Get requested arithmetic type
        arithmetic_type = config['effects']['arithmetic']
        
        # Download and process bands based on arithmetic type
        # Download and crop TIFF files
        red_url = config['urls'][0]  # VIS (RED) band
        nir_url = config['urls'][1]  # SWIR band (substitute for NIR)
        
        # Download files
        logger.info("Downloading files...")
        red_file = download_tiff(red_url, "red.tif")
        nir_file = download_tiff(nir_url, "nir.tif")
        
        # Get geometry from config (either AOI or polygon)
        geometry = get_geometry_from_config(config)
        
        logger.info("Cropping images...")
        # Crop both images
        red_data, mask_array, meta = crop_tiff(red_file, geometry)
        nir_data, _, _ = crop_tiff(nir_file, geometry)
        
        logger.info("Calculating NDVI...")
        # Calculate NDVI with mask
        ndvi = calculate_ndvi(nir_data, red_data, mask_array)
        
        logger.info("Applying colormap...")
        # Apply specified colormap with config settings
        colored_ndvi = apply_colormap(ndvi, mask_array, config)
        
        # Update metadata for RGBA output
        meta.update({
            "dtype": "uint8",
            "count": 4,  # 4 bands for RGBA
            "nodata": None
        })
        
        # Save colored NDVI result
        output_file = "ndvi_colored.tif"
        with rasterio.open(output_file, "w", **meta) as dst:
            for idx in range(4):
                dst.write(colored_ndvi[:, :, idx], idx + 1)
        
        logger.info(f"Colored NDVI saved as {output_file}")
        
        # Cleanup downloaded files
        os.remove(red_file)
        os.remove(nir_file)
        
        # Zip results
        files_to_zip = [output_file]
        zip_filename = "results.zip"
        zip_results(files_to_zip, zip_filename)
        
        logger.info(f"Results zipped in {zip_filename}")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()