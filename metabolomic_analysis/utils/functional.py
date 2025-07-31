import matplotlib.pyplot as plt
from io import BytesIO

def save_fig():
    """
    Save the current matplotlib figure to PNG bytes and return the bytes.

    Returns:
        bytes: PNG image data as bytes
    """
    # Create a BytesIO buffer to hold the image data
    buffer = BytesIO()

    # Save the current figure to the buffer in PNG format
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)

    # Get the bytes from the buffer
    buffer.seek(0)  # Reset buffer position to beginning
    png_bytes = buffer.getvalue()

    # Close the buffer to free memory
    buffer.close()
    plt.close()

    return png_bytes