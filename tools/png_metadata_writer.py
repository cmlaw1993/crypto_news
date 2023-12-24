from PIL import Image
from PIL.PngImagePlugin import PngInfo
import sys


if __name__ == '__main__':
    
    # Open an existing image
    with Image.open(sys.argv[1]) as img:
        # Create a PngInfo object to hold metadata
        metadata = PngInfo()

        # Add standard and custom metadata
        metadata.add_text('Title', 'Daily Crypto News')
        metadata.add_text('Author', 'The New Satellite')
        metadata.add_text('Description', 'Daily Crypto News')
        metadata.add_text('Copyright', 'The New Satellite')
        metadata.add_text('Caption', 'Daily Crypto News')
        metadata.add_text('Keywords', 'Daily Crypto News, Cryptocurrency News, Cryptocurrency, Crypto Today, Latest Crypto News, Crypto News Today')

        # Save the image with new metadata
        img.save(sys.argv[1], pnginfo=metadata)
