import numpy as np

def calculate_none(band: np.ndarray) -> np.ndarray:
    """Return single band data."""
    return band

def calculate_ndvi(band2: np.ndarray, band1: np.ndarray) -> np.ndarray:
    """Calculate Normalized Difference Vegetation Index."""
    denominator = band2 + band1
    denominator = np.where(denominator == 0, np.nan, denominator)
    return np.divide(band2 - band1, denominator)

def calculate_evi(band3: np.ndarray, band2: np.ndarray, band1: np.ndarray) -> np.ndarray:
    """Calculate Enhanced Vegetation Index."""
    denominator = band3 + 6 * band2 - 7.5 * band1 + 1
    denominator = np.where(denominator == 0, np.nan, denominator)
    return 2.5 * np.divide(band3 - band2, denominator)

def calculate_savi(band2: np.ndarray, band1: np.ndarray) -> np.ndarray:
    """Calculate Soil Adjusted Vegetation Index."""
    denominator = band2 + band1 + 0.5
    denominator = np.where(denominator == 0, np.nan, denominator)
    return 1.5 * np.divide(band2 - band1, denominator)

def calculate_nbr(band2: np.ndarray, band1: np.ndarray) -> np.ndarray:
    """Calculate Normalized Burn Ratio."""
    denominator = band2 + band1
    denominator = np.where(denominator == 0, np.nan, denominator)
    return np.divide(band2 - band1, denominator)

def calculate_msavi(band3: np.ndarray, band2: np.ndarray) -> np.ndarray:
    """Calculate Modified Soil Adjusted Vegetation Index."""
    return 0.5 * (2 + band3 - np.sqrt((2 * band3 + 1)**2 - 8 * (band3 - band2)))

def calculate_ndwi(band2: np.ndarray, band3: np.ndarray) -> np.ndarray:
    """Calculate Normalized Difference Water Index."""
    denominator = band2 + band3
    denominator = np.where(denominator == 0, np.nan, denominator)
    return np.divide(band2 - band3, denominator)