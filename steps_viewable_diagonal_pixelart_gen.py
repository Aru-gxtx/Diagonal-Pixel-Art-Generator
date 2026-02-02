import numpy as np
from PIL import Image, ImageFilter, ImageOps
import matplotlib.pyplot as plt
import io
from pyscript import display, when

def generate_final_diagonal_canvas(image_source, target_block_count=275):
    steps = {}
    
    try:
        img = Image.open(image_source)

        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3]) 
            img = bg
        else:
            img = img.convert('RGB')

        img = ImageOps.autocontrast(img)
        steps['1. Original'] = np.array(img)

        img_rot = img.rotate(-45, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
        steps['2. Rotated'] = np.array(img_rot)

        gray_rot = img_rot.convert("L")
        edges_high_res = gray_rot.filter(ImageFilter.FIND_EDGES)
        edges_high_res = edges_high_res.filter(ImageFilter.MaxFilter(3))
        steps['3. Edges'] = np.array(edges_high_res)

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
        
        final_canvas = final_canvas.reshape((44, 44))
        steps['4. Final Pixel Art'] = final_canvas
        
        return steps

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
    
    steps = generate_final_diagonal_canvas(io.BytesIO(file_bytes))
    
    if steps is not None:
        plt.figure(figsize=(15, 5))
        
        cols = len(steps)
        for i, (title, data) in enumerate(steps.items()):
            plt.subplot(1, cols, i+1)
            
            cmap = 'gray'
            if len(data.shape) == 3: cmap = None # RGB images
            if 'Final' in title: cmap = 'Greys'
            if 'Final' in title:
                vis_data = (data > 0).astype(np.uint8) * 255
                temp_img = Image.fromarray(vis_data)
                
                rotated_final = temp_img.rotate(45, resample=Image.NEAREST, expand=True)
                
                plt.imshow(rotated_final, cmap=cmap)
            else:
                plt.imshow(data, cmap=cmap)
                 
            plt.title(title)
            plt.axis('off')

        plt.tight_layout()
        
        display(plt.gcf(), target="plot-output", append=False)
