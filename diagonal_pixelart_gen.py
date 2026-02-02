import numpy as np
from PIL import Image, ImageFilter, ImageOps
import matplotlib.pyplot as plt
import io # Needed to handle image data from the browser
from pyscript import display, when # Needed for the web interface

def generate_final_diagonal_canvas(image_source, target_block_count=275):
    try:
        img = Image.open(image_source)

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
        final_canvas[top_indices] = 275
        
        return final_canvas.reshape((44, 44))

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

@when("change", "#file-upload")
async def process_image(event):
    file_list = event.target.files
    if not file_list:
        return
    first_file = file_list.item(0)
    
    array_buffer = await first_file.arrayBuffer()
    file_bytes = array_buffer.to_bytes()
    
    canvas = generate_final_diagonal_canvas(io.BytesIO(file_bytes))
    
    if canvas is not None:
        rows, cols = canvas.shape
        x, y = np.arange(cols + 1), np.arange(rows + 1)
        X, Y = np.meshgrid(x, y)
        iso_X, iso_Y = (X - Y), (X + Y) * 0.5 
        
        plt.figure(figsize=(8, 8))
        plt.pcolormesh(iso_X, iso_Y, np.flipud(canvas), 
                       cmap='Greys', vmin=0, vmax=275, edgecolors='none')
        plt.axis('equal')
        plt.axis('off')
        
        display(plt.gcf(), target="plot-output", append=False)
