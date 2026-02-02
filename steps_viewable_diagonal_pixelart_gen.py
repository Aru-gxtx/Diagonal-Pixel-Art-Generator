from js import document # Import document to listen for global events
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
        
def process_and_render(image_bytes):
    try:
        steps = generate_final_diagonal_canvas(io.BytesIO(image_bytes))
        if steps is not None:
            plt.clf() # Clear the previous figure to prevent memory leaks
            plt.figure(figsize=(15, 5))
            cols = len(steps)
            for i, (title, data) in enumerate(steps.items()):
                plt.subplot(1, cols, i+1)
                cmap = 'gray'
                if len(data.shape) == 3: cmap = None 
                if 'Final' in title: cmap = 'Greys'

                if 'Final' in title:
                     plt.imshow(data, cmap=cmap, vmin=0, vmax=275)
                else:
                     plt.imshow(data, cmap=cmap)
                plt.title(title)
                plt.axis('off')
            plt.tight_layout()
            display(plt.gcf(), target="plot-output", append=False)
    except Exception as e:
        console.log(f"Error in render: {str(e)}")

@when("paste", "body")
async def handle_paste(event):
    items = event.clipboardData.items
    
    for i in range(items.length):
        item = items.item(i)
        if "image" in item.type:
            event.preventDefault()
            
            blob = item.getAsFile()
            array_buffer = await blob.arrayBuffer()
            image_bytes = array_buffer.to_bytes()
            
            process_and_render(image_bytes)
            break
            
