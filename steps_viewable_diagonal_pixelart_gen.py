from js import document, console, window, Uint8Array
import numpy as np
from PIL import Image, ImageFilter, ImageOps
import matplotlib.pyplot as plt
import io
from pyscript import display, when

def generate_final_diagonal_canvas(image_source, target_block_count=275, grid_size=44):
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

        img_small = edges_high_res.resize((grid_size, grid_size), Image.Resampling.LANCZOS)
        edge_data = np.array(img_small, dtype=np.float32)

        edge_data[0, :] = -1
        edge_data[-1, :] = -1
        edge_data[:, 0] = -1
        edge_data[:, -1] = -1

        flat_data = edge_data.flatten()
        sorted_indices = np.argsort(flat_data)
        
        safe_block_count = min(target_block_count, len(flat_data))
        top_indices = sorted_indices[-safe_block_count:]

        final_canvas = np.zeros_like(flat_data, dtype=np.int16)
        final_canvas[top_indices] = target_block_count 
        
        final_canvas = final_canvas.reshape((grid_size, grid_size))
        steps['4. Final Pixel Art'] = final_canvas

        return steps
    except Exception as e:
        console.log(f"Generator Error: {e}")
        return None

last_image_bytes = None 

def run_pipeline(image_bytes):
    global last_image_bytes
    last_image_bytes = image_bytes 
    
    log = document.getElementById("debug-log")
    
    try:
        c_val = document.getElementById("block-count").value
        target_count = int(c_val) if c_val else 275
        
        g_val = document.getElementById("grid-size").value
        target_grid = int(g_val) if g_val else 44
        
    except:
        target_count = 275
        target_grid = 44

    try:
        log.innerText = f"Processing: {target_grid}x{target_grid} grid, {target_count} blocks..."
        
        stream = io.BytesIO(bytes(image_bytes))
        
        steps = generate_final_diagonal_canvas(stream, target_block_count=target_count, grid_size=target_grid)
        
        if steps:
            document.getElementById("plot-output").innerHTML = ""
            plt.close('all')
            fig = plt.figure(figsize=(16, 6))
            cols = len(steps)
            for i, (title, data) in enumerate(steps.items()):
                plt.subplot(1, cols, i+1)
                cmap = 'gray'
                if len(data.shape) == 3: cmap = None 
                if 'Final' in title: cmap = 'Greys'
                plt.imshow(data, cmap=cmap, aspect='equal')
                plt.title(title)
                plt.axis('off')
            plt.tight_layout()
            display(fig, target="plot-output")
            log.innerText = "Done!"
        else:
            log.innerText = "Error during generation."
    except Exception as e:
        log.innerText = f"Pipeline Error: {e}"

@when("change", "#block-count")
def on_blocks_change(event):
    if last_image_bytes is not None:
        run_pipeline(last_image_bytes)

@when("change", "#grid-size")
def on_grid_change(event):
    if last_image_bytes is not None:
        run_pipeline(last_image_bytes)

@when("change", "#file-upload")
async def handle_upload(event):
    if event.target.files.length > 0:
        file = event.target.files.item(0)
        array_buffer = await file.arrayBuffer()
        js_array = Uint8Array.new(array_buffer)
        run_pipeline(js_array)

window.process_image_from_js = run_pipeline

document.getElementById("debug-log").innerText = "System Ready. Paste away!"
document.getElementById("debug-log").style.color = "green"
