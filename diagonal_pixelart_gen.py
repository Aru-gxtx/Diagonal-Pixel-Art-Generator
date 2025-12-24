import numpy as np
from PIL import Image, ImageFilter, ImageOps
import matplotlib.pyplot as plt

def generate_final_diagonal_canvas(image_path, target_block_count=275):
    try:
        img = Image.open(image_path)

        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3]) 
            img = bg
        else:
            img = img.convert('RGB')

        img = ImageOps.autocontrast(img)

        img_rot = img.rotate(-45, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))

        gray_rot = img_rot.convert("L")

        edges_high_res = gray_rot.filter(ImageFilter.FIND_EDGES)

        edges_high_res = edges_high_res.filter(ImageFilter.MaxFilter(3))

        img_small = edges_high_res.resize((44, 44), Image.Resampling.LANCZOS)
        edge_data = np.array(img_small, dtype=np.float32)

        edge_data[0, :] = -1
        edge_data[-1, :] = -1
        edge_data[:, 0] = -1
        edge_data[:, -1] = -1

        flat_data = edge_data.flatten()
        sorted_indices = np.argsort(flat_data)

        top_indices = sorted_indices[-target_block_count:]

        final_canvas = np.zeros_like(flat_data, dtype=np.int16)
        final_canvas[top_indices] = 275 # Set active blocks to value 275
        
        return final_canvas.reshape((44, 44))

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def visualize_final_result(canvas_data):

    if canvas_data is None:
        return

    count = np.sum(canvas_data == 275)
    print(f"Processing Complete.")
    print(f"Grid Dimensions: {canvas_data.shape}")
    print(f"Total Blocks Used: {count}")

    rows, cols = canvas_data.shape
    x = np.arange(cols + 1)
    y = np.arange(rows + 1)
    X, Y = np.meshgrid(x, y)
   
    iso_X = (X - Y)
    iso_Y = (X + Y) * 0.5 
    
    plt.figure(figsize=(8, 8))

    plt.pcolormesh(iso_X, iso_Y, np.flipud(canvas_data), 
                   cmap='Greys', vmin=0, vmax=275, edgecolors='none')
    
    plt.axis('equal')
    plt.axis('off')
    plt.title(f"Final Diagonal Canvas\nActive Blocks: {count} | Value: 275")
    plt.show()

input_img = "gallegodz.png" 

canvas = generate_final_diagonal_canvas(input_img, target_block_count=275)
visualize_final_result(canvas)
