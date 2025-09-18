import os
import ipywidgets as widgets
from IPython.display import display, HTML
import threading
import time
import sys
import subprocess
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
from functools import partial

# -----------------------------
# Bootstrap required Python packages when run as the first script
# This will attempt to install missing packages quietly using pip.
# -----------------------------
def _bootstrap_requirements():
    required = ["ipywidgets", "requests"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except Exception:
            missing.append(pkg)

    if not missing:
        return

    # Attempt to install missing packages
    print(f"Installing missing packages: {missing}")
    try:
        # Use sys.executable to call the same Python interpreter
        cmd = [sys.executable, "-m", "pip", "install"] + missing
        import subprocess
        subprocess.check_call(cmd)
    except Exception as e:
        print("Automatic installation of requirements failed:", e)
        print("Please manually install the required packages and re-run this script:")
        print("pip install ipywidgets requests")

_bootstrap_requirements()


# -----------------------------
# Civitai helper functions
# -----------------------------
def extract_civitai_model_id(url):
    """Extract model ID from Civitai download URL"""
    import re
    if not url or 'civitai.com' not in url:
        return None
    match = re.search(r'/models/(\d+)', url)
    if match:
        return match.group(1)
    return None


def get_civitai_model_url(download_url):
    """Convert download URL to model page URL"""
    model_id = extract_civitai_model_id(download_url)
    if model_id:
        return f"https://civitai.com/models/{model_id}"
    return None

# -----------------------------
# Environment Variables
# -----------------------------
public_ip = os.environ.get('RUNPOD_PUBLIC_IP', 'localhost')
external_port = os.environ.get('RUNPOD_TCP_PORT_8188', '8188')
public_url = f"http://{public_ip}:{external_port}/"

# -----------------------------
# Enhanced CSS Styling (Simplified for better compatibility)
# -----------------------------
css = """
<style>
    /* Scoped styles for Comfy UI widgets - do not affect the global Jupyter UI */
    .comfy-root {
        /* root container background and typography for the Comfy UI area only */
        background: #F5F5DC;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        overflow-x: hidden; /* prevent horizontal scroll inside the comfy area */
        box-sizing: border-box;
    }

    .comfy-root .widget-box {
        background: transparent !important;
    }

    .comfy-root .centered-vbox {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        min-height: 100vh !important;
        gap: 20px;
        padding: 30px 20px;
    }
    
    .comfy-root .homogenized-button {
        background: #E74C3C !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        border: none !important;
        width: 280px !important;
        height: 60px !important;
        font-size: 18px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    
    /* .homogenized-button:hover:not(:disabled) {
        background: linear-gradient(135deg, #C0392B 0%, #A93226 100%) !important;
        box-shadow: 0 0 20px 4px #FFF5E1 !important;
        transform: translateY(-3px) !important;
    } */
    
    .comfy-root .homogenized-button:disabled {
        background: linear-gradient(135deg, #95A5A6 0%, #7F8C8D 100%) !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    }

    /* When a button should keep its active color while disabled, add the 'preserve-color' class */
    .comfy-root .preserve-color:disabled {
        background: #E74C3C !important;
        color: white !important;
        cursor: not-allowed !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    
    .comfy-root .comfy-title-normal {
        text-align: center;
        /* Responsive title: clamp between 36px and 96px, scale with viewport */
        font-size: clamp(36px, 8vw, 96px);
        font-weight: bold;
        color: #1A237E;
        margin: 0px 0 15px 0; /* increased bottom margin */
        line-height: 1.2; /* increase to show full letters including descenders */
        padding-bottom: 10px; /* extra space for descenders */
        text-shadow: 2px 2px 4px rgba(0,0,0,0.08);
        max-width: 100%;
        overflow: visible; /* allow descenders to render outside the line box */
        word-wrap: break-word;
        box-sizing: border-box;
    }
    
    .comfy-root .status-text {
        text-align: center;
        font-size: 22px;
        color: #1A237E; /* match title color */
        font-weight: bold;
        margin: 2px 0px 2px 0px;
    }
    
    .comfy-root .progress-container {
        background-color: #F5F5DC;
        width: 300px;
        height: 24px; /* reserve a fixed height even when empty */
        border-radius: 10px;
        border: 2px solid #C0392B;
        margin-top: 16px; /* increased space between status row and progress bar (approx 4x) */
        margin-bottom: 20px;
        display: block; /* keep the placeholder visible so layout doesn't shift */
        overflow: hidden;
    }
    
    .comfy-root .progress-bar {
        background: #E74C3C;
        height: 100%;
        width: 0%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }
    
    .comfy-root .comfy-link {
        font-size: 24px;
        font-weight: bold;
        text-decoration: none;
        color: #E74C3C;
        padding: 12px 24px;
        border: 2px solid #E74C3C;
        border-radius: 8px;
        transition: all 0.3s ease;
        margin-bottom: 30px;
    }
    
    /* .comfy-link:hover {
        background-color: #E74C3C;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
    } */
    
    /* Category Button Styling */
    .comfy-root .category-button {
        background: #F5F5DC !important;
        border: 2px solid #C0392B !important;
        border-radius: 8px !important;
        width: 280px !important;
        height: 40px !important;
        margin: 5px 0 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        color: #1A237E !important;
        font-weight: bold !important;
    }
    
    /* .category-button:hover {
        background: linear-gradient(135deg, #F0F0DC 0%, #E8E4D5 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    } */
    
    /* Table Styling */
    .comfy-root .item-container {
        width: 100%;
        max-width: 800px;
        background: #F5F5DC;
        border: 2px solid #C0392B;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .comfy-root .item-row {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #E8E4D5;
    }
    
    .item-row:last-child {
        border-bottom: none;
    }
    
    
    
    /* Custom Toggle Switch */
    .comfy-root .custom-toggle {
        width: 60px;
        height: 30px;
        background-color: #F5F5DC;
        border: 2px solid #C0392B;
        border-radius: 15px;
        position: relative;
        cursor: pointer;
        /* Only animate background color and the knob position — keep size/box model constant */
        transition: background-color 0.12s ease;
        margin-right: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .comfy-root .custom-toggle.active {
        background-color: #E74C3C;
        /* Keep shape and size constant when active: remove shadows or other effects */
        box-shadow: none !important;
    }
    
    .custom-toggle.disabled {
        cursor: not-allowed;
        background-color: #BDC3C7;
    }
    
    .custom-toggle::after {
        content: '';
        width: 24px;
        height: 24px;
        /* Solid white knob for consistent appearance in all states */
        background: white;
        border-radius: 50%;
        position: absolute;
        top: 1px;
        left: 1px;
        /* animate only the knob position; keep color static (white) */
        transition: left 0.12s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .custom-toggle.active::after {
        /* Only move the knob when active; color stays white */
        left: 33px;
    }
    
    /* .custom-toggle:hover:not(.disabled) {
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    } */
    
    .comfy-root .item-info {
        flex: 1;
    }
    
    .comfy-root .item-name {
        font-size: 16px;
        font-weight: bold;
        color: #1A237E;
        margin-bottom: 4px;
    }
    
    .comfy-root .item-description {
        font-size: 14px;
        color: #7F8C8D;
        font-style: italic;
    }

    /* Clickable model name styling */
    .comfy-root .item-name a {
        color: #1A237E !important;
        text-decoration: none !important;
        font-weight: bold !important;
        transition: color 0.3s ease !important;
    }

    .item-name a:hover {
        color: #E74C3C !important;
        text-decoration: underline !important;
    }

    .item-name a:visited {
        color: #1A237E !important;
    }
    
    .comfy-root .required-badge {
        background: white;
        color: #F5F5DC;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 12px;
        margin-left: 10px;
        font-weight: bold;
    }
    
    .comfy-root .optional-badge {
        background: linear-gradient(135deg, #95A5A6 0%, #7F8C8D 100%);
        color: white;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 12px;
        margin-left: 10px;
        font-weight: bold;
    }
    
    /* Hide default ipywidgets styling */
    /* hide toggle if present inside comfy-root only */
    .comfy-root .widget-toggle-button {
        display: none !important;
    }

    /* Remove default outlines and add a light beige glow for focus states */
    .comfy-root button:focus,
    .comfy-root a:focus,
    .comfy-root input:focus {
        outline: none !important;
        box-shadow: 0 0 4px 1px rgba(245, 245, 220, 0.8) !important; /* light beige glow */
        border-radius: 8px; /* keep consistent with your theme */
    }

    /* Ensure custom-toggle does NOT get a focus glow or extra shadow that changes perceived size */
    .comfy-root .custom-toggle:focus,
    .comfy-root .custom-toggle:active,
    .comfy-root .custom-toggle.active:focus {
        outline: none !important;
        box-shadow: none !important;
    }

    /* Lock box-sizing and remove margin/padding issues that may cause reflow in some renderers */
    .comfy-root .custom-toggle,
    .comfy-root .custom-toggle::after {
        box-sizing: border-box !important;
        -webkit-box-sizing: border-box !important;
    }

    /* Ensure the toggle's border and padding do not change between states */
    .comfy-root .custom-toggle,
    .comfy-root .custom-toggle.active {
        padding: 0 !important;
        border-width: 2px !important;
    }

    /* Civitai token input placed in the title row */
    .comfy-root .civit-token-wrapper {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        justify-content: flex-end;
    }

    .comfy-root .civit-token-input {
        background: linear-gradient(180deg, #0A5CFF 0%, #0747D1 100%);
        border: 2px solid #0639B2;
        color: white;
        height: 40px; /* match category-button height */
        width: 100%;
        max-width: 560px; /* prefer responsive width up to the desired size */
        padding: 6px 12px;
        border-radius: 8px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.15);
        font-size: 14px;
        outline: none;
    }
    /* Inner input should be white with dark text and inherit sizing from the container */
    .comfy-root .civit-token-input input,
    .comfy-root .civit-token-input .widget-text {
        background: white !important;
        border: none !important;
        color: #1A237E !important; /* dark blue/black text for readability */
        height: calc(100% - 4px) !important;
        width: calc(100% - 12px) !important;
        padding: 8px 6px !important;
        box-sizing: border-box !important;
        border-radius: 6px !important;
        text-align: center !important;
    }
    .comfy-root .civit-token-input input::placeholder {
        color: rgba(26,35,126,0.45) !important;
        text-align: center !important;
    }

    /* Get API Key link styling */
    .comfy-root .civitai-get-key-link a {
        color: white !important;
        text-decoration: none !important;
        font-weight: bold !important;
        font-size: 14px !important;
        margin-right: 12px !important;
        transition: color 0.3s ease !important;
    }

    .civitai-get-key-link a:hover {
        color: #F0F0F0 !important;
        text-decoration: underline !important;
    }

    /* Blue Open Comfy UI button styling - same visual tone as title */
    .comfy-root .open-comfy-blue {
        background: linear-gradient(180deg, #1A237E 0%, #0747D1 100%);
        color: white !important;
        border: 2px solid #0639B2 !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.15) !important;
        border-radius: 12px !important;
        width: 280px !important;
        height: 60px !important;
        font-size: 18px !important;
        cursor: pointer !important;
    }
    .open-link-frame {
        width: 280px;
        height: 60px;
        border: 2px solid #0639B2;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 12px;
        background: transparent;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    }

    .comfy-root .open-link-text {
        color: #1A237E;
        font-weight: bold;
        font-size: 22px;
        text-decoration: none;
        transition: color 0.3s ease;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .comfy-root .open-link-text:hover {
        color: white;
    }
</style>
"""

    /* Preset preview styles (permanent images under each preset) */
    .preset-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        margin: 8px 0 18px 0;
        width: 100%;
    }

    .preset-image-wrapper {
        display: flex;
        justify-content: center;
        width: 100%;
    }

    .preset-image {
        max-width: 400px;
        width: 100%;
        height: auto;
        border: 2px solid #C0392B;
        border-radius: 8px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
    }
</style>
"""
display(HTML(css))

# -----------------------------
# Title
# -----------------------------
from ipywidgets import Layout

# Title row with Civitai token input on the right
# Allow the title widget to size itself vertically so descenders (like the "y") are visible
title_html = widgets.HTML(
    value='<div class="comfy-title-normal">Comfy UI</div>',
    layout=Layout(height='auto')
)

# Civitai token input widget (bound to Python)
civitai_token_widget = widgets.Text(
    value='',
    placeholder='Civitai API token',
    layout=Layout(width='560px', height='40px')
)
# Apply the CSS class so the input inherits our blue styling
civitai_token_widget.add_class('civit-token-input')

# Title row: keep only the title (OPEN link will be positioned above the Start Up button)
title_row = widgets.VBox([
    widgets.HBox([title_html], layout=Layout(width='100%', justify_content='center', align_items='center'))
], layout=Layout(width='100%', align_items='center'))

display(title_row)

import base64
import os


def load_image_as_base64(image_path):
    """Load an image from `image_path` and return a data URI or None on failure."""
    try:
        # Resolve relative to the script directory when a relative path is provided
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = image_path if os.path.isabs(image_path) else os.path.join(base_dir, image_path)
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                # Guess mime from extension
                ext = os.path.splitext(full_path)[1].lower()
                mime = 'image/png'
                if ext in ['.jpg', '.jpeg']:
                    mime = 'image/jpeg'
                elif ext == '.webp':
                    mime = 'image/webp'
                return f'data:{mime};base64,{encoded}'
        return None
    except Exception:
        return None


def _build_preset_image_html(data_uri: str, alt_text: str = '') -> str:
    if not data_uri:
        return '<div style="color:#7F8C8D; font-style:italic; text-align:center; padding:12px;">Preview image not found.</div>'
    return f"<div class='preset-image-wrapper'><img class='preset-image' src='{data_uri}' alt='{alt_text}'/></div>"

def get_civitai_token():
    """Return the current value of the civitai token input."""
    return civitai_token_widget.value


def download_file(url, dest_path, cwd=None):
    """Download `url` to `dest_path`.
    If the URL is a Civitai API download and a token is provided by the user,
    include it as an Authorization: Bearer <token> header.
    Falls back to calling wget when requests-based download fails or when token is not provided.
    """
    import subprocess
    try:
        import requests
    except Exception:
        requests = None

    token = ''
    try:
        token = get_civitai_token() or ''
    except Exception:
        token = ''

    # Ensure destination directory exists
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    except Exception:
        pass

    is_civit = 'civitai.com' in (url or '')
    if is_civit and token and requests is not None:
        headers = {'Authorization': f'Bearer {token}'}
        try:
            with requests.get(url, headers=headers, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(dest_path, 'wb') as fh:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            fh.write(chunk)
            return True
        except Exception as e:
            print(f"Civitai download failed for {url}: {e}")
            # fall through to wget fallback

    # Fallback: use wget (system dependent)
    try:
        cmd = f"wget -O {dest_path} {url}"
        subprocess.run(cmd, shell=True, cwd=cwd, check=True)
        return True
    except Exception as e:
        print(f"Download failed for {url}: {e}")
        return False


# -----------------------------
# Parallel helpers (process-based) for faster downloads and clones
# -----------------------------
def download_file_process(url, dest_path, token=None):
    """Download file in a separate process - returns (success, message)"""
    try:
        import requests
        import os
        import subprocess
        # Ensure destination directory exists
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        except Exception:
            pass

        is_civit = 'civitai.com' in (url or '')
        if is_civit and token:
            headers = {'Authorization': f'Bearer {token}'}
            try:
                with requests.get(url, headers=headers, stream=True, timeout=300) as r:
                    r.raise_for_status()
                    with open(dest_path, 'wb') as fh:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                fh.write(chunk)
                return True, f"Downloaded: {os.path.basename(dest_path)}"
            except Exception:
                # Fall through to wget
                pass

        # Fallback: use wget
        try:
            cmd = f"wget -O '{dest_path}' '{url}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return True, f"Downloaded (wget): {os.path.basename(dest_path)}"
            else:
                return False, f"wget failed for {os.path.basename(dest_path)}: {result.stderr}"
        except Exception as e:
            return False, f"Download failed for {os.path.basename(dest_path)}: {str(e)}"
            
    except Exception as e:
        return False, f"Process error for {os.path.basename(dest_path)}: {str(e)}"


def clone_repo_process(repo_url, dest_path, repo_name):
    """Clone git repository in a separate process - returns (success, message)"""
    try:
        import subprocess
        import os
        # Ensure destination directory exists
        try:
            os.makedirs(dest_path, exist_ok=True)
        except Exception:
            pass
        # Clone the repository
        result = subprocess.run(
            f"git clone {repo_url}", 
            shell=True, 
            cwd=dest_path, 
            capture_output=True, 
            text=True, 
            timeout=300
        )
        if result.returncode == 0:
            # Try to install requirements if they exist
            req_path = os.path.join(dest_path, repo_name, "requirements.txt")
            if os.path.exists(req_path):
                pip_result = subprocess.run(
                    "../../venv/bin/pip install -r requirements.txt",
                    shell=True,
                    cwd=os.path.join(dest_path, repo_name),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if pip_result.returncode == 0:
                    return True, f"Cloned and installed: {repo_name}"
                else:
                    return True, f"Cloned (pip install failed): {repo_name}"
            else:
                return True, f"Cloned: {repo_name}"
        else:
            return False, f"Git clone failed for {repo_name}: {result.stderr}"
        
    except Exception as e:
        return False, f"Clone error for {repo_name}: {str(e)}"


def run_parallel_downloads(download_tasks, clone_tasks, progress_callback=None):
    """Run downloads and clones in parallel with progress tracking"""
    total_tasks = len(download_tasks) + len(clone_tasks)
    completed_tasks = 0
    # Results storage
    download_results = []
    clone_results = []
    def update_progress():
        nonlocal completed_tasks
        completed_tasks += 1
        if progress_callback:
            progress = int((completed_tasks / total_tasks) * 100)
            progress_callback(progress)
    # Start download processes (10 workers)
    with ProcessPoolExecutor(max_workers=10) as download_executor:
        download_futures = {
            download_executor.submit(download_file_process, task['url'], task['dest_path'], task.get('token')): task
            for task in download_tasks
        }
        # Start clone processes (6 workers) 
        with ProcessPoolExecutor(max_workers=6) as clone_executor:
            clone_futures = {
                clone_executor.submit(clone_repo_process, task['url'], task['dest_path'], task['name']): task
                for task in clone_tasks
            }
            # Collect download results
            for future in as_completed(download_futures):
                task = download_futures[future]
                try:
                    success, message = future.result()
                    download_results.append({
                        'task': task,
                        'success': success,
                        'message': message
                    })
                    print(f"Download: {message}")
                except Exception as e:
                    download_results.append({
                        'task': task,
                        'success': False,
                        'message': f"Exception: {str(e)}"
                    })
                    print(f"Download failed: {task.get('name', 'Unknown')} - {str(e)}")
                finally:
                    update_progress()
            # Collect clone results
            for future in as_completed(clone_futures):
                task = clone_futures[future]
                try:
                    success, message = future.result()
                    clone_results.append({
                        'task': task,
                        'success': success,
                        'message': message
                    })
                    print(f"Clone: {message}")
                except Exception as e:
                    clone_results.append({
                        'task': task,
                        'success': False,
                        'message': f"Exception: {str(e)}"
                    })
                    print(f"Clone failed: {task.get('name', 'Unknown')} - {str(e)}")
                finally:
                    update_progress()
    return download_results, clone_results

# -----------------------------
# Status and Progress Bar (reserve space to avoid layout shifts)
# -----------------------------
# Pre-allocated hidden status placeholder (height reserved)
status_label = widgets.HTML(value="<div class='status-text' style='height: 26px; visibility: hidden;'>Placeholder</div>")

# Pre-allocated hidden progress container (space reserved; hidden by visibility)
progress_container = widgets.HTML(value="""
<div style="display:flex; justify-content:center; margin-bottom:20px;">
    <div class="progress-container" style="display:block; visibility: hidden;">
        <div class="progress-bar" style="width:0%;"></div>
    </div>
</div>
""")

# Download-only status and progress (reserve space like the main progress bar)
download_status_label = widgets.HTML(value="<div class='status-text' style='height: 26px; visibility: hidden;'>Downloading...</div>")

download_progress_container = widgets.HTML(value="""
<div style="display:flex; justify-content:center; margin-bottom:20px;">
    <div class="progress-container" style="display:block; visibility: hidden;">
        <div class="progress-bar" style="width:0%;"></div>
    </div>
</div>
""")

# -----------------------------
# Open Comfy UI Link
# -----------------------------
# Simple clickable text link in blue (visible from start). This uses the existing .comfy-link style.
open_link_html = widgets.HTML(value=f"<a href=\"{public_url}\" target=\"_blank\" class=\"open-link-text\">Open Comfy UI</a>")

# Frame the link and place it on the right above the Start Up button
open_link_frame = widgets.Box([open_link_html], layout=widgets.Layout(width='280px', height='60px'))

# -----------------------------
# Data Definitions
# -----------------------------
custom_nodes = [
    {
        "name": "ComfyUI-Manager",
        "url": "https://github.com/ltdrdata/ComfyUI-Manager.git",
        "info": "Essential node manager for ComfyUI",
        "required": True
    },
    {
        "name": "rgthree-comfy",
        "url": "https://github.com/rgthree/rgthree-comfy.git",
        "info": "Quality of life nodes and utilities",
        "required": False
    },
    {
        "name": "lora-info",
        "url": "https://github.com/jitcoder/lora-info.git",
        "info": "LoRA info node for detailed model information",
        "required": False
    },
    {
        "name": "ComfyUI-Impact-Pack",
        "url": "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git",
        "info": "Advanced image processing and segmentation nodes",
        "required": False
    },
    {
        "name": "ComfyUI-Easy-Use",
        "url": "https://github.com/yolain/ComfyUI-Easy-Use.git",
        "info": "Simplified workflow nodes for beginners",
        "required": False
    },
    {
        "name": "ComfyUI-Custom-Scripts",
        "url": "https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git",
        "info": "Custom scripts and workflow enhancements",
        "required": False
    },
    {
        "name": "ComfyUI-Inspyrenet-Rembg",
        "url": "https://github.com/john-mnz/ComfyUI-Inspyrenet-Rembg.git",
        "info": "Advanced background removal using Inspyrenet",
        "required": False
    },
    {
        "name": "Bjornulf_custom_nodes",
        "url": "https://github.com/justUmen/Bjornulf_custom_nodes.git",
        "info": "Specialized custom nodes by Bjornulf",
        "required": False
    },
    {
        "name": "comfy-image-saver",
        "url": "https://github.com/giriss/comfy-image-saver.git",
        "info": "Enhanced image saving with metadata",
        "required": False
    },
    {
        "name": "ComfyUI-Impact-Subpack",
        "url": "https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git",
        "info": "Additional impact pack nodes and utilities",
        "required": False
    },
    {
        "name": "was-node-suite-comfyui",
        "url": "https://github.com/WASasquatch/was-node-suite-comfyui.git",
        "info": "Comprehensive node suite with text and image tools",
        "required": False
    },
    {
        "name": "ComfyUI_JPS-Nodes",
        "url": "https://github.com/JPS-GER/ComfyUI_JPS-Nodes.git",
        "info": "JPS custom nodes for advanced workflows",
        "required": False
    },
    {
        "name": "comfyui_controlnet_aux",
        "url": "https://github.com/Fannovel16/comfyui_controlnet_aux.git",
        "info": "ControlNet auxiliary preprocessors and tools",
        "required": False
    },
    {
        "name": "ComfyUI-KJNodes",
        "url": "https://github.com/kijai/ComfyUI-KJNodes.git",
        "info": "KJ's collection of utility and processing nodes",
        "required": False
    },
    {
        "name": "ComfyUI_essentials",
        "url": "https://github.com/cubiq/ComfyUI_essentials.git",
        "info": "Essential utility nodes for common tasks",
        "required": False
    },
    {
        "name": "ComfyUI-enricos-nodes",
        "url": "https://github.com/erosDiffusion/ComfyUI-enricos-nodes.git",
        "info": "Enrico's specialized nodes for advanced features",
        "required": False
    },
    {
        "name": "ComfyUI-AnimateDiff-Evolved",
        "url": "https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git",
        "info": "Advanced AnimateDiff implementation for video generation",
        "required": False
    },
    {
        "name": "ComfyUI-VideoHelperSuite",
        "url": "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git",
        "info": "Comprehensive video processing and creation tools",
        "required": False
    },
    {
        "name": "ComfyUI-Advanced-ControlNet",
        "url": "https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git",
        "info": "Enhanced ControlNet nodes with advanced features",
        "required": False
    },
    {
        "name": "ComfyUI_IPAdapter_plus",
        "url": "https://github.com/cubiq/ComfyUI_IPAdapter_plus.git",
        "info": "IP-Adapter implementation with extra features",
        "required": False
    }
]

checkpoints = [
    # Pony Diffusion V6 XL (user requested) - high priority SDXL checkpoint
    {
        "name": "Pony_Diffusion_V6_XL.safetensors",
        "url": "https://civitai.com/api/download/models/290640?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "info": "Pony Diffusion V6 XL - Versatile SDXL checkpoint",
        "required": False,
        "filename": "Pony_Diffusion_V6_XL.safetensors"
    },
    # Additional SD1.5 variants requested by user (download into ComfyUI/models/checkpoints)
    {
        "name": "SD1.5_DreamShaper.safetensors",
        "url": "https://civitai.com/api/download/models/128713",
        "info": "DreamShaper SD1.5 variant",
        "required": False,
        "filename": "SD1.5_DreamShaper.safetensors"
    },
    {
        "name": "SD1.5_RevAnimated.safetensors",
        "url": "https://civitai.com/api/download/models/425083",
        "info": "RevAnimated SD1.5 variant",
        "required": False,
        "filename": "SD1.5_RevAnimated.safetensors"
    },
    {
        "name": "SD1.5_Epic_Realism.safetensors",
        "url": "https://civitai.com/api/download/models/143906",
        "info": "Epic Realism SD1.5 variant",
        "required": False,
        "filename": "SD1.5_Epic_Realism.safetensors"
    },
    {
        "name": "SD1.5_Deliberate.safetensors",
        "url": "https://huggingface.co/XpucT/Deliberate/resolve/main/Deliberate_v6.safetensors?download=true",
        "info": "Deliberate SD1.5 variant",
        "required": False,
        "filename": "SD1.5_Deliberate.safetensors"
    }
]

# Additional checkpoint bundles (SDXL, Illustrious, Pony, Flux)
extra_checkpoints = [
    {"name": "SDXL.safetensors", "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors?download=true", "filename": "SDXL.safetensors", "required": False},
    {"name": "SDXL_WildCard.safetensors", "url": "https://civitai.com/api/download/models/345685", "filename": "SDXL_WildCard.safetensors", "required": False},
    {"name": "SDXL_CyberRealisticXL.safetensors", "url": "https://civitai.com/api/download/models/1609607", "filename": "SDXL_CyberRealisticXL.safetensors", "required": False},
    {"name": "zavychromaxl_v80.safetensors", "url": "https://huggingface.co/misri/zavychromaxl_v80/resolve/main/zavychromaxl_v80.safetensors", "filename": "zavychromaxl_v80.safetensors", "required": False},
    {"name": "juggernautXL_version6Rundiffusion.safetensors", "url": "https://huggingface.co/lllyasviel/fav_models/resolve/main/fav/juggernautXL_version6Rundiffusion.safetensors", "filename": "juggernautXL_version6Rundiffusion.safetensors", "required": False},
    {"name": "DreamShaperXL.safetensors", "url": "https://civitai.com/api/download/models/351306", "filename": "DreamShaperXL.safetensors", "required": False},

    # Illustrious
    {"name": "Illustrious.safetensors", "url": "https://civitai.com/api/download/models/889818", "filename": "Illustrious.safetensors", "required": False},
    {"name": "Illustrious_AnIco.safetensors", "url": "https://civitai.com/api/download/models/1641205", "filename": "Illustrious_AnIco.safetensors", "required": False},
    {"name": "Illustrious_Illustrij.safetensors", "url": "https://civitai.com/api/download/models/2186168", "filename": "Illustrious_Illustrij.safetensors", "required": False},
    {"name": "Illustrious_ToonMerge.safetensors", "url": "https://civitai.com/api/download/models/1622588", "filename": "Illustrious_ToonMerge.safetensors", "required": False},
    {"name": "Illustrious_SEMImergeijV6.safetensors", "url": "https://civitai.com/api/download/models/1920758", "filename": "Illustrious_SEMImergeijV6.safetensors", "required": False},

    # Pony models
    {"name": "Pony.safetensors", "url": "https://civitai.com/api/download/models/290640", "filename": "Pony.safetensors", "required": False},
    {"name": "Pony_CyberRealistic.safetensors", "url": "https://civitai.com/api/download/models/2178176", "filename": "Pony_CyberRealistic.safetensors", "required": False},
    {"name": "Pony_Lucent.safetensors", "url": "https://civitai.com/api/download/models/1971591", "filename": "Pony_Lucent.safetensors", "required": False},
    {"name": "Pony_DucHaiten_Real.safetensors", "url": "https://civitai.com/api/download/models/695106", "filename": "Pony_DucHaiten_Real.safetensors", "required": False},
    {"name": "Pony_Real_Dream.safetensors", "url": "https://civitai.com/api/download/models/2129811", "filename": "Pony_Real_Dream.safetensors", "required": False},
    {"name": "Pony_Real_Merge.safetensors", "url": "https://civitai.com/api/download/models/994131", "filename": "Pony_Real_Merge.safetensors", "required": False},
    {"name": "Pony_Realism.safetensors", "url": "https://civitai.com/api/download/models/914390", "filename": "Pony_Realism.safetensors", "required": False},

    # Flux
    {"name": "flux1-dev-fp8.safetensors", "url": "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors?download=true", "filename": "flux1-dev-fp8.safetensors", "required": False},
    {"name": "Flux_Fill.safetensors", "url": "https://civitai.com/api/download/models/1086292", "filename": "Flux_Fill.safetensors", "required": False, "dest_dir": "models/diffusion_models"}
]

# Append extras to checkpoints list
for cp in extra_checkpoints:
    checkpoints.append(cp)

loras = []

# User-provided LoRA additions (SD1.5, SDXL, Illustrious, Pony)
user_loras = [
    # SD1.5 LoRAs
    {"name": "Stable_Diffusion_Loras_Detailed_Eyes.safetensors", "url": "https://civitai.com/api/download/models/145907", "filename": "Stable_Diffusion_Loras_Detailed_Eyes.safetensors", "dest_dir": "models/loras"},
    {"name": "Stable_Diffusion_Loras_Midjourney_Mimic.safetensors", "url": "https://civitai.com/api/download/models/283697", "filename": "Stable_Diffusion_Loras_Midjourney_Mimic.safetensors", "dest_dir": "models/loras"},
    {"name": "Stable_Diffusion_Loras_Extremely_Detailed.safetensors", "url": "https://civitai.com/api/download/models/258687", "filename": "Stable_Diffusion_Loras_Extremely_Detailed.safetensors", "dest_dir": "models/loras"},
    {"name": "Stable_Diffusion_Loras_Juggernot_Cinematic.safetensors", "url": "https://civitai.com/api/download/models/131991", "filename": "Stable_Diffusion_Loras_Juggernot_Cinematic.safetensors", "dest_dir": "models/loras"},
    {"name": "Stable_Diffusion_Loras_Detail_Tweaker.safetensors", "url": "https://civitai.com/api/download/models/135867", "filename": "Stable_Diffusion_Loras_Detail_Tweaker.safetensors", "dest_dir": "models/loras"},
    {"name": "Stable_Diffusion_Loras_Wowifier.safetensors", "url": "https://civitai.com/api/download/models/217866", "filename": "Stable_Diffusion_Loras_Wowifier.safetensors", "dest_dir": "models/loras"},

    # SDXL LoRAs
    {"name": "SDXL_Pop_Art_Style.safetensors", "url": "https://civitai.com/api/download/models/192584", "filename": "SDXL_Pop_Art_Style.safetensors", "dest_dir": "models/loras"},
    {"name": "SDXL_loras_2Steps.safetensors", "url": "https://huggingface.co/ByteDance/SDXL-Lightning/resolve/main/sdxl_lightning_2step_lora.safetensors?download=true", "filename": "SDXL_loras_2Steps.safetensors", "dest_dir": "models/loras"},
    {"name": "Hyper-SDXL-8steps-CFG-lora.safetensors", "url": "https://huggingface.co/ByteDance/Hyper-SD/resolve/main/Hyper-SDXL-8steps-CFG-lora.safetensors", "filename": "Hyper-SDXL-8steps-CFG-lora.safetensors", "dest_dir": "models/loras"},
    {"name": "SDXL_lightning_8_steps.safetensors", "url": "https://civitai.com/api/download/models/391999", "filename": "SDXL_lightning_8_steps.safetensors", "dest_dir": "models/loras"},
    {"name": "SDXL_lightning_2_steps.safetensors", "url": "https://civitai.com/api/download/models/391994", "filename": "SDXL_lightning_2_steps.safetensors", "dest_dir": "models/loras"},

    # Illustrious LoRAs
    {"name": "Illustrious_USNR_Style.safetensors", "url": "https://civitai.com/api/download/models/959419", "filename": "Illustrious_USNR_Style.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_Gennesis.safetensors", "url": "https://civitai.com/api/download/models/1219983", "filename": "Illustrious_Gennesis.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_Loras_Hassaku_Shiro_Styles.safetensors", "url": "https://civitai.com/api/download/models/1580764", "filename": "Illustrious_Loras_Hassaku_Shiro_Styles.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_Loras_Power_Puff_Mix.safetensors", "url": "https://civitai.com/api/download/models/1456601", "filename": "Illustrious_Loras_Power_Puff_Mix.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_Loras_Detailer_Tool.safetensors", "url": "https://civitai.com/api/download/models/1191626", "filename": "Illustrious_Loras_Detailer_Tool.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_loRA_Semi_real_Fantasy_illustrious.safetensors", "url": "https://civitai.com/api/download/models/1597800", "filename": "Illustrious_loRA_Semi_real_Fantasy_illustrious.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_loRA_Midjourney_watercolors.safetensors", "url": "https://civitai.com/api/download/models/1510865", "filename": "Illustrious_loRA_Midjourney_watercolors.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_loRA_Commix_style.safetensors", "url": "https://civitai.com/api/download/models/1227175", "filename": "Illustrious_loRA_Commix_style.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_loRA_detailrej.safetensors", "url": "https://civitai.com/api/download/models/1396529", "filename": "Illustrious_loRA_detailrej.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_loRA_Vixons_Dappled_Sunlight.safetensors", "url": "https://civitai.com/api/download/models/1144547", "filename": "Illustrious_loRA_Vixons_Dappled_Sunlight.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_Vixon_Style.safetensors", "url": "https://civitai.com/api/download/models/1382407", "filename": "Illustrious_Vixon_Style.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_MagicalCircleTentacles.safetensors", "url": "https://civitai.com/api/download/models/1323341", "filename": "Illustrious_MagicalCircleTentacles.safetensors", "dest_dir": "models/loras"},
    {"name": "Illustrious_lora_Add_Super_Details.safetensors", "url": "https://civitai.com/api/download/models/1622964", "filename": "Illustrious_lora_Add_Super_Details.safetensors", "dest_dir": "models/loras"},

    # Pony LoRAs
    {"name": "PONY_Fernando_Style.safetensors", "url": "https://civitai.com/api/download/models/452367", "filename": "PONY_Fernando_Style.safetensors", "dest_dir": "models/loras"},
    {"name": "PONY_Majo.safetensors", "url": "https://civitai.com/api/download/models/835055", "filename": "PONY_Majo.safetensors", "dest_dir": "models/loras"},
    {"name": "PONY_Western_Comic_Art_Style.safetensors", "url": "https://civitai.com/api/download/models/871611", "filename": "PONY_Western_Comic_Art_Style.safetensors", "dest_dir": "models/loras"},
    {"name": "PONY_Incase_unaesthetic_style.safetensors", "url": "https://civitai.com/api/download/models/1128016", "filename": "PONY_Incase_unaesthetic_style.safetensors", "dest_dir": "models/loras"},
    {"name": "Pony_Lora_Water_Color_Anime.safetensors", "url": "https://civitai.com/api/download/models/725772", "filename": "Pony_Lora_Water_Color_Anime.safetensors", "dest_dir": "models/loras"},
    {"name": "Pony_Lora_Water_Color.safetensors", "url": "https://civitai.com/api/download/models/720004", "filename": "Pony_Lora_Water_Color.safetensors", "dest_dir": "models/loras"},
    {"name": "Pony_Lora_Sketch_Illustration.safetensors", "url": "https://civitai.com/api/download/models/882225", "filename": "Pony_Lora_Sketch_Illustration.safetensors", "dest_dir": "models/loras"},
    {"name": "Pony_Peoples_Work.safetensors", "url": "https://civitai.com/api/download/models/1036362", "filename": "Pony_Peoples_Work.safetensors", "dest_dir": "models/loras"}
]

# Additional Pony-related LoRAs requested by user
user_loras.extend([
    {
        "name": "Disney_Princess_XL_v2.0.safetensors",
        "url": "https://civitai.com/api/download/models/244808",
        "filename": "Disney_Princess_XL_v2.0.safetensors",
        "dest_dir": "models/loras",
        "required": False
    },
    {
        "name": "ExpressiveH_Hentai_Style.safetensors",
        "url": "https://civitai.com/api/download/models/382152?type=Model&format=SafeTensor",
        "filename": "ExpressiveH_Hentai_Style.safetensors",
        "dest_dir": "models/loras",
        "required": False
    },
    {
        "name": "Vixons_Pony_Gothic_Neon_v1.0.safetensors",
        "url": "https://civitai.com/api/download/models/398847?type=Model&format=SafeTensor",
        "filename": "Vixons_Pony_Gothic_Neon_v1.0.safetensors",
        "dest_dir": "models/loras",
        "required": False
    },
    {
        "name": "Incase_Style_PonyXL_v3.0.safetensors",
        "url": "https://civitai.com/api/download/models/436219?type=Model&format=SafeTensor",
        "filename": "Incase_Style_PonyXL_v3.0.safetensors",
        "dest_dir": "models/loras",
        "required": False
    }
])

# Append user-provided LoRAs
for ul in user_loras:
    # maintain the simple info and required flag defaults used elsewhere
    entry = {
        'name': ul.get('name'),
        'url': ul.get('url'),
        'info': ul.get('name'),
        'required': False,
    }
    # include optional fields used by downloader
    if 'filename' in ul:
        entry['filename'] = ul['filename']
    if 'dest_dir' in ul:
        entry['dest_dir'] = ul['dest_dir']
    loras.append(entry)

# Flux LoRAs provided by user
flux_loras = [
    {"name": "Flux_lora_Semirealisticportraitpainting.safetensors", "url": "https://civitai.com/api/download/models/978472", "filename": "Flux_lora_Semirealisticportraitpainting.safetensors", "dest_dir": "models/loras"},
    {"name": "Flux_lora_Velvetv2.safetensors", "url": "https://civitai.com/api/download/models/967375", "filename": "Flux_lora_Velvetv2.safetensors", "dest_dir": "models/loras"},
    {"name": "Flux_lora_RetroAnimeStyle.safetensors", "url": "https://civitai.com/api/download/models/806265", "filename": "Flux_lora_RetroAnimeStyle.safetensors", "dest_dir": "models/loras"},
    {"name": "Flux_lora_VelvetMythicFantasyRealistic_Fantasy.safetensors", "url": "https://civitai.com/api/download/models/1227179", "filename": "Flux_lora_VelvetMythicFantasyRealistic_Fantasy.safetensors", "dest_dir": "models/loras"},
    {"name": "Flux_lora_VelvetMythicFantasyGothicLines.safetensors", "url": "https://civitai.com/api/download/models/1202162", "filename": "Flux_lora_VelvetMythicFantasyGothicLines.safetensors", "dest_dir": "models/loras"},
    {"name": "Flux_lora_Mezzotint.safetensors", "url": "https://civitai.com/api/download/models/757030", "filename": "Flux_lora_Mezzotint.safetensors", "dest_dir": "models/loras"},
    {"name": "uso-flux1-dit-lora-v1.safetensors", "url": "https://huggingface.co/Comfy-Org/USO_1.0_Repackaged/resolve/main/split_files/loras/uso-flux1-dit-lora-v1.safetensors", "filename": "uso-flux1-dit-lora-v1.safetensors", "dest_dir": "models/loras"}
]

for fl in flux_loras:
    entry = {
        'name': fl.get('name'),
        'url': fl.get('url'),
        'info': fl.get('name'),
        'required': False,
    }
    entry['filename'] = fl['filename']
    entry['dest_dir'] = fl['dest_dir']
    loras.append(entry)

clip_models = [
    {
        "name": "CLIP ViT-L/14",
        "url": "https://huggingface.co/openai/clip-vit-large-patch14",
        "info": "Standard CLIP model for text encoding",
        "required": False
    },
    {
        "name": "CLIP ViT-B/32",
        "url": "https://huggingface.co/openai/clip-vit-base-patch32",
        "info": "Smaller CLIP model for faster processing",
        "required": False
    },
    {
        "name": "CLIP G",
        "url": "https://huggingface.co/laion/CLIP-ViT-g-14-laion2B-s12B-b42K",
        "info": "Large CLIP G model for SDXL",
        "required": False
    }
]

# Replaced CLIP backends provided by user (will download into models/clip)
clip_models = [
    {
        "name": "clip_l.safetensors",
        "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors?download=true",
        "info": "Flux clip_l encoder",
        "required": False,
        "filename": "clip_l.safetensors",
        "dest_dir": "models/clip"
    },
    {
        "name": "t5xxl_fp16.safetensors",
        "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors?download=true",
        "info": "Flux t5xxl text encoder",
        "required": False,
        "filename": "t5xxl_fp16.safetensors",
        "dest_dir": "models/clip"
    },
    {
        "name": "clip_g.safetensors",
        "url": "https://huggingface.co/calcuis/sd3.5-large-gguf/resolve/7f72f2a432131bba82ecd1aafb931ac99f0f05f7/clip_g.safetensors?download=true",
        "info": "Large CLIP G encoder",
        "required": False,
        "filename": "clip_g.safetensors",
        "dest_dir": "models/clip"
    }
]

clip_vision_models = [
    {
        "name": "CLIP Vision ViT-L",
        "url": "https://huggingface.co/openai/clip-vit-large-patch14",
        "info": "CLIP vision encoder for image understanding",
        "required": False
    },
    {
        "name": "CLIP Vision G",
        "url": "https://huggingface.co/laion/CLIP-ViT-g-14-laion2B-s12B-b42K",
        "info": "Large CLIP vision model for advanced image processing",
        "required": False
    },
    {
        "name": "IP-Adapter CLIP Vision",
        "url": "https://huggingface.co/h94/IP-Adapter",
        "info": "Specialized CLIP vision for IP-Adapter workflows",
        "required": False
    }
]

# Replaced CLIP Vision models as requested (download into models/clip_vision)
clip_vision_models = [
    {
        "name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
        "url": "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors",
        "info": "CLIP ViT-H-14 encoder (IP-Adapter repack)",
        "required": False,
        "filename": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
        "dest_dir": "models/clip_vision"
    },
    {
        "name": "CLIP-ViT-bigG-14-laion2B-39B-b160k.safetensors",
        "url": "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/image_encoder/model.safetensors",
        "info": "CLIP ViT bigG encoder for SDXL",
        "required": False,
        "filename": "CLIP-ViT-bigG-14-laion2B-39B-b160k.safetensors",
        "dest_dir": "models/clip_vision"
    },
    {
        "name": "model_l.safetensors",
        "url": "https://huggingface.co/openai/clip-vit-large-patch14/resolve/main/model.safetensors?download=true",
        "info": "OpenAI CLIP ViT-L model",
        "required": False,
        "filename": "model_l.safetensors",
        "dest_dir": "models/clip_vision"
    },
    {
        "name": "clip-vision_vit-h.safetensors",
        "url": "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors",
        "info": "Alternate vit-h encoder",
        "required": False,
        "filename": "clip-vision_vit-h.safetensors",
        "dest_dir": "models/clip_vision"
    },
    {
        "name": "clip_vision_h.safetensors",
        "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors?download=true",
        "info": "Comfy repackaged clip_vision_h",
        "required": False,
        "filename": "clip_vision_h.safetensors",
        "dest_dir": "models/clip_vision"
    },
    {
        "name": "sigclip_vision_patch14_384.safetensors",
        "url": "https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors?download=true",
        "info": "SigCLIP vision model",
        "required": False,
        "filename": "sigclip_vision_patch14_384.safetensors",
        "dest_dir": "models/clip_vision"
    }
]

vae_models = [
    {
        "name": "SDXL VAE",
        "url": "https://huggingface.co/stabilityai/sdxl-vae",
        "info": "Standard VAE for SDXL models",
        "required": False
    },
    {
        "name": "VAE MSE 840k",
        "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original",
        "info": "High quality VAE for better image details",
        "required": False
    },
    {
        "name": "Kl-f8-anime2",
        "url": "https://huggingface.co/hakurei/waifu-diffusion-v1-4",
        "info": "VAE optimized for anime-style images",
        "required": False
    }
]

# User-provided VAE replacements
vae_models = [
    {
        "name": "SDXL_Vae.safetensors",
        "url": "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors?download=true",
        "info": "Official SDXL VAE",
        "required": False,
        "filename": "SDXL_Vae.safetensors",
        "dest_dir": "models/vae"
    },
    {
        "name": "ae.safetensors",
        "url": "https://huggingface.co/Comfy-Org/Lumina_Image_2.0_Repackaged/resolve/main/split_files/vae/ae.safetensors?download=true",
        "info": "Lumina ae VAE",
        "required": False,
        "filename": "ae.safetensors",
        "dest_dir": "models/vae"
    }
]

controlnet_models = [
    {
        "name": "ControlNet Canny",
        "url": "https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0",
        "info": "Canny edge detection ControlNet for SDXL",
        "required": False
    },
    {
        "name": "ControlNet Depth",
        "url": "https://huggingface.co/diffusers/controlnet-depth-sdxl-1.0",
        "info": "Depth map ControlNet for SDXL",
        "required": False
    },
    {
        "name": "ControlNet OpenPose",
        "url": "https://huggingface.co/thibaud/controlnet-openpose-sdxl-1.0",
        "info": "Human pose detection ControlNet for SDXL",
        "required": False
    }
]

# Replaced ControlNet models provided by user (download into models/controlnet)
controlnet_models = [
    {
        "name": "FLUX.1-dev-Controlnet-Union.safetensors",
        "url": "https://huggingface.co/InstantX/FLUX.1-dev-Controlnet-Union/resolve/main/diffusion_pytorch_model.safetensors",
        "info": "FLUX.1 dev Controlnet union",
        "required": False,
        "filename": "FLUX.1-dev-Controlnet-Union.safetensors",
        "dest_dir": "models/controlnet"
    },
    {
        "name": "control_lora_rank128_v11f1e_sd15_tile_fp16.safetensors",
        "url": "https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_lora_rank128_v11f1e_sd15_tile_fp16.safetensors",
        "info": "Control Lora rank128 tile fp16",
        "required": False,
        "filename": "control_lora_rank128_v11f1e_sd15_tile_fp16.safetensors",
        "dest_dir": "models/controlnet"
    },
    {
        "name": "t2i-adapter-lineart-sdxl-1.0_fp16.safetensors",
        "url": "https://huggingface.co/TencentARC/t2i-adapter-lineart-sdxl-1.0/resolve/main/diffusion_pytorch_model.fp16.safetensors?download=true",
        "info": "t2i adapter lineart sdxl fp16",
        "required": False,
        "filename": "t2i-adapter-lineart-sdxl-1.0_fp16.safetensors",
        "dest_dir": "models/controlnet"
    },
    {
        "name": "control_v11p_sd15_inpaint_fp16.safetensors",
        "url": "https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11p_sd15_inpaint_fp16.safetensors",
        "info": "inpaint control v11p sd15 fp16",
        "required": False,
        "filename": "control_v11p_sd15_inpaint_fp16.safetensors",
        "dest_dir": "models/controlnet"
    },
    {
        "name": "controlnet-union-sdxl-1.0_promax.safetensors",
        "url": "https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/resolve/main/diffusion_pytorch_model_promax.safetensors?download=true",
        "info": "ControlNet union for SDXL",
        "required": False,
        "filename": "controlnet-union-sdxl-1.0_promax.safetensors",
        "dest_dir": "models/controlnet"
    },
    {
        "name": "control_lora_rank128_v11f1p_sd15_depth_fp16.safetensors",
        "url": "https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_lora_rank128_v11f1p_sd15_depth_fp16.safetensors?download=true",
        "info": "Control Lora rank128 depth fp16",
        "required": False,
        "filename": "control_lora_rank128_v11f1p_sd15_depth_fp16.safetensors",
        "dest_dir": "models/controlnet"
    }
]

upscale_models = [
    {
        "name": "Real-ESRGAN x4",
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        "info": "4x upscaling model for general images",
        "required": False
    },
    {
        "name": "Real-ESRGAN Anime",
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
        "info": "4x upscaling model optimized for anime images",
        "required": False
    },
    {
        "name": "LDSR",
        "url": "https://heibox.uni-heidelberg.de/f/578df07c8fc04ffbadf3/?dl=1",
        "info": "Latent diffusion super-resolution model",
        "required": False
    }
]

# Replaced Upscale model list provided by user
upscale_models = [
    {"name": "4x_foolhardy_Remacri.pth", "url": "https://huggingface.co/FacehugmanIII/4x_foolhardy_Remacri/resolve/main/4x_foolhardy_Remacri.pth?download=true", "filename": "4x_foolhardy_Remacri.pth", "dest_dir": "models/upscale_models", "required": False},
    {"name": "RealESRGAN_x4plus.pth", "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth", "filename": "RealESRGAN_x4plus.pth", "dest_dir": "models/upscale_models", "required": False},
    {"name": "4x-UltraSharp.safetensors", "url": "https://civitai.com/api/download/models/125843", "filename": "4x-UltraSharp.safetensors", "dest_dir": "models/upscale_models", "required": False},
    {"name": "4x_NMKD_Siax_200k.pth", "url": "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_NMKD-Siax_200k.pth?download=true", "filename": "4x_NMKD_Siax_200k.pth", "dest_dir": "models/upscale_models", "required": False},
    {"name": "RealESRGAN_x4plus_anime_and_illustrations_6B.pth", "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth", "filename": "RealESRGAN_x4plus_anime_and_illustrations_6B.pth", "dest_dir": "models/upscale_models", "required": False},
    {"name": "4x_NMKD-Superscale-SP_178000_G.pth", "url": "https://huggingface.co/gemasai/4x_NMKD-Superscale-SP_178000_G/resolve/main/4x_NMKD-Superscale-SP_178000_G.pth", "filename": "4x_NMKD-Superscale-SP_178000_G.pth", "dest_dir": "models/upscale_models", "required": False},
    {"name": "OmniSR_X2_DIV2K.safetensors", "url": "https://huggingface.co/Acly/Omni-SR/resolve/main/OmniSR_X2_DIV2K.safetensors", "filename": "OmniSR_X2_DIV2K.safetensors", "dest_dir": "models/upscale_models", "required": False},
    {"name": "OmniSR_X3_DIV2K.safetensors", "url": "https://huggingface.co/Acly/Omni-SR/resolve/main/OmniSR_X3_DIV2K.safetensors", "filename": "OmniSR_X3_DIV2K.safetensors", "dest_dir": "models/upscale_models", "required": False},
    {"name": "OmniSR_X4_DIV2K.safetensors", "url": "https://huggingface.co/Acly/Omni-SR/resolve/main/OmniSR_X4_DIV2K.safetensors", "filename": "OmniSR_X4_DIV2K.safetensors", "dest_dir": "models/upscale_models", "required": False}
]

additional_downloads = [
    {
        "name": "uso-flux1-projector-v1.safetensors",
        "url": "https://huggingface.co/Comfy-Org/USO_1.0_Repackaged/resolve/main/split_files/model_patches/uso-flux1-projector-v1.safetensors",
        "info": "USO Flux1 projector model patch",
        "required": False,
        "filename": "uso-flux1-projector-v1.safetensors",
        "dest_dir": "models/model_patches"
    },
    {
        "name": "Flux_Redux.safetensors",
        "url": "https://civitai.com/api/download/models/1086258",
        "info": "Flux Redux style model",
        "required": False,
        "filename": "Flux_Redux.safetensors",
        "dest_dir": "models/style_models"
    }
]

# Embeddings collection (new category)
embeddings = [
    {
        "name": "EasyNegative.pt",
        "url": "https://civitai.com/api/download/models/9208?type=Model&format=SafeTensor&size=full&fp=fp16",
        "info": "EasyNegative embedding for better negative prompts (version 9208)",
        "required": False,
        "filename": "EasyNegative.pt",
        "dest_dir": "models/embeddings"
    }
]

# (toggle state and widget mapping for `embeddings` will be initialized
# later automatically when `category_data` is processed)

# -----------------------------
# Additional Pony/Illustrious Models
# -----------------------------

# 1️⃣ A‑mix [Illustrious] Checkpoint
checkpoints.append(
    {
        "name": "A-mix_Illustrious_v1915059.safetensors",
        "website_url": "https://civitai.com/models/1692152/a-mix-illustrious?modelVersionId=1915059",
        "download_url": "https://civitai.com/api/download/models/1692152?modelVersionId=1915059&format=SafeTensor",
        "info": "A‑mix [Illustrious] checkpoint version 1915059",
        "required": False,
        "filename": "A-mix_Illustrious_v1915059.safetensors",
        "dest_dir": "models/checkpoints"
    }
)

# 2️⃣ Ri‑mix – Style LORA [PONY + Illustrious + FLUX]
loras.append(
    {
        "name": "Ri-mix_Style_LORA_PONY_Illustrious_FLUX_v1918677.safetensors",
        "website_url": "https://civitai.com/models/996220/ri-mix-style-lora-pony-illustrious-flux?modelVersionId=1918677",
        "download_url": "https://civitai.com/api/download/models/996220?modelVersionId=1918677&format=SafeTensor",
        "info": "Ri‑mix – Style LORA [PONY + Illustrious + FLUX], version 1918677",
        "required": False,
        "filename": "Ri-mix_Style_LORA_PONY_Illustrious_FLUX_v1918677.safetensors",
        "dest_dir": "models/loras"
    }
)

# -----------------------------
# Optional: Add to category_data if not already (category_data is defined later)
# -----------------------------
# -----------------------------
# Additional user-provided models (corrected/verified)
# These use the same structure as other entries and use the key 'url'
# so the existing download logic will pick them up.

# CyberRealistic Pony v13.0 (Corrected)
checkpoints.append(
    {
        "name": "CyberRealistic_Pony_v13.0.safetensors",
        "website_url": "https://civitai.com/models/443821/cyberrealistic-pony",
        # download URL points to the version-specific API endpoint; keep as `url` for downloader
        "url": "https://civitai.com/api/download/models/2178176",
        "info": "CyberRealistic Pony v13.0 - High-quality SDXL Pony model",
        "required": False,
        "filename": "CyberRealistic_Pony_v13.0.safetensors",
        "dest_dir": "models/checkpoints"
    }
)

# ExpressiveH Style LoRA (Corrected)
loras.append(
    {
        "name": "ExpressiveH_Hentai_Style_PonyXL.safetensors",
        "website_url": "https://civitai.com/models/413320/expressiveh-hentai-lora-style",
        "url": "https://civitai.com/api/download/models/464404",
        "info": "ExpressiveH Hentai LoRA Style - PonyXL compatible",
        "required": False,
        "filename": "ExpressiveH_Hentai_Style_PonyXL.safetensors",
        "dest_dir": "models/loras"
    }
)

# -----------------------------
# Slider LoRAs (placeholders - need verification on Civitai)
# These are intentionally left as placeholders so you can fill the correct
# `website_url` / `url` fields after locating the proper model/version IDs.
slider_loras = [
    {
        "name": "Pony_Amateur_LoRA_v1.safetensors",
        "website_url": "https://civitai.com/models/[NEED_TO_FIND]",
        "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "info": "Pony Amateur ✨ - Rough (V1)",
        "required": False,
        "filename": "Pony_Amateur_LoRA_v1.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Crazy_Girlfriend_Mix_XL_PONY.safetensors",
        "website_url": "https://civitai.com/models/[NEED_TO_FIND]",
        "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "info": "Crazy Girlfriend Mix [XL/PONY]",
        "required": False,
        "filename": "Crazy_Girlfriend_Mix_XL_PONY.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Insta_Baddie_PONY.safetensors",
        "website_url": "https://civitai.com/models/[NEED_TO_FIND]",
        "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "info": "Insta Baddie[PONY]",
        "required": False,
        "filename": "Insta_Baddie_PONY.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Real_Beauty_LoRA_v1.safetensors",
        "website_url": "https://civitai.com/models/[NEED_TO_FIND]",
        "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "info": "Real Beauty LoRA v1",
        "required": False,
        "filename": "Real_Beauty_LoRA_v1.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Dramatic_Lighting_Slider_v1.0.safetensors",
        "website_url": "https://civitai.com/models/[NEED_TO_FIND]",
        "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "info": "Dramatic Lighting Slider v1.0",
        "required": False,
        "filename": "Dramatic_Lighting_Slider_v1.0.safetensors",
        "dest_dir": "models/loras"
    }
]

# -----------------------------
# VERIFIED ALTERNATIVE LoRAs (if originals can't be found)
verified_loras = [
    {
        "name": "ExpressiveH_Mixed_Style_v3.safetensors",
        "website_url": "https://civitai.com/models/602698/expressiveh-vixons-gothic-neon-incase-mixed-style-v2-pony-xl-by-uoc",
        "url": "https://civitai.com/api/download/models/670947",
        "info": "ExpressiveH & Incase Mixed Style v3 - Illustrious/XL compatible",
        "required": False,
        "filename": "ExpressiveH_Mixed_Style_v3.safetensors",
        "dest_dir": "models/loras"
    }
]

# If you want to include verified alternatives automatically, uncomment the
# following line (we leave it commented so you can review before adding):
# loras.extend(verified_loras)

# Note: category_data is defined later and uses the `checkpoints` and `loras`
# variables, so the entries appended above will automatically be included in
# the GUI and the toggle initialization that runs after `category_data` is built.

# -----------------------------
# =============================================
# TRIPLE-CHECKED MODEL URLs - CRITICAL FIXES
# =============================================

# Checkpoints - CORRECTED URLs (converted download_url -> url)
checkpoints_data = [
    {
        "name": "Comic_Diffusion_PickleTensor",
        "website_url": "https://civitai.com/models/13/comic-diffusion",
        "url": "https://civitai.com/api/download/models/13?type=Model&format=PickleTensor&size=full&fp=fp16",
        "info": "Comic Diffusion checkpoint (PickleTensor)",
        "required": False,
        "filename": "Comic_Diffusion_PickleTensor.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "Superhero_Diffusion_PickleTensor",
        "website_url": "https://civitai.com/models/1/superhero-diffusion",
        "url": "https://civitai.com/api/download/models/1?type=Model&format=PickleTensor&size=full&fp=fp16",
        "info": "Superhero Diffusion checkpoint (PickleTensor)",
        "required": False,
        "filename": "Superhero_Diffusion_PickleTensor.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "helloComic",
        "website_url": "https://civitai.com/models/112857/hellocomic",
        "url": "https://civitai.com/api/download/models/112857?type=Model&format=SafeTensor&size=full&fp=fp16",
        "info": "helloComic checkpoint",
        "required": False,
        "filename": "helloComic.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "Nightvideionxl",
        "website_url": "https://civitai.com/models/577919/nightvideionxl",
        "url": "https://civitai.com/api/download/models/577919?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "info": "Nightvideionxl checkpoint",
        "required": False,
        "filename": "Nightvideionxl.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "AlbedoBase_XL",
        "website_url": "https://civitai.com/models/1041855/albedobase-xl",
        "url": "https://civitai.com/api/download/models/1041855?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "info": "AlbedoBase XL checkpoint",
        "required": False,
        "filename": "AlbedoBase_XL.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "Impasto_Virtuoso",
        "website_url": "https://civitai.com/models/516211/impasto-virtuoso",
        "url": "https://civitai.com/api/download/models/516211?type=Model&format=SafeTensor",
        "info": "Impasto Virtuoso checkpoint",
        "required": False,
        "filename": "Impasto_Virtuoso.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "SDVN7-NijiStyleXL",
        "website_url": "https://civitai.com/models/155870/sdvn7-nijistylexl",
        "url": "https://civitai.com/api/download/models/155870?type=Model&format=SafeTensor&size=full&fp=fp16",
        "info": "SDVN7-NijiStyleXL checkpoint",
        "required": False,
        "filename": "SDVN7-NijiStyleXL.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "Tamarin_XL",
        "website_url": "https://civitai.com/models/265836/tamarin-xl",
        "url": "https://civitai.com/api/download/models/265836?type=Model&format=SafeTensor&size=full&fp=fp16",
        "info": "Tamarin XL checkpoint",
        "required": False,
        "filename": "Tamarin_XL.safetensors",
        "dest_dir": "models/checkpoints"
    },
    {
        "name": "Animagine_XL_Realistic_Stylistic",
        "website_url": "https://civitai.com/models/1969417/animagine-xl-realistic-or-stylistic",
        "url": "https://civitai.com/api/download/models/1969417?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "info": "Animagine XL Realistic or Stylistic checkpoint",
        "required": False,
        "filename": "Animagine_XL_Realistic_Stylistic.safetensors",
        "dest_dir": "models/checkpoints"
    },
]

checkpoints.extend(checkpoints_data)

# -----------------------------
# LoRAs - NEED INDIVIDUAL VERIFICATION (converted download_url -> url)
loras_data = [
    {
        "name": "Jim_Lee_SD1.5_LoRA",
        "website_url": "https://civitai.com/models/10580/jim-lee",
        "url": "https://civitai.com/api/download/models/10580?type=Model&format=SafeTensor&size=full&fp=fp16",
        "info": "Jim Lee SD1.5 LoRA",
        "required": False,
        "filename": "Jim_Lee_SD1.5_LoRA.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Western_Comics_Art_LoRA",
        "website_url": "https://civitai.com/models/334734/western-comics-art",
        "url": "https://civitai.com/api/download/models/334734?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "info": "Western Comics Art LoRA",
        "required": False,
        "filename": "Western_Comics_Art_LoRA.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Marvelmixx_Flux_LoRA",
        "website_url": "https://civitai.com/models/909317/marvelmixx",
        "url": "https://civitai.com/api/download/models/909317?type=Model&format=SafeTensor",
        "info": "Marvelmixx Flux LoRA",
        "required": False,
        "filename": "Marvelmixx_Flux_LoRA.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "SXZ_Jim_Lee_FLUX",
        "website_url": "https://civitai.com/models/776104/sxz-jim-lee-flux",
        "url": "https://civitai.com/api/download/models/776104?type=Model&format=SafeTensor",
        "info": "SXZ Jim Lee FLUX LoRA",
        "required": False,
        "filename": "SXZ_Jim_Lee_FLUX.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Ri_Mix_LoRA",
        "website_url": "https://civitai.com/models/996220/ri-mix-style-lora-pony-illustrious-flux",
        # NOTE: This entry intentionally keeps the download ID as provided by the user
        # (could point to a different version). Double-check the version ID before use.
        "url": "https://civitai.com/api/download/models/1918677?type=Model&format=SafeTensor",
        "info": "Ri Mix LoRA",
        "required": False,
        "filename": "Ri_Mix_LoRA.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Jim_Lee_Flux_LoRA",
        "website_url": "https://civitai.com/models/1711873/jim-lee-flux",
        "url": "https://civitai.com/api/download/models/1711873?type=Model&format=SafeTensor",
        "info": "Jim Lee Flux LoRA",
        "required": False,
        "filename": "Jim_Lee_Flux_LoRA.safetensors",
        "dest_dir": "models/loras"
    }
]

loras.extend(loras_data)

# =============================================
# CRITICAL ISSUES FOUND - NOTES included in comments
# =============================================

# Category Data and State Management
# -----------------------------
category_data = {
    "custom-nodes": custom_nodes,
    "checkpoints": checkpoints,
    "loras": loras,
    "embeddings": embeddings,
    "clip": clip_models,
    "clip-vision": clip_vision_models,
    "vae": vae_models,
    "controlnet": controlnet_models,
    "upscale": upscale_models,
    "additional": additional_downloads
}

category_labels = {
    "custom-nodes": "Custom Nodes",
    "checkpoints": "Checkpoints",
    "loras": "LoRAs",
    "embeddings": "Embeddings",
    "clip": "CLIP Models",
    "clip-vision": "CLIP Vision",
    "vae": "VAE Models",
    "controlnet": "ControlNet Models",
    "upscale": "Upscale Models",
    "additional": "Additional Downloads"
}

# State management
expanded_state = False
category_expanded = {key: False for key in category_data.keys()}
toggle_states = {}

# Store actual toggle Button widgets so we can programmatically change them
toggle_widgets = {key: {} for key in category_data.keys()}

# Initialize toggle states
for category_id, items in category_data.items():
    toggle_states[category_id] = {}
    for i, item in enumerate(items):
        toggle_states[category_id][i] = item.get('required', False)

# -----------------------------
# Progress Update Function
# -----------------------------
def update_progress(percent):
    # Make the status and progress visible while preserving reserved layout space
    progress_container.value = f"""
    <div style="display:flex; justify-content:center; margin-bottom:20px;">
        <div class="progress-container" style="display:block; visibility: visible;">
            <div class="progress-bar" style="width:{percent}%;"></div>
        </div>
    </div>
    """
    status_label.value = "<div class='status-text' style='height: 26px; visibility: visible;'>is Installing...</div>"


def update_download_progress(percent, message: str = 'Downloading...'):
    """Update the download-only progress bar and its status text while preserving layout space."""
    download_progress_container.value = f"""
    <div style="display:flex; justify-content:center; margin-bottom:20px;">
        <div class="progress-container" style="display:block; visibility: visible;">
            <div class="progress-bar" style="width:{percent}%;"></div>
        </div>
    </div>
    """
    download_status_label.value = f"<div class='status-text' style='height: 26px; visibility: visible;'>{message}</div>"

# -----------------------------
# Python-driven Toggle Widget (no JS bridge)
# -----------------------------
def create_toggle_widget(category_id, item_id, item):
    """Return an ipywidgets HBox containing a styled toggle button and info.
    The visual styling uses the CSS classes defined above; we add/remove
    those classes on the Button widget to reflect state.
    """
    is_required = item.get('required', False)

    # Ensure toggle_states structure exists
    if category_id not in toggle_states:
        toggle_states[category_id] = {}
    toggle_states[category_id][item_id] = toggle_states.get(category_id, {}).get(item_id, item.get('required', False))

    # Visible button used as the toggle (we apply CSS classes to it)
    btn = widgets.Button(
        description="",
        layout=widgets.Layout(width='60px', height='30px'),
        disabled=is_required
    )
    # store the button so we can toggle it programmatically later
    try:
        toggle_widgets.setdefault(category_id, {})[item_id] = btn
    except Exception:
        toggle_widgets[category_id] = toggle_widgets.get(category_id, {})
        toggle_widgets[category_id][item_id] = btn
    # Add the CSS class names to the button DOM element
    try:
        btn.add_class('custom-toggle')
        if toggle_states[category_id][item_id]:
            btn.add_class('active')
        if is_required:
            btn.add_class('disabled')
    except Exception:
        # Older ipywidgets may not have add_class; fall back to _dom_classes
        if 'custom-toggle' not in btn._dom_classes:
            btn._dom_classes = btn._dom_classes + ['custom-toggle']
        if toggle_states[category_id][item_id] and 'active' not in btn._dom_classes:
            btn._dom_classes = btn._dom_classes + ['active']
        if is_required and 'disabled' not in btn._dom_classes:
            btn._dom_classes = btn._dom_classes + ['disabled']

    # Callback toggles Python-side state and updates CSS classes
    def _on_click(b):
        if is_required:
            return
        # flip state
        toggle_states[category_id][item_id] = not toggle_states[category_id][item_id]
        active = toggle_states[category_id][item_id]
        # update classes
        try:
            if active:
                btn.add_class('active')
            else:
                btn.remove_class('active')
        except Exception:
            # fallback
            if active and 'active' not in btn._dom_classes:
                btn._dom_classes = btn._dom_classes + ['active']
            if not active and 'active' in btn._dom_classes:
                btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

    btn.on_click(_on_click)

    # Info block
    # Show a 'Required' badge only for required items; hide any badge for optional items
    badge = '<span class="required-badge">Always included</span>' if is_required else ''
    # Only show descriptions for custom-nodes to reduce clutter for downloads
    desc_html = f"<div class='item-description'>{item.get('info','')}</div>" if category_id == 'custom-nodes' else ''

    # Make model names clickable if they point to civitai model downloads
    # Support either 'url' or legacy 'download_url' fields
    civitai_url = get_civitai_model_url(item.get('url') or item.get('download_url') or '')
    model_name = item.get('name', '')
    if civitai_url:
        name_html = f'<a href="{civitai_url}" target="_blank" style="color: #1A237E; text-decoration: none; font-weight: bold;">{model_name}</a>'
    else:
        name_html = f'<span style="color: #1A237E; font-weight: bold;">{model_name}</span>'

    info = widgets.HTML(value=f"""
        <div class='item-info'>
            <div class='item-name'>{name_html} {badge}</div>
            {desc_html}
        </div>
    """)

    row = widgets.HBox([btn, info], layout=widgets.Layout(align_items='center'))
    # add a class to the row so it matches your .item-row styling
    try:
        row.add_class('item-row')
        # also apply container class on parent later
    except Exception:
        if 'item-row' not in row._dom_classes:
            row._dom_classes = row._dom_classes + ['item-row']

    return row

# Helper to enable/disable flux-dev checkpoint and all custom nodes programmatically
def set_flux_and_custom(enabled: bool):
    """Set all custom-nodes toggles and the flux-dev checkpoint toggle on/off.
    This updates both the `toggle_states` dict and the visual button classes in `toggle_widgets`.
    """
    # Toggle all custom nodes
    for idx in range(len(custom_nodes)):
        toggle_states.setdefault('custom-nodes', {})[idx] = bool(enabled)
        btn = toggle_widgets.get('custom-nodes', {}).get(idx)
        if btn is not None:
            try:
                if enabled:
                    btn.add_class('active')
                else:
                    btn.remove_class('active')
            except Exception:
                if enabled and 'active' not in btn._dom_classes:
                    btn._dom_classes = btn._dom_classes + ['active']
                if not enabled and 'active' in btn._dom_classes:
                    btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

    # Find flux-dev checkpoint by name or filename in checkpoints
    flux_idx = None
    for i, cp in enumerate(checkpoints):
        name = (cp.get('name') or '').lower()
        fname = (cp.get('filename') or '').lower()
        if 'flux' in name or 'flux' in fname or 'flux1' in name:
            flux_idx = i
            break

    if flux_idx is not None:
        toggle_states.setdefault('checkpoints', {})[flux_idx] = bool(enabled)
        btn = toggle_widgets.get('checkpoints', {}).get(flux_idx)
        if btn is not None:
            try:
                if enabled:
                    btn.add_class('active')
                else:
                    btn.remove_class('active')
            except Exception:
                if enabled and 'active' not in btn._dom_classes:
                    btn._dom_classes = btn._dom_classes + ['active']
                if not enabled and 'active' in btn._dom_classes:
                    btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

# -----------------------------
# Startup Function
# -----------------------------
def startup_comfyui(b):
    b.disabled = True

    # Make status placeholder visible with text
    status_label.value = "<div class='status-text' style='height: 26px; visibility: visible;'>Installing ComfyUI...</div>"

    def run_installation():
        import subprocess
        import os

        def run_cmd(cmd, cwd=None):
            try:
                result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=300)
                return result.returncode == 0
            except subprocess.TimeoutExpired:
                return False
            except Exception:
                return False

        # Clone primary repository sequentially to prepare workspace
        repo_url = "https://github.com/comfyanonymous/ComfyUI.git"
        update_progress(5)
        run_cmd(f"git clone {repo_url}")

        # Create virtualenv and basic setup sequentially
        update_progress(15)
        run_cmd("python3 -m venv venv", cwd="ComfyUI")
        update_progress(25)
        run_cmd("venv/bin/pip install --upgrade pip", cwd="ComfyUI")
        update_progress(35)
        # Defer heavy package installs until after downloads/clones

        # Ensure directories exist for custom nodes and models
        run_cmd("mkdir -p custom_nodes", cwd="ComfyUI")
        run_cmd("mkdir -p models/checkpoints", cwd="ComfyUI")

        # Build clone tasks for selected custom nodes
        clone_tasks = []
        for i, node in enumerate(custom_nodes):
            if toggle_states['custom-nodes'].get(i, False):
                clone_tasks.append({
                    'url': node['url'],
                    'dest_path': os.path.join(os.getcwd(), 'ComfyUI', 'custom_nodes'),
                    'name': node['name']
                })

        # Build download tasks for all selected files
        download_tasks = []
        token = get_civitai_token() or None

        def add_item_downloads(items, category_name):
            for idx, item in enumerate(items):
                # Respect required flag or user selection
                if not toggle_states.get(category_name, {}).get(idx, False) and not item.get('required', False):
                    continue
                url = item.get('url') or item.get('download_url')
                if not url:
                    continue
                filename = item.get('filename') or url.split('/')[-1].split('?')[0]
                if not filename:
                    # skip items without a resolvable filename
                    continue
                dest_dir = item.get('dest_dir') or f"models/{category_name}"
                full_dest = os.path.join(os.getcwd(), 'ComfyUI', dest_dir)
                # Ensure the directory exists (runner also ensures but create now)
                try:
                    os.makedirs(full_dest, exist_ok=True)
                except Exception:
                    pass
                download_tasks.append({'url': url, 'dest_path': os.path.join(full_dest, filename), 'token': token, 'name': item.get('name')})

        add_item_downloads(additional_downloads, 'additional')
        add_item_downloads(checkpoints, 'checkpoints')
        add_item_downloads(loras, 'loras')
        add_item_downloads(embeddings, 'embeddings')
        add_item_downloads(clip_models, 'clip')
        add_item_downloads(clip_vision_models, 'clip-vision')
        add_item_downloads(vae_models, 'vae')
        add_item_downloads(controlnet_models, 'controlnet')
        add_item_downloads(upscale_models, 'upscale')

        update_progress(50)

        # Run downloads and clones in parallel
        try:
            dl_results, cl_results = run_parallel_downloads(download_tasks, clone_tasks, progress_callback=update_progress)
        except Exception as e:
            print(f"Parallel tasks failed: {e}")
            dl_results, cl_results = [], []

        update_progress(80)

        # After downloads/clones, install remaining python deps and torch
        run_cmd("venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121", cwd="ComfyUI")
        run_cmd("venv/bin/pip install -r requirements.txt", cwd="ComfyUI")

        update_progress(95)

        # Start ComfyUI
        try:
            subprocess.Popen(["venv/bin/python", "main.py", "--listen", "--port", "8188"], cwd="ComfyUI", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        update_progress(100)

        # Update visible status and re-enable button
        status_label.value = "<div class='status-text' style='height: 26px; visibility: visible;'>is up and running!</div>"
        b.disabled = False

    threading.Thread(target=run_installation).start()

# -----------------------------
# Create Category Widgets with Custom HTML
# -----------------------------
def create_category_widget(category_id, label, items):
    # Create toggle button
    def toggle_category_func(b):
        category_expanded[category_id] = not category_expanded[category_id]
        
        if category_expanded[category_id]:
            b.description = f"▲ {label}"
            category_containers[category_id].children[1].layout.display = 'block'
        else:
            b.description = f"▼ {label}"
            category_containers[category_id].children[1].layout.display = 'none'
    
    button = widgets.Button(
        description=f"▼ {label}",
        layout=widgets.Layout(width='280px', height='40px', margin='5px 0px'),
        style=widgets.ButtonStyle(button_color='#F5F5DC'),
        _dom_classes=['category-button']
    )
    button.on_click(toggle_category_func)
    # Create content VBox composed of the python-driven toggle rows
    rows = []
    for i, item in enumerate(items):
        row = create_toggle_widget(category_id, i, item)
        rows.append(row)

    content_box = widgets.VBox(rows, layout=widgets.Layout(display='none'))
    # wrap in a container to match previous styling
    content_html = widgets.VBox([widgets.HTML('<div class="item-container"></div>'), content_box], layout=widgets.Layout(display='none'))
    
    container = widgets.VBox([button, content_box], 
                           layout=widgets.Layout(align_items='center', margin='5px 0px'))
    
    return container

# Create startup button
startup_btn = widgets.Button(
    description="Start Up", 
    _dom_classes=["homogenized-button", "preserve-color"]
)
startup_btn.on_click(startup_comfyui)


# Helper: check if model directories exist (used to show/hide downloads-only button)
def model_dirs_exist():
    base = os.path.join(os.getcwd(), "ComfyUI", "models")
    required = [
        os.path.join(base, "Stable-diffusion"),
        os.path.join(base, "Lora"),
        os.path.join(base, "CLIP"),
        os.path.join(base, "CLIP-vision"),
        os.path.join(base, "VAE"),
        os.path.join(base, "ControlNet"),
        os.path.join(base, "ESRGAN"),
        os.path.join(base, "Extra"),
    ]
    return all(os.path.isdir(p) for p in required)


# Downloads-only handler: runs only the downloads (no clone/venv/start)
def start_downloads_only(b):
    b.disabled = True
    # show the main status placeholder (keep it hidden for installation) but enable download status
    status_label.value = "<div class='status-text' style='height: 26px; visibility: hidden;'>Placeholder</div>"
    download_status_label.value = "<div class='status-text' style='height: 26px; visibility: visible;'>Running downloads...</div>"

    def run_downloads():
        import os
        token = get_civitai_token() or None
        # Build download task list
        download_tasks = []

        def add_items(items, category_name):
            for idx, item in enumerate(items):
                if not toggle_states.get(category_name, {}).get(idx, False) and not item.get('required', False):
                    continue
                url = item.get('url') or item.get('download_url')
                if not url:
                    continue
                filename = item.get('filename') or url.split('/')[-1].split('?')[0]
                if not filename:
                    continue
                dest_dir = item.get('dest_dir') or f"models/{category_name}"
                full_dest = os.path.join(os.getcwd(), 'ComfyUI', dest_dir)
                try:
                    os.makedirs(full_dest, exist_ok=True)
                except Exception:
                    pass
                download_tasks.append({'url': url, 'dest_path': os.path.join(full_dest, filename), 'token': token, 'name': item.get('name')})

        add_items(additional_downloads, 'additional')
        add_items(checkpoints, 'checkpoints')
        add_items(loras, 'loras')
        add_items(embeddings, 'embeddings')
        add_items(clip_models, 'clip')
        add_items(clip_vision_models, 'clip-vision')
        add_items(vae_models, 'vae')
        add_items(controlnet_models, 'controlnet')
        add_items(upscale_models, 'upscale')

        try:
            # Use the download-specific progress callback for downloads-only flow
            dl_results, _ = run_parallel_downloads(download_tasks, [], progress_callback=update_download_progress)
            download_status_label.value = "<div class='status-text' style='height: 26px; visibility: visible;'>Downloads completed.</div>"
            # Leave the main install status hidden
        except Exception as e:
            download_status_label.value = f"<div class='status-text' style='height: 26px; visibility: visible;'>Downloads failed: {e}</div>"
        finally:
            # keep reserved space but hide progress bar (visibility hidden) after completion
            download_progress_container.value = """
            <div style="display:flex; justify-content:center; margin-bottom:20px;">
                <div class="progress-container" style="display:block; visibility: hidden;">
                    <div class="progress-bar" style="width:0%;"></div>
                </div>
            </div>
            """
            # keep the status text visible for a short while and then revert to hidden placeholder
            time.sleep(1.0)
            download_status_label.value = "<div class='status-text' style='height: 26px; visibility: hidden;'>Placeholder</div>"
            b.disabled = False

    threading.Thread(target=run_downloads, daemon=True).start()


# NOTE: header-level small downloads button replaced by a large downloads button in downloads_container

# Create advanced toggle button
def toggle_advanced(b):
    global expanded_state
    expanded_state = not expanded_state
    
    if expanded_state:
        b.description = "▲"
        b.style.button_color = '#E74C3C'
        try:
            civitai_input_row.layout.display = 'flex'
        except Exception:
            pass
        for container in category_containers.values():
            container.layout.display = 'flex'
        downloads_container.layout.display = 'flex'
    else:
        b.description = "▼"
        b.style.button_color = '#F5F5DC'
        try:
            civitai_input_row.layout.display = 'none'
        except Exception:
            pass
        for container in category_containers.values():
            container.layout.display = 'none'
        downloads_container.layout.display = 'none'

advanced_toggle_button = widgets.Button(
    description="▼",
    layout=widgets.Layout(width='280px', height='40px', margin='10px 0px'),
    style=widgets.ButtonStyle(button_color='#F5F5DC'),
    _dom_classes=['category-button']
)
advanced_toggle_button.on_click(toggle_advanced)

# Create all category containers
category_containers = {}
for category_id, label in category_labels.items():
    category_containers[category_id] = create_category_widget(
        category_id, label, category_data[category_id]
    )
    category_containers[category_id].layout.display = 'none'  # Initially hidden

# Create main container (header_box and downloads_container are inserted later)

# Create a fixed header area under the title that holds status, progress, link and startup controls
# We want the advanced (triangle) button below the Start Up button.
# Create a top row (vertical) that stacks the OPEN link above the Start Up button
open_link_html = widgets.HTML(value=f"<a href=\"{public_url}\" target=\"_blank\" class=\"open-link-text\">Open Comfy UI</a>")

top_row_children = [open_link_html, startup_btn]
# Positioning: increase gap and center vertically between status and Start Up button
top_row = widgets.VBox(top_row_children, layout=widgets.Layout(gap='25px', align_items='center', margin='8vh 0 0 0', justify_content='center'))

# Create a hidden civitai input row that will expand directly under the advanced button
# Create "Get API Key" link
get_api_key_link = widgets.HTML(value='<a href="https://civitai.com/user/account#api-keys" target="_blank" class="civitai-get-key-link">Get API Key</a>')

# Create a hidden civitai input row with the link and input field
civitai_input_row = widgets.HBox([get_api_key_link, civitai_token_widget], layout=widgets.Layout(align_items='center', justify_content='center', width='100%', margin='6px 0px'))
try:
    civitai_input_row.add_class('item-row')
except Exception:
    if 'item-row' not in civitai_input_row._dom_classes:
        civitai_input_row._dom_classes = civitai_input_row._dom_classes + ['item-row']

# hide by default; shown when advanced is expanded
civitai_input_row.layout.display = 'none'

# Remove the separate open frame from controls — the OPEN link is now inline in the title
# (Previously we nudged the startup button further down; that override is removed to keep vertical centering)

# Controls box stacks Start Up, advanced toggle, and civitai input (open link moved to title)
controls_box = widgets.VBox([top_row, advanced_toggle_button, civitai_input_row], layout=widgets.Layout(gap='6px', align_items='center'))

# Large downloads button shown as the first item when categories are expanded
downloads_large_btn = widgets.Button(
    description="start selected Downloads",
    layout=widgets.Layout(width='280px', height='40px', margin='5px 0px'),
    _dom_classes=['homogenized-button','preserve-color']
)
downloads_large_btn.on_click(start_downloads_only)

# Visible toggle (HTML-style) to enable Flux-dev checkpoint + all custom nodes
flux_custom_toggle_state = {'enabled': False}

flux_toggle_btn = widgets.Button(
    description="",
    layout=widgets.Layout(width='60px', height='30px'),
    disabled=False
)
# apply visual classes
try:
    flux_toggle_btn.add_class('custom-toggle')
except Exception:
    if 'custom-toggle' not in flux_toggle_btn._dom_classes:
        flux_toggle_btn._dom_classes = flux_toggle_btn._dom_classes + ['custom-toggle']

flux_label = widgets.HTML(value=f"""
    <div class='item-info'>
        <div class='item-name'>Standard installation</div>
    </div>
""")

def _on_flux_toggle_click(b):
    # flip state
    flux_custom_toggle_state['enabled'] = not flux_custom_toggle_state['enabled']
    enabled = flux_custom_toggle_state['enabled']
    # update visual state
    try:
        if enabled:
            flux_toggle_btn.add_class('active')
        else:
            flux_toggle_btn.remove_class('active')
    except Exception:
        if enabled and 'active' not in flux_toggle_btn._dom_classes:
            flux_toggle_btn._dom_classes = flux_toggle_btn._dom_classes + ['active']
        if not enabled and 'active' in flux_toggle_btn._dom_classes:
            flux_toggle_btn._dom_classes = [c for c in flux_toggle_btn._dom_classes if c != 'active']

    # call helper to toggle the underlying sets
    set_flux_and_custom(enabled)

flux_toggle_btn.on_click(_on_flux_toggle_click)

flux_custom_row = widgets.HBox([flux_toggle_btn, flux_label], layout=widgets.Layout(align_items='center', width='800px', margin='5px 0px'))
try:
    flux_custom_row.add_class('item-row')
except Exception:
    if 'item-row' not in flux_custom_row._dom_classes:
        flux_custom_row._dom_classes = flux_custom_row._dom_classes + ['item-row']

# --- All downloads toggle (toggles all categories on/off) ---
all_downloads_state = {'enabled': False}

all_toggle_btn = widgets.Button(
    description="",
    layout=widgets.Layout(width='60px', height='30px'),
    disabled=False
)
try:
    all_toggle_btn.add_class('custom-toggle')
except Exception:
    if 'custom-toggle' not in all_toggle_btn._dom_classes:
        all_toggle_btn._dom_classes = all_toggle_btn._dom_classes + ['custom-toggle']

all_label = widgets.HTML(value=f"""
    <div class='item-info'>
        <div class='item-name'>All downloads</div>
    </div>
""")

def set_all_downloads(enabled: bool):
    """Set all optional items across categories to enabled/disabled and update visuals."""
    for cat, items in category_data.items():
        # skip required-only categories? we still set states but respect 'required' fields
        for idx in range(len(items)):
            # respect required flag: if required, always True
            if items[idx].get('required', False):
                toggle_states.setdefault(cat, {})[idx] = True
                continue
            toggle_states.setdefault(cat, {})[idx] = bool(enabled)
            # update visual button if present
            btn = toggle_widgets.get(cat, {}).get(idx)
            if btn is not None:
                try:
                    if enabled:
                        btn.add_class('active')
                    else:
                        btn.remove_class('active')
                except Exception:
                    if enabled and 'active' not in btn._dom_classes:
                        btn._dom_classes = btn._dom_classes + ['active']
                    if not enabled and 'active' in btn._dom_classes:
                        btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

def _on_all_toggle_click(b):
    all_downloads_state['enabled'] = not all_downloads_state['enabled']
    enabled = all_downloads_state['enabled']
    try:
        if enabled:
            all_toggle_btn.add_class('active')
        else:
            all_toggle_btn.remove_class('active')
    except Exception:
        if enabled and 'active' not in all_toggle_btn._dom_classes:
            all_toggle_btn._dom_classes = all_toggle_btn._dom_classes + ['active']
        if not enabled and 'active' in all_toggle_btn._dom_classes:
            all_toggle_btn._dom_classes = [c for c in all_toggle_btn._dom_classes if c != 'active']

    # set all categories
    set_all_downloads(enabled)

all_toggle_btn.on_click(_on_all_toggle_click)

all_downloads_row = widgets.HBox([all_toggle_btn, all_label], layout=widgets.Layout(align_items='center', width='800px', margin='5px 0px'))
try:
    all_downloads_row.add_class('item-row')
except Exception:
    if 'item-row' not in all_downloads_row._dom_classes:
        all_downloads_row._dom_classes = all_downloads_row._dom_classes + ['item-row']

# --- Disney Animation Preset Toggle ---
disney_preset_state = {'enabled': False}

disney_toggle_btn = widgets.Button(
    description="",
    layout=widgets.Layout(width='60px', height='30px'),
    disabled=False
)
try:
    disney_toggle_btn.add_class('custom-toggle')
except Exception:
    if 'custom-toggle' not in disney_toggle_btn._dom_classes:
        disney_toggle_btn._dom_classes = disney_toggle_btn._dom_classes + ['custom-toggle']

disney_label = widgets.HTML(value="""
    <div class='item-info'>
        <div class='item-name'>Disney Animation</div>
    </div>
""")

def set_disney_preset(enabled: bool):
    """Set Disney Animation preset: all custom nodes + Pony Diffusion V6 XL + Disney LoRAs"""
    # Enable all custom nodes
    for idx in range(len(custom_nodes)):
        toggle_states.setdefault('custom-nodes', {})[idx] = bool(enabled)
        btn = toggle_widgets.get('custom-nodes', {}).get(idx)
        if btn is not None:
            try:
                if enabled:
                    btn.add_class('active')
                else:
                    btn.remove_class('active')
            except Exception:
                if enabled and 'active' not in btn._dom_classes:
                    btn._dom_classes = btn._dom_classes + ['active']
                if not enabled and 'active' in btn._dom_classes:
                    btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

    # Disney Animation specific items
    disney_items = [
        # Checkpoints
        ('checkpoints', 'Pony_Diffusion_V6_XL.safetensors'),
        # LoRAs
        ('loras', 'Disney_Princess_XL_v2.0.safetensors'),
        ('loras', 'ExpressiveH_Hentai_Style'),
        ('loras', 'Vixons_Pony_Gothic_Neon_v1.0.safetensors'),
        ('loras', 'Incase_Style_PonyXL_v3.0.safetensors'),
        # Embeddings
        ('embeddings', 'EasyNegative.pt'),
        # Upscale
        ('upscale', '4x_foolhardy_Remacri.pth'),
    ]
    
    for category, item_name in disney_items:
        items = category_data.get(category, [])
        for idx, item in enumerate(items):
            if item_name in item.get('name', '') or item_name in item.get('filename', ''):
                toggle_states.setdefault(category, {})[idx] = bool(enabled)
                btn = toggle_widgets.get(category, {}).get(idx)
                if btn is not None:
                    try:
                        if enabled:
                            btn.add_class('active')
                        else:
                            btn.remove_class('active')
                    except Exception:
                        if enabled and 'active' not in btn._dom_classes:
                            btn._dom_classes = btn._dom_classes + ['active']
                        if not enabled and 'active' in btn._dom_classes:
                            btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

def _on_disney_toggle_click(b):
    disney_preset_state['enabled'] = not disney_preset_state['enabled']
    enabled = disney_preset_state['enabled']
    try:
        if enabled:
            disney_toggle_btn.add_class('active')
        else:
            disney_toggle_btn.remove_class('active')
    except Exception:
        if enabled and 'active' not in disney_toggle_btn._dom_classes:
            disney_toggle_btn._dom_classes = disney_toggle_btn._dom_classes + ['active']
        if not enabled and 'active' in disney_toggle_btn._dom_classes:
            disney_toggle_btn._dom_classes = [c for c in disney_toggle_btn._dom_classes if c != 'active']

    # preserve existing preset selection behavior
    set_disney_preset(enabled)

disney_toggle_btn.on_click(_on_disney_toggle_click)

disney_row = widgets.HBox([disney_toggle_btn, disney_label], layout=widgets.Layout(align_items='Center', width='800px', margin='5px 0px'))
try:
    disney_row.add_class('item-row')
except Exception:
    if 'item-row' not in disney_row._dom_classes:
        disney_row._dom_classes = disney_row._dom_classes + ['item-row']

# Create Disney permanent preview (always visible)
disney_img_path = os.path.join('workspace', 'Uploads', 'Disney Illustration Animation.png')
disney_data = load_image_as_base64(disney_img_path)
disney_image_html = widgets.HTML(value=_build_preset_image_html(disney_data, 'Disney Animation Preview'))
disney_container = widgets.VBox([disney_row, disney_image_html], layout=widgets.Layout(width='800px', align_items='center', margin='5px 0px'))
try:
    disney_container.add_class('preset-container')
except Exception:
    if 'preset-container' not in disney_container._dom_classes:
        disney_container._dom_classes = disney_container._dom_classes + ['preset-container']


# --- Impasto Preset Toggle ---
impasto_preset_state = {'enabled': False}

impasto_toggle_btn = widgets.Button(
    description="",
    layout=widgets.Layout(width='60px', height='30px'),
    disabled=False
)
try:
    impasto_toggle_btn.add_class('custom-toggle')
except Exception:
    if 'custom-toggle' not in impasto_toggle_btn._dom_classes:
        impasto_toggle_btn._dom_classes = impasto_toggle_btn._dom_classes + ['custom-toggle']

impasto_label = widgets.HTML(value="""
    <div class='item-info'>
        <div class='item-name'>Impasto</div>
    </div>
""")

def set_impasto_preset(enabled: bool):
    """Set Impasto preset: all custom nodes + A-mix Illustrious + Ri-mix LoRA"""
    # Enable all custom nodes
    for idx in range(len(custom_nodes)):
        toggle_states.setdefault('custom-nodes', {})[idx] = bool(enabled)
        btn = toggle_widgets.get('custom-nodes', {}).get(idx)
        if btn is not None:
            try:
                if enabled:
                    btn.add_class('active')
                else:
                    btn.remove_class('active')
            except Exception:
                if enabled and 'active' not in btn._dom_classes:
                    btn._dom_classes = btn._dom_classes + ['active']
                if not enabled and 'active' in btn._dom_classes:
                    btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

    # Impasto specific items
    impasto_items = [
        # Checkpoints
        ('checkpoints', 'A-mix_Illustrious'),
        # LoRAs
        ('loras', 'Ri-mix_Style_LORA'),
    ]
    
    for category, item_name in impasto_items:
        items = category_data.get(category, [])
        for idx, item in enumerate(items):
            if item_name in item.get('name', '') or item_name in item.get('filename', ''):
                toggle_states.setdefault(category, {})[idx] = bool(enabled)
                btn = toggle_widgets.get(category, {}).get(idx)
                if btn is not None:
                    try:
                        if enabled:
                            btn.add_class('active')
                        else:
                            btn.remove_class('active')
                    except Exception:
                        if enabled and 'active' not in btn._dom_classes:
                            btn._dom_classes = btn._dom_classes + ['active']
                        if not enabled and 'active' in btn._dom_classes:
                            btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

def _on_impasto_toggle_click(b):
    impasto_preset_state['enabled'] = not impasto_preset_state['enabled']
    enabled = impasto_preset_state['enabled']
    try:
        if enabled:
            impasto_toggle_btn.add_class('active')
        else:
            impasto_toggle_btn.remove_class('active')
    except Exception:
        if enabled and 'active' not in impasto_toggle_btn._dom_classes:
            impasto_toggle_btn._dom_classes = impasto_toggle_btn._dom_classes + ['active']
        if not enabled and 'active' in impasto_toggle_btn._dom_classes:
            impasto_toggle_btn._dom_classes = [c for c in impasto_toggle_btn._dom_classes if c != 'active']

    # preserve existing preset selection behavior
    set_impasto_preset(enabled)

impasto_toggle_btn.on_click(_on_impasto_toggle_click)

impasto_row = widgets.HBox([impasto_toggle_btn, impasto_label], layout=widgets.Layout(align_items='center', width='800px', margin='5px 0px'))
try:
    impasto_row.add_class('item-row')
except Exception:
    if 'item-row' not in impasto_row._dom_classes:
        impasto_row._dom_classes = impasto_row._dom_classes + ['item-row']

# Create Impasto permanent preview (always visible)
impasto_img_path = os.path.join('workspace', 'Uploads', 'Impasto Wokflow.png')
impasto_data = load_image_as_base64(impasto_img_path)
impasto_image_html = widgets.HTML(value=_build_preset_image_html(impasto_data, 'Impasto Preview'))
impasto_container = widgets.VBox([impasto_row, impasto_image_html], layout=widgets.Layout(width='800px', align_items='center', margin='5px 0px'))
try:
    impasto_container.add_class('preset-container')
except Exception:
    if 'preset-container' not in impasto_container._dom_classes:
        impasto_container._dom_classes = impasto_container._dom_classes + ['preset-container']

# --- Cinematic Realistic Photography Preset Toggle ---
cinematic_preset_state = {'enabled': False}

cinematic_toggle_btn = widgets.Button(
    description="",
    layout=widgets.Layout(width='60px', height='30px'),
    disabled=False
)
try:
    cinematic_toggle_btn.add_class('custom-toggle')
except Exception:
    if 'custom-toggle' not in cinematic_toggle_btn._dom_classes:
        cinematic_toggle_btn._dom_classes = cinematic_toggle_btn._dom_classes + ['custom-toggle']

cinematic_label = widgets.HTML(value="""
    <div class='item-info'>
        <div class='item-name'>Cinematic Realistic Photography</div>
    </div>
""")

def set_cinematic_preset(enabled: bool):
    """Set Cinematic Realistic Photography preset: all custom nodes + CyberRealistic Pony + specific LoRAs"""
    # Enable all custom nodes
    for idx in range(len(custom_nodes)):
        toggle_states.setdefault('custom-nodes', {})[idx] = bool(enabled)
        btn = toggle_widgets.get('custom-nodes', {}).get(idx)
        if btn is not None:
            try:
                if enabled:
                    btn.add_class('active')
                else:
                    btn.remove_class('active')
            except Exception:
                if enabled and 'active' not in btn._dom_classes:
                    btn._dom_classes = btn._dom_classes + ['active']
                if not enabled and 'active' in btn._dom_classes:
                    btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

    # Cinematic Realistic Photography specific items
    cinematic_items = [
        # Checkpoints
        ('checkpoints', 'CyberRealistic_Pony'),
        # LoRAs - Note: These might need to be added to your loras list if not present
        ('loras', 'Crazy_Girlfriend_Mix'),
        ('loras', 'Insta_Baddie'),
    ]
    
    for category, item_name in cinematic_items:
        items = category_data.get(category, [])
        for idx, item in enumerate(items):
            if item_name in item.get('name', '') or item_name in item.get('filename', ''):
                toggle_states.setdefault(category, {})[idx] = bool(enabled)
                btn = toggle_widgets.get(category, {}).get(idx)
                if btn is not None:
                    try:
                        if enabled:
                            btn.add_class('active')
                        else:
                            btn.remove_class('active')
                    except Exception:
                        if enabled and 'active' not in btn._dom_classes:
                            btn._dom_classes = btn._dom_classes + ['active']
                        if not enabled and 'active' in btn._dom_classes:
                            btn._dom_classes = [c for c in btn._dom_classes if c != 'active']

# Add missing LoRAs that might not be in your current list
missing_loras = [
    {
        "name": "Crazy_Girlfriend_Mix_XL_PONY.safetensors",
        "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",  # You'll need to find the correct model ID
        "info": "Crazy Girlfriend Mix [XL/PONY] LoRA",
        "required": False,
        "filename": "Crazy_Girlfriend_Mix_XL_PONY.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Insta_Baddie_PONY.safetensors",
        "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",  # You'll need to find the correct model ID
        "info": "Insta Baddie[PONY] LoRA",
        "required": False,
        "filename": "Insta_Baddie_PONY.safetensors",
        "dest_dir": "models/loras"
    }
]

# Uncomment the following line to add the missing LoRAs to your list:
# loras.extend(missing_loras)

print("Added Disney Animation, Impasto, and Cinematic Realistic Photography preset toggles!")
print("Note: Some LoRAs may need correct Civitai model IDs to be added to download properly.")

def _on_cinematic_toggle_click(b):
    cinematic_preset_state['enabled'] = not cinematic_preset_state['enabled']
    enabled = cinematic_preset_state['enabled']
    try:
        if enabled:
            cinematic_toggle_btn.add_class('active')
        else:
            cinematic_toggle_btn.remove_class('active')
    except Exception:
        if enabled and 'active' not in cinematic_toggle_btn._dom_classes:
            cinematic_toggle_btn._dom_classes = cinematic_toggle_btn._dom_classes + ['active']
        if not enabled and 'active' in cinematic_toggle_btn._dom_classes:
            cinematic_toggle_btn._dom_classes = [c for c in cinematic_toggle_btn._dom_classes if c != 'active']

    # preserve existing preset selection behavior
    set_cinematic_preset(enabled)

cinematic_toggle_btn.on_click(_on_cinematic_toggle_click)

cinematic_row = widgets.HBox([cinematic_toggle_btn, cinematic_label], layout=widgets.Layout(align_items='center', width='800px', margin='5px 0px'))
try:
    cinematic_row.add_class('item-row')
except Exception:
    if 'item-row' not in cinematic_row._dom_classes:
        cinematic_row._dom_classes = cinematic_row._dom_classes + ['item-row']

# Create Cinematic permanent preview (always visible)
cinematic_img_path = os.path.join('workspace', 'Uploads', 'Cinematic Photography.png')
cinematic_data = load_image_as_base64(cinematic_img_path)
cinematic_image_html = widgets.HTML(value=_build_preset_image_html(cinematic_data, 'Cinematic Photography Preview'))
cinematic_container = widgets.VBox([cinematic_row, cinematic_image_html], layout=widgets.Layout(width='800px', align_items='center', margin='5px 0px'))
try:
    cinematic_container.add_class('preset-container')
except Exception:
    if 'preset-container' not in cinematic_container._dom_classes:
        cinematic_container._dom_classes = cinematic_container._dom_classes + ['preset-container']

# Update the downloads_container to include the new preset toggles
downloads_container = widgets.VBox([
    downloads_large_btn,
    flux_custom_row,
    # Disney container (toggle + image)
    disney_container,
    # Impasto container (toggle + image)
    impasto_container,
    # Cinematic container (toggle + image)
    cinematic_container,
    all_downloads_row
], layout=widgets.Layout(display='none', align_items='center', margin='5px 0px'))

header_box = widgets.VBox([
    status_label,
    progress_container,
    # Download-only progress/status (reserve space below the main progress)
    download_status_label,
    download_progress_container,
    controls_box
], layout=widgets.Layout(align_items='center', width='100%', margin='0px 0px'))

# Main container now places header fixed under title and categories below
main_container = widgets.VBox(
    [header_box, downloads_container] + list(category_containers.values()),
    layout=widgets.Layout(
        display='flex',
        flex_flow='column',
        align_items='center',
        width='100%',
        gap='10px'
    )
)

try:
    main_container.add_class('comfy-root')
except Exception:
    # fallback for older ipywidgets versions
    if 'comfy-root' not in main_container._dom_classes:
        main_container._dom_classes = main_container._dom_classes + ['comfy-root']

display(main_container)

# -----------------------------
# Debug Functions
# -----------------------------
def get_selected_items():
    """Get all selected items across categories"""
    selected = {}
    total_count = 0
    
    for category_id, states in toggle_states.items():
        selected[category_id] = {
            'items': [],
            'count': 0
        }
        
        for item_id, is_selected in states.items():
            if is_selected:
                item_data = category_data[category_id][item_id].copy()
                item_data['item_id'] = item_id
                selected[category_id]['items'].append(item_data)
                selected[category_id]['count'] += 1
                total_count += 1
    
    selected['_summary'] = {
        'total_selected': total_count,
        'categories_with_selections': len([cat for cat in selected.values() 
                                         if isinstance(cat, dict) and cat.get('count', 0) > 0])
    }
    
    return selected

def print_selection_summary():
    """Print a formatted summary of selected items"""
    selected = get_selected_items()
    print("=" * 60)
    print("SELECTION SUMMARY")
    print("=" * 60)
    print(f"Total items selected: {selected['_summary']['total_selected']}")
    print(f"Categories with selections: {selected['_summary']['categories_with_selections']}")
    print()
    
    for category_id, data in selected.items():
        if category_id != '_summary' and isinstance(data, dict) and data['count'] > 0:
            print(f"{category_labels[category_id].upper()}: {data['count']} selected")
            for item in data['items']:
                status = "REQUIRED" if item.get('required', False) else "OPTIONAL"
                print(f"  • {item['name']} ({status})")
            print()

def show_selections():
    """Display current selections in a user-friendly format"""
    print_selection_summary()

def debug_toggle_states():
    """Debug function to show current toggle states"""
    print("Current toggle states:")
    for category, states in toggle_states.items():
        print(f"{category}: {states}")

# Functions ready for use
# Use show_selections() to see current selections
# Use debug_toggle_states() to see raw toggle states
