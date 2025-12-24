import numpy as np
from PIL import Image, ImageFilter, ImageOps
import matplotlib.pyplot as plt

def generate_high_fidelity_steps(image_path, target_block_count=275):
    steps = {}
    
    try:
        img = Image.open(image_path)
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3]) 
            img = bg
        else:
            img = img.convert('RGB')
        
        img = ImageOps.autocontrast(img)
        steps['1. Original'] = np.array(img)

        img_rot = img.rotate(-45, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
        steps['2. Rotated (Hi-Res)'] = np.array(img_rot)

        gray_rot = img_rot.convert("L")
        
        edges_high_res = gray_rot.filter(ImageFilter.FIND_EDGES)
        
        edges_high_res = edges_high_res.filter(ImageFilter.MaxFilter(3))
        
        steps['3. Edge Map (Hi-Res)'] = np.array(edges_high_res)

        img_small = edges_high_res.resize((44, 44), Image.Resampling.LANCZOS)
        
        edge_data = np.array(img_small, dtype=np.float32)
        steps['4. Downsampled Edges'] = edge_data

        edge_data[0, :] = -1
        edge_data[-1, :] = -1
        edge_data[:, 0] = -1
        edge_data[:, -1] = -1
        
        flat_data = edge_data.flatten()
        sorted_indices = np.argsort(flat_data)
        top_indices = sorted_indices[-target_block_count:]
        
        final_canvas = np.zeros_like(flat_data, dtype=np.int16)
        final_canvas[top_indices] = 275
        final_canvas = final_canvas.reshape((44, 44))
        
        steps['5. Final (275 Blocks)'] = final_canvas
        
        return steps

    except Exception as e:
        print(f"Error: {e}")
        return None

def show_dashboard(steps):
    if steps is None: return

    plt.figure(figsize=(15, 5))
    
    cols = len(steps)
    for i, (title, data) in enumerate(steps.items()):
        plt.subplot(1, cols, i+1)
        
        cmap = 'gray'
        if len(data.shape) == 3: cmap = None # RGB
        if 'Final' in title: cmap = 'Greys' # Ink look
            
        plt.imshow(data, cmap=cmap)
        plt.title(title)
        plt.axis('off')

    plt.tight_layout()
    plt.show()

input_img = "gallegodz.png" 
debug_data = generate_high_fidelity_steps(input_img, target_block_count=275)
show_dashboard(debug_data)
