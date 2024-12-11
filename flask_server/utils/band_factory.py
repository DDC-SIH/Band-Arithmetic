from typing import Dict, Any, Callable
import numpy as np
from .band_arithmetic import *

class BandArithmeticFactory:
    @staticmethod
    def get_processor(method: str) -> Callable:
        """Returns the appropriate band arithmetic function based on method name."""
        processors = {
            'ndvi': calculate_ndvi,
            'ndwi': calculate_ndwi,
            'evi': calculate_evi,
            'savi': calculate_savi,
            'msavi': calculate_msavi,
            'btt': calculate_brightness_temp,
            'cloud': calculate_cloud_mask,
            'olr': calculate_olr,
            'uth': calculate_uth,
            'amv': calculate_amv,
            'ndsi': calculate_ndsi,
            'aod': calculate_aod,
            'wvc': calculate_wvc,
            'azimuth': calculate_azimuth
        }
        
        if method.lower() not in processors:
            raise ValueError(f"Unsupported band arithmetic method: {method}")
        
        return processors[method.lower()]

    @staticmethod
    def process_bands(method: str, bands: Dict[str, np.ndarray], metadata: Dict = None, **kwargs) -> np.ndarray:
        """Process the bands using the specified arithmetic method."""
        processor = BandArithmeticFactory.get_processor(method)
        
        # Handle special cases with metadata requirements
        if method.lower() == 'btt' and metadata:
            return processor(
                bands['tir'],
                metadata.get('scale_factor', 1.0),
                metadata.get('add_offset', 0.0)
            )
        elif method.lower() == 'olr':
            return processor(bands['tir1'], bands['tir2'], kwargs.get('c', 1.1))
        elif method.lower() == 'uth' and metadata:
            return processor(bands['wv'], metadata.get('wv_scale_factor', 1.0))
        elif method.lower() == 'amv' and metadata:
            return processor(
                bands['mir'], bands['wv'],
                metadata.get('mir_scale', 1.0),
                metadata.get('wv_scale', 1.0)
            )
        else:
            # Pass all available bands to the processor
            return processor(*bands.values())