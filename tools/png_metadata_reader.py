from PIL import Image
import sys


if __name__ == '__main__':

    with Image.open(sys.argv[1]) as img:

        # Retrieve metadata
        metadata = img.info

        # Print metadata
        for key, value in metadata.items():
            print(f"{key}: {value}")
