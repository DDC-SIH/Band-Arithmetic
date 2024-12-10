import numpy as np
from typing import Tuple, Dict, Union, Optional

def calculate_ndvi(nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
    """Calculate Normalized Difference Vegetation Index."""
    denominator = (nir_band + red_band)
    # Avoid division by zero
    denominator = np.where(denominator == 0, np.nan, denominator)
    return np.divide((nir_band - red_band), denominator)

def calculate_ndwi(nir_band: np.ndarray, green_band: np.ndarray) -> np.ndarray:
    """Calculate Normalized Difference Water Index."""
    denominator = (green_band + nir_band)
    denominator = np.where(denominator == 0, np.nan, denominator)
    return np.divide((green_band - nir_band), denominator)

def calculate_evi(nir_band: np.ndarray, red_band: np.ndarray, blue_band: np.ndarray) -> np.ndarray:
    """Calculate Enhanced Vegetation Index."""
    return 2.5 * ((nir_band - red_band) / (nir_band + 6 * red_band - 7.5 * blue_band + 1))

def calculate_savi(nir_band: np.ndarray, red_band: np.ndarray, L: float = 0.5) -> np.ndarray:
    """Calculate Soil Adjusted Vegetation Index."""
    return ((nir_band - red_band) * (1 + L)) / (nir_band + red_band + L)

def calculate_msavi(nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
    """Calculate Modified Soil Adjusted Vegetation Index."""
    return (2 * nir_band + 1 - np.sqrt((2 * nir_band + 1)**2 - 8 * (nir_band - red_band))) / 2

def calculate_brightness_temp(band: np.ndarray, scale_factor: float, add_offset: float) -> np.ndarray:
    """Calculate brightness temperature"""
    return (band / scale_factor) + add_offset - 273.15

def calculate_cloud_mask(band: np.ndarray, threshold: float = 250) -> np.ndarray:
    """Calculate cloud mask"""
    return band > threshold

def calculate_olr(tir1: np.ndarray, tir2: np.ndarray, c: float = 1.1) -> np.ndarray:
    """Calculate Outgoing Longwave Radiation"""
    return c * (tir1 + tir2)

def calculate_uth(wv_band: np.ndarray, scale_factor: float) -> np.ndarray:
    """Calculate Upper Tropospheric Humidity"""
    wv_scaled = wv_band * scale_factor
    return 100 * (wv_scaled / (wv_scaled + 1))

def calculate_amv(mir_band: np.ndarray, wv_band: np.ndarray, 
                 mir_scale: float, wv_scale: float) -> np.ndarray:
    """Calculate Atmospheric Motion Vectors"""
    return (mir_band * mir_scale) - (wv_band * wv_scale)

def calculate_ndsi(vis_band: np.ndarray, swir_band: np.ndarray) -> np.ndarray:
    """Calculate Normalized Difference Snow Index"""
    return (vis_band - swir_band) / (vis_band + swir_band)

def calculate_aod(vis_band: np.ndarray, epsilon: float = 0.1) -> np.ndarray:
    """Calculate Aerosol Optical Depth"""
    return vis_band / (vis_band + epsilon)

def calculate_wvc(wv_band: np.ndarray, norm_factor: float = 1.0) -> np.ndarray:
    """Calculate Water Vapor Content"""
    return 100 * (wv_band / norm_factor)

def calculate_azimuth(azimuth_band: np.ndarray, scale_factor: float) -> np.ndarray:
    """Calculate calibrated azimuth"""
    return azimuth_band * scale_factor