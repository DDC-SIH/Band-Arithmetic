
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def apply_colormap(data: np.ndarray, colormap_name: str, min_val: float, max_val: float, steps: int = 256) -> np.ndarray:
    """
    Apply a colormap to the data.

    Parameters:
    - data: The raster data as a NumPy array.
    - colormap_name: The name of the colormap to apply.
    - min_val: The minimum value for normalization.
    - max_val: The maximum value for normalization.
    - steps: Number of steps in the colormap.

    Returns:
    - colorized_data: The data with the colormap applied.
    """
    # Normalize the data
    normalized_data = (data - min_val) / (max_val - min_val)
    normalized_data = np.clip(normalized_data, 0, 1)

    # Get the colormap
    colormap = cm.get_cmap(colormap_name, steps)

    # Apply the colormap
    colorized_data = colormap(normalized_data)

    # Convert to 8-bit unsigned integer
    colorized_data_uint8 = (colorized_data[:, :, :3] * 255).astype(np.uint8)

    return colorized_data_uint8