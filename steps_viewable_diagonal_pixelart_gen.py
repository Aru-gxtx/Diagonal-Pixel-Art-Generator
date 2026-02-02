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
        document.getElementById("plot-output").innerHTML = ""
        
        steps = generate_final_diagonal_canvas(io.BytesIO(image_bytes))
        if steps is not None:
            plt.close('all') # Proper cleanup of Matplotlib figures
            fig = plt.figure(figsize=(15, 5))
            cols = len(steps)
            for i, (title, data) in enumerate(steps.items()):
                plt.subplot(1, cols, i+1)
                cmap = 'gray'
                if len(data.shape) == 3: cmap = None 
                if 'Final' in title: cmap = 'Greys'

                plt.imshow(data, cmap=cmap, vmin=(0 if 'Final' in title else None), vmax=(275 if 'Final' in title else None))
                plt.title(title)
                plt.axis('off')
            
            plt.tight_layout()
            display(fig, target="plot-output")
    except Exception as e:
        console.log(f"Render Error: {str(e)}")

@when("paste", "#paste-box")
async def handle_paste(event):
    # Prevent any default browser behavior
    event.preventDefault()

    items = event.clipboardData.items
    for i in range(items.length):
        if "image" in items.item(i).type:
            document.getElementById("plot-output").innerHTML = "Searching for edges..."
            
            blob = items.item(i).getAsFile()
            array_buffer = await blob.arrayBuffer()
            
            process_and_render(array_buffer.to_bytes())
            return # Exit after finding the first image

    document.getElementById("plot-output").innerHTML = "No image found in clipboard. Please copy an image first."

@when("change", "#file-upload")
async def handle_upload(event):
    files = event.target.files
    if files.length > 0:
        file = files.item(0)
        array_buffer = await file.arrayBuffer()
        process_and_render(array_buffer.to_bytes())
        
