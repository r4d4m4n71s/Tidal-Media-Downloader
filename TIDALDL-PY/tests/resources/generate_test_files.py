import os
from PIL import Image, ImageDraw

def create_test_cover():
    """Create a test cover image."""
    # Create a 500x500 white image
    img = Image.new('RGB', (500, 500), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw some text
    draw.text((50, 200), 'Test Cover Art', fill='black')
    
    # Save the image
    img.save('cover.jpg', 'JPEG')

if __name__ == "__main__":
    create_test_cover()