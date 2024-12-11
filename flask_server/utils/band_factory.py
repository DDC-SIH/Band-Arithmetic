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
        """Process the bands using the specified arithmetic method.
        Bands are numbered according to their order in the input URLs."""
        processor = BandArithmeticFactory.get_processor(method)
        method = method.lower()

        # Match frontend band arithmetic formulas
        if method == 'ndvi':
            # NIR and RED
            return processor(bands['band_2'], bands['band_1'])
        elif method == 'evi':
            # NIR, RED, BLUE
            return processor(bands['band_3'], bands['band_2'], bands['band_1'])
        elif method == 'savi':
            # NIR and RED
            return processor(bands['band_2'], bands['band_1'])
        elif method == 'nbr':
            # NIR and SWIR
            return processor(bands['band_2'], bands['band_1'])
        elif method == 'msavi':
            # NIR and RED
            return processor(bands['band_2'], bands['band_1'])
        elif method == 'ndwi':
            # GREEN and NIR
            return processor(bands['band_2'], bands['band_3'])
        else:
            return processor(bands['band_1'])