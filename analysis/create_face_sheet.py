"""
Create a contact sheet showing all extracted faces.
"""
from PIL import Image
from pathlib import Path

def create_contact_sheet():
    """Create a contact sheet of all faces."""
    faces_dir = Path('../graphics/faces_fixed')
    faces = sorted(faces_dir.glob('face_*.png'))
    
    if not faces:
        print("No faces found!")
        return
    
    print(f"Creating contact sheet from {len(faces)} faces...")
    
    # Load all faces
    images = []
    for face_path in faces:
        img = Image.open(face_path)
        images.append((face_path.stem, img))
    
    # Calculate grid
    cols = 8
    rows = (len(images) + cols - 1) // cols
    
    # Get max dimensions
    max_w = max(img.width for _, img in images)
    max_h = max(img.height for _, img in images)
    
    # Add padding
    cell_w = max_w + 4
    cell_h = max_h + 4
    
    # Create sheet
    sheet_w = cols * cell_w
    sheet_h = rows * cell_h
    
    sheet = Image.new('RGB', (sheet_w, sheet_h), (32, 32, 32))
    
    # Paste faces
    for i, (name, img) in enumerate(images):
        row = i // cols
        col = i % cols
        
        x = col * cell_w + 2
        y = row * cell_h + 2
        
        # Convert palette image to RGB
        rgb_img = img.convert('RGB')
        sheet.paste(rgb_img, (x, y))
    
    # Save
    output = Path('../graphics/pilot_faces_sheet.png')
    sheet.save(output)
    
    print(f"Contact sheet saved: {output}")
    print(f"Size: {sheet_w}x{sheet_h}")
    print(f"Grid: {cols} cols × {rows} rows")

if __name__ == '__main__':
    create_contact_sheet()
