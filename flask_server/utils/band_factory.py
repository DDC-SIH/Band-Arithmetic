from typing import Dict, Callable
import numpy as np
from .band_arithmetic import *

class BandArithmeticFactory:
    @staticmethod
    def get_required_bands(method: str) -> int:
        """Returns the number of required bands for each method."""
        requirements = {
            'none': 1,
            'ndvi': 2,
            'evi': 3,
            'savi': 2,
            'nbr': 2,
            'msavi': 2,
            'ndwi': 2
        }
        return requirements.get(method.lower(), 1)

    @staticmethod
    def get_processor(method: str) -> Callable:
        """Returns the appropriate band arithmetic function based on method name."""
        processors = {
            'none': calculate_none,
            'ndvi': calculate_ndvi,
            'evi': calculate_evi,
            'savi': calculate_savi,
            'nbr': calculate_nbr,
            'msavi': calculate_msavi,
            'ndwi': calculate_ndwi
        }
        
        if method.lower() not in processors:
            return calculate_none
        
        return processors[method.lower()]

    @staticmethod
    def process_bands(method: str, bands: Dict[str, np.ndarray], **kwargs) -> np.ndarray:
        """Process the bands using the specified arithmetic method."""
        processor = BandArithmeticFactory.get_processor(method)
        method = method.lower()

        # Verify available bands
        available_bands = len(bands)
        required_bands = BandArithmeticFactory.get_required_bands(method)
        
        if available_bands < required_bands:
            raise ValueError(f"{method} requires {required_bands} bands, but only {available_bands} provided")
            
        # Use available bands based on count
        if method == 'none':
            return processor(bands['band_1'])
        elif method == 'evi' and available_bands >= 3:
            return processor(bands['band_3'], bands['band_2'], bands['band_1'])
        elif method in ['msavi', 'ndwi'] and available_bands >= 2:
            return processor(bands['band_2'], bands['band_1'])
        elif available_bands >= 2:
            # For all other two-band indices (ndvi, savi, nbr)
            return processor(bands['band_2'], bands['band_1'])
        else:
            return processor(bands['band_1'])