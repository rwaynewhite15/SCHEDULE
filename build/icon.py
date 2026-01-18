from PIL import Image, ImageDraw, ImageFont
import os

def create_calendar_icon():
    """Create a modern calendar icon"""
    # Create a 256x256 image with transparency
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw calendar background (rounded rectangle)
    margin = 20
    calendar_rect = [margin, margin + 30, size - margin, size - margin]
    
    # Draw shadow
    shadow_offset = 8
    draw.rounded_rectangle(
        [calendar_rect[0] + shadow_offset, calendar_rect[1] + shadow_offset,
         calendar_rect[2] + shadow_offset, calendar_rect[3] + shadow_offset],
        radius=20,
        fill=(0, 0, 0, 60)
    )
    
    # Draw main calendar body (white)
    draw.rounded_rectangle(calendar_rect, radius=20, fill='white')
    
    # Draw calendar header (accent color)
    header_rect = [margin, margin + 30, size - margin, margin + 80]
    draw.rounded_rectangle(header_rect, radius=20, fill='#2c3e50')
    draw.rectangle([margin, margin + 60, size - margin, margin + 80], fill='#2c3e50')
    
    # Draw binding rings
    ring_y = margin + 30
    ring_radius = 8
    for x in [70, 120, 136, 186]:
        draw.ellipse([x - ring_radius, ring_y - ring_radius,
                     x + ring_radius, ring_y + ring_radius],
                    fill='#34495e')
        draw.ellipse([x - ring_radius + 2, ring_y - ring_radius + 2,
                     x + ring_radius - 2, ring_y + ring_radius - 2],
                    fill='white')
    
    # Draw date number (large)
    try:
        # Try to use a system font
        font_large = ImageFont.truetype("arial.ttf", 80)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw "18" (day)
    text = "18"
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = margin + 110
    draw.text((text_x, text_y), text, fill='#2c3e50', font=font_large)
    
    # Draw "JAN" (month)
    month_text = "JAN"
    bbox = draw.textbbox((0, 0), month_text, font=font_small)
    month_width = bbox[2] - bbox[0]
    month_x = (size - month_width) // 2
    month_y = text_y + 75
    draw.text((month_x, month_y), month_text, fill='#7f8c8d', font=font_small)
    
    # Save as .ico with multiple sizes
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save('calendar_app.ico', format='ICO', sizes=icon_sizes)
    print("✓ Icon created: calendar_app.ico")
    
    # Also save as PNG for preview
    img.save('calendar_app_preview.png', format='PNG')
    print("✓ Preview created: calendar_app_preview.png")

if __name__ == "__main__":
    create_calendar_icon()
    print("\nIcon files created successfully!")
    print("You can now use 'calendar_app.ico' with PyInstaller.")