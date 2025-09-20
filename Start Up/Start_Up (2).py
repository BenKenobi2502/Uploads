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
try:
    import psutil
except ImportError:
    psutil = None
    # Note: psutil optional - status monitoring will be disabled when absent
    # Use logging to record environment-level issues without spamming stdout
    # logging will be configured below; log this situation later if needed
    pass

# Configure module logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
if psutil is None:
    logger.info("psutil not available; ComfyUI status monitoring will be disabled.")

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
    logging.getLogger(__name__).info(f"Installing missing packages: {missing}")
    try:
        # Use sys.executable to call the same Python interpreter
        cmd = [sys.executable, "-m", "pip", "install"] + missing
        import subprocess
        subprocess.check_call(cmd)
    except Exception as e:
        logging.getLogger(__name__).exception("Automatic installation of requirements failed: %s", e)
        logging.getLogger(__name__).warning("Please manually install the required packages and re-run this script: pip install ipywidgets requests")

_bootstrap_requirements()


# -----------------------------
# API Key File Management
# -----------------------------
def load_api_key():
    """Read API key from workspace/Uploads/Civit Ai Key/CivitAi Api Key.txt
    Returns the last line of the file (most recent key) or empty string if not found"""
    try:
        api_key_path = os.path.join('workspace', 'Uploads', 'Civit Ai Key', 'CivitAi Api Key.txt')
        if os.path.exists(api_key_path):
            with open(api_key_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    # Return the last non-empty line (most recent key)
                    for line in reversed(lines):
                        line = line.strip()
                        if line:
                            return line
        return ""
    except Exception as e:
        logging.getLogger(__name__).exception("Error loading API key: %s", e)
        return ""

def save_api_key(key):
    """Save API key to workspace/Uploads/Civit Ai Key/CivitAi Api Key.txt
    Appends the key as a new line to maintain history"""
    try:
        if not key or not key.strip():
            return
        
        api_key_dir = os.path.join('workspace', 'Uploads', 'Civit Ai Key')
        api_key_path = os.path.join(api_key_dir, 'CivitAi Api Key.txt')
        
        # Create directory if it doesn't exist
        os.makedirs(api_key_dir, exist_ok=True)
        
        # Append new key with timestamp comment
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(api_key_path, 'a', encoding='utf-8') as f:
            f.write(f"# Added {timestamp}\n{key.strip()}\n")
            
    except Exception as e:
        logging.getLogger(__name__).exception("Error saving API key: %s", e)

def save_key_on_change(change):
    """Observer function to automatically save API key when changed"""
    if change['type'] == 'change' and change['name'] == 'value':
        new_value = change['new']
        if new_value and new_value.strip():
            save_api_key(new_value)


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
# Image helpers for display testing
# -----------------------------
def image_to_base64(path):
    """Return base64-encoded PNG data for an image file, or empty string on failure."""
    try:
        import base64
        with open(path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode('ascii')
    except Exception:
        return ''


def generate_triple_image_html(base_img_path, preset_name):
    """Generate HTML for 3 identical images in a row using the same source image."""
    base64_data = image_to_base64(base_img_path)
    if not base64_data:
        # Fallback if image can't be loaded
        return f'<div style="text-align:center; padding:10px; color:#1A237E;">Images for {preset_name} preset not available</div>'

    return f'''
    <div style="text-align:center; padding:10px;">
        <div style="display:flex; justify-content:center; gap:15px; flex-wrap:wrap;">
            <img src="data:image/png;base64,{base64_data}" 
                 style="max-width:250px; width:100%; height:auto; border-radius:8px; box-shadow:0 4px 8px rgba(0,0,0,0.1); cursor:pointer;" 
                 onclick="alert('{preset_name} preset image 1 clicked');">
            <img src="data:image/png;base64,{base64_data}" 
                 style="max-width:250px; width:100%; height:auto; border-radius:8px; box-shadow:0 4px 8px rgba(0,0,0,0.1); cursor:pointer;" 
                 onclick="alert('{preset_name} preset image 2 clicked');">
            <img src="data:image/png;base64,{base64_data}" 
                 style="max-width:250px; width:100%; height:auto; border-radius:8px; box-shadow:0 4px 8px rgba(0,0,0,0.1); cursor:pointer;" 
                 onclick="alert('{preset_name} preset image 3 clicked');">
        </div>
    </div>
    '''

def copy_image_to_cwd(src_path, dst_name='test_image_copy.png'):
    """Copy an image into the current working directory and return its relative path."""
    try:
        import shutil
        dst = os.path.join(os.getcwd(), dst_name)
        shutil.copyfile(src_path, dst)
        return dst
    except Exception:
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
        margin: 0; /* ensure the comfy-root fills to the top without white gaps */
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
        /* Use the same font/color characteristics as .status-text */
        font-family: inherit; /* inherit the root 'Segoe UI' family */
        font-size: 100px !important; /* enlarged title per request */
        font-weight: bold;
    color: #1A237E; /* match Open Comfy UI text */
        margin: 0px 0 15px 0;
        line-height: 1.05; /* tighter line-height for large display */
        padding-bottom: 6px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.08);
        max-width: 100%;
        overflow: visible;
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

    /* CivitAI input container (new compact blue style) */
    .comfy-root .civitai-input-container {
        background: linear-gradient(180deg, #1A237E 0%, #0747D1 100%);
        border: 2px solid #0639B2;
        color: white;
        border-radius: 12px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        max-width: 720px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        font-size: 14px;
    }

    /* civitai-label styling removed: label text was removed from the input container */

    .comfy-root .civitai-input-container input,
    .comfy-root .civitai-input-container .widget-text {
        background: white !important;
        color: #1A237E !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        font-size: 14px !important;
        height: 32px !important;
        box-sizing: border-box !important;
        flex: 1 1 auto;
    }

    .comfy-root .civitai-input-container input::placeholder {
        color: rgba(26,35,126,0.45) !important;
    }

    /* Removed legacy .civitai-get-key-link rules; replaced by a status-style link added below. */

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

    /* Legacy 'civitai-container' has been replaced by .civitai-input-container above.
       This keeps styling focused and avoids duplicate/competing rules. */

    /* ComfyUI status monitoring - running state */
    .comfy-root .open-link-text.running {
        text-decoration: underline !important;
    }

    /* New CivitAI status-style link (white, bold, underlined) */
    .comfy-root .status-civitai-link {
        text-align: center;
        font-size: 22px;
        color: white;
        font-weight: bold;
        margin: 2px 0px 2px 0px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .comfy-root .status-civitai-link a {
        color: white !important;
        text-decoration: underline !important;
        font-weight: bold !important;
        font-size: 22px !important;
        font-family: inherit !important;
    }

    .comfy-root .status-civitai-link a:hover {
        color: #F0F0F0 !important;
        text-decoration: underline !important;
    }

    /* Download progress bar styling (identical to main progress) */
    .comfy-root .download-progress-container {
        background-color: #F5F5DC;
        width: 300px;
        height: 24px;
        border-radius: 10px;
        border: 2px solid #C0392B;
        margin-top: 16px;
        margin-bottom: 20px;
        display: block;
        overflow: hidden;
    }

    .comfy-root .download-progress-bar {
        background: #E74C3C;
        height: 100%;
        width: 0%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }

    /* Additional downloads progress (separate from the main installation and the regular downloads) */
    .comfy-root .additional-progress-container {
        background-color: #F5F5DC;
        width: 300px;
        height: 24px;
        border-radius: 10px;
        border: 2px solid #C0392B;
        margin-top: 16px;
        margin-bottom: 20px;
        display: block;
        overflow: hidden;
    }

    .comfy-root .additional-progress-bar {
        background: #E74C3C; /* same red color scheme */
        height: 100%;
        width: 0%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }

    /* Preset preview images - constrained size and clickable appearance */
    .comfy-root .preset-image-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px;
    }

    .comfy-root .preset-image-wrapper img {
        max-height: 160px;
        width: auto;
        border-radius: 8px;
        border: 2px solid rgba(0,0,0,0.06);
        box-shadow: 0 6px 14px rgba(0,0,0,0.08);
        cursor: pointer;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }

    .comfy-root .preset-image-wrapper img:hover {
        transform: scale(1.03);
        box-shadow: 0 10px 22px rgba(0,0,0,0.12);
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

# Note: The CivitAI token input widget is created later in the controls area
# as part of the advanced/expanded controls; defined there to keep title
# layout minimal and avoid duplicate inputs.

# Title row: keep only the title (OPEN link will be positioned above the Start Up button)
title_row = widgets.VBox([
    widgets.HBox([title_html], layout=Layout(width='100%', justify_content='center', align_items='center'))
], layout=Layout(width='100%', align_items='center'))

import os


# NOTE: Dynamic image monitoring and base64 helpers removed in favor of simple HTML/PIL rendering per user request.

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
            logging.getLogger(__name__).warning("Civitai download failed for %s: %s", url, e)
            # fall through to wget fallback

    # Fallback: use wget (system dependent)
    try:
        cmd = f"wget -O {dest_path} {url}"
        subprocess.run(cmd, shell=True, cwd=cwd, check=True)
        return True
    except Exception as e:
        logging.getLogger(__name__).warning("Download failed for %s: %s", url, e)
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
                    logging.getLogger(__name__).info("Download: %s", message)
                except Exception as e:
                    download_results.append({
                        'task': task,
                        'success': False,
                        'message': f"Exception: {str(e)}"
                    })
                    logging.getLogger(__name__).warning("Download failed: %s - %s", task.get('name', 'Unknown'), str(e))
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
                    logging.getLogger(__name__).info("Clone: %s", message)
                except Exception as e:
                    clone_results.append({
                        'task': task,
                        'success': False,
                        'message': f"Exception: {str(e)}"
                    })
                    logging.getLogger(__name__).warning("Clone failed: %s - %s", task.get('name', 'Unknown'), str(e))
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

# New CivitAI status-style link (white, matches 'is up and running' styling)
civitai_status_link = widgets.HTML(
    value="<div class='status-civitai-link'><a href='https://civitai.com/user/account#api-keys' target='_blank'>Get CivitAI API Key</a></div>",
    layout=Layout(height='26px', margin='2px 0px')
)

# Download-only status and progress (reserve space like the main progress bar)
download_status_label = widgets.HTML(value="<div class='status-text' style='height: 26px; visibility: hidden;'>Downloading...</div>")

download_progress_container = widgets.HTML(value="""
<div style="display:flex; justify-content:center; margin-bottom:20px;">
    <div class="progress-container" style="display:block; visibility: hidden;">
        <div class="progress-bar" style="width:0%;"></div>
    </div>
</div>
""")

# Additional-downloads status and progress (separate bar for 'additional downloads')
additional_downloads_status_label = widgets.HTML(value="<div class='status-text' style='height: 26px; visibility: hidden;'>Additional downloads...</div>")

additional_downloads_progress_container = widgets.HTML(value="""
<div style="display:flex; justify-content:center; margin-bottom:20px;">
    <div class="additional-progress-container" style="display:block; visibility: hidden;">
        <div class="additional-progress-bar" style="width:0%;"></div>
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
        "website_url": None,  # TODO: find correct Civitai model page and set URL
        # TODO: Find correct model ID on Civitai and replace the URL below
        # "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "url": None,
        "info": "Pony Amateur ✨ - Rough (V1)",
        "required": False,
        "filename": "Pony_Amateur_LoRA_v1.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Crazy_Girlfriend_Mix_XL_PONY.safetensors",
        "website_url": None,  # TODO: find correct Civitai model page and set URL
        # TODO: Find correct model ID on Civitai and replace the URL below
        # "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "url": None,
        "info": "Crazy Girlfriend Mix [XL/PONY]",
        "required": False,
        "filename": "Crazy_Girlfriend_Mix_XL_PONY.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Insta_Baddie_PONY.safetensors",
        "website_url": None,  # TODO: find correct Civitai model page and set URL
        # TODO: Find correct model ID on Civitai and replace the URL below
        # "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "url": None,
        "info": "Insta Baddie[PONY]",
        "required": False,
        "filename": "Insta_Baddie_PONY.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Real_Beauty_LoRA_v1.safetensors",
        "website_url": None,  # TODO: find correct Civitai model page and set URL
        # TODO: Find correct model ID on Civitai and replace the URL below
        # "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "url": None,
        "info": "Real Beauty LoRA v1",
        "required": False,
        "filename": "Real_Beauty_LoRA_v1.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Dramatic_Lighting_Slider_v1.0.safetensors",
        "website_url": None,  # TODO: find correct Civitai model page and set URL
        # TODO: Find correct model ID on Civitai and replace the URL below
        # "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",
        "url": None,
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
    "generation-downloads": [],
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

# New media categories
images_downloads = [
    {"name": "Image Processing Tools", "info": "Tools for image manipulation and processing", "required": False},
    {"name": "Image Format Converters", "info": "Convert between different image formats", "required": False},
    {"name": "Image Enhancement Models", "info": "AI models for image enhancement", "required": False}
]

videos_downloads = [
    {"name": "Video Processing Tools", "info": "Tools for video editing and processing", "required": False},
    {"name": "Video Codecs", "info": "Video encoding and decoding libraries", "required": False},
    {"name": "Animation Tools", "info": "Tools for creating animations", "required": False}
]

audio_downloads = [
    {"name": "Audio Processing Libraries", "info": "Libraries for audio manipulation", "required": False},
    {"name": "Audio Format Converters", "info": "Convert between audio formats", "required": False},
    {"name": "Audio Enhancement Tools", "info": "Tools for audio quality improvement", "required": False}
]

text_downloads = [
    {"name": "Text Processing Tools", "info": "Natural language processing tools", "required": False},
    {"name": "Font Collections", "info": "Typography and font resources", "required": False},
    {"name": "Translation Tools", "info": "Language translation utilities", "required": False}
]

code_downloads = [
    {"name": "Development Tools", "info": "Code development and debugging tools", "required": False},
    {"name": "Code Templates", "info": "Pre-built code templates and snippets", "required": False},
    {"name": "Documentation Generators", "info": "Tools for generating code documentation", "required": False}
]

category_labels = {
    "generation-downloads": "Download ComfyUI Generations",
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

# Add labels for new media categories
category_labels.update({
    "images": "Images",
    "videos": "Videos",
    "audio": "Audio",
    "text": "Text",
    "code": "Code"
})

# State management
expanded_state = False
category_expanded = {key: False for key in category_data.keys()}
toggle_states = {}

# Button state tracking for toggles (startup and downloads)
button_states = {
    'startup': {'active': False, 'process': None},
    'downloads': {'active': False, 'process': None}
}

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


def update_download_progress(percent, message: str = 'Running downloads...'):
    """Update the download-only progress bar and its status text while preserving layout space.
    Shows both status text and progress bar for enhanced visual feedback."""
    # Update download status text
    download_status_label.value = f"<div class='status-text' style='height: 26px; visibility: visible;'>{message}</div>"
    
    # Update download progress bar with enhanced styling
    download_progress_container.value = f"""
    <div style="display:flex; justify-content:center; margin-bottom:20px;">
        <div class="download-progress-container" style="display:block; visibility: visible;">
            <div class="download-progress-bar" style="width:{percent}%;"></div>
        </div>
    </div>
    """


def update_additional_downloads_progress(percent, message: str = 'Running additional downloads...'):
    """Update the additional-downloads-only progress bar and its status text while preserving layout space."""
    additional_downloads_status_label.value = f"<div class='status-text' style='height: 26px; visibility: visible;'>{message}</div>"
    additional_downloads_progress_container.value = f"""
    <div style="display:flex; justify-content:center; margin-bottom:20px;">
        <div class="additional-progress-container" style="display:block; visibility: visible;">
            <div class="additional-progress-bar" style="width:{percent}%;"></div>
        </div>
    </div>
    """

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
        if not hasattr(btn, '_dom_classes'):
            try:
                btn._dom_classes = []
            except Exception:
                pass
        if 'custom-toggle' not in getattr(btn, '_dom_classes', []):
            btn._dom_classes = getattr(btn, '_dom_classes', []) + ['custom-toggle']
        if toggle_states[category_id][item_id] and 'active' not in getattr(btn, '_dom_classes', []):
            btn._dom_classes = getattr(btn, '_dom_classes', []) + ['active']
        if is_required and 'disabled' not in getattr(btn, '_dom_classes', []):
            btn._dom_classes = getattr(btn, '_dom_classes', []) + ['disabled']

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
        if not hasattr(row, '_dom_classes'):
            try:
                row._dom_classes = []
            except Exception:
                pass
        if 'item-row' not in getattr(row, '_dom_classes', []):
            row._dom_classes = getattr(row, '_dom_classes', []) + ['item-row']

    return row

# Helper to enable/disable comprehensive standard installation
def set_standard_installation(enabled: bool):
    """Set comprehensive standard installation: all custom nodes + essential models.
    Includes all checkpoints, upscale models, controlnet models, VAE models, 
    CLIP models, CLIP Vision models as specified in requirements.
    This updates both the `toggle_states` dict and the visual button classes in `toggle_widgets`.
    """
    
    def update_toggle_visual(category, idx, enabled):
        """Helper to update visual state of a toggle button"""
        btn = toggle_widgets.get(category, {}).get(idx)
        if btn is not None:
            try:
                if enabled:
                    btn.add_class('active')
                else:
                    btn.remove_class('active')
            except Exception:
                if not hasattr(btn, '_dom_classes'):
                    try:
                        btn._dom_classes = []
                    except Exception:
                        pass
                if enabled and 'active' not in getattr(btn, '_dom_classes', []):
                    btn._dom_classes = getattr(btn, '_dom_classes', []) + ['active']
                if not enabled and 'active' in getattr(btn, '_dom_classes', []):
                    btn._dom_classes = [c for c in getattr(btn, '_dom_classes', []) if c != 'active']
    
    # 1. Toggle ALL custom nodes
    for idx in range(len(custom_nodes)):
        toggle_states.setdefault('custom-nodes', {})[idx] = bool(enabled)
        update_toggle_visual('custom-nodes', idx, enabled)
    
    # 2. Toggle specific essential checkpoints
    essential_checkpoints = ['flux1-dev-fp8', 'Flux_Fill', 'SDXL_WildCard', 'SD1.5_Epic_Realism']
    for idx, cp in enumerate(checkpoints):
        name = (cp.get('name') or '').lower()
        fname = (cp.get('filename') or '').lower()
        
        # Check if this checkpoint is in our essential list
        is_essential = any(essential.lower() in name or essential.lower() in fname 
                          for essential in essential_checkpoints)
        
        if is_essential:
            toggle_states.setdefault('checkpoints', {})[idx] = bool(enabled)
            update_toggle_visual('checkpoints', idx, enabled)
    
    # 3. Toggle ALL upscale models
    for idx in range(len(upscale_models)):
        toggle_states.setdefault('upscale', {})[idx] = bool(enabled)
        update_toggle_visual('upscale', idx, enabled)
    
    # 4. Toggle ALL controlnet models  
    for idx in range(len(controlnet_models)):
        toggle_states.setdefault('controlnet', {})[idx] = bool(enabled)
        update_toggle_visual('controlnet', idx, enabled)
    
    # 5. Toggle ALL VAE models
    for idx in range(len(vae_models)):
        toggle_states.setdefault('vae', {})[idx] = bool(enabled)
        update_toggle_visual('vae', idx, enabled)
    
    # 6. Toggle ALL CLIP models
    for idx in range(len(clip_models)):
        toggle_states.setdefault('clip', {})[idx] = bool(enabled)
        update_toggle_visual('clip', idx, enabled)
    
    # 7. Toggle ALL CLIP Vision models
    for idx in range(len(clip_vision_models)):
        toggle_states.setdefault('clip-vision', {})[idx] = bool(enabled)
        update_toggle_visual('clip-vision', idx, enabled)

# -----------------------------
# Startup Function
# -----------------------------
def startup_comfyui(b):
    # Toggle behavior: start or stop
    if not button_states['startup']['active']:
        # Start installation
        button_states['startup']['active'] = True
        b.description = "Stop Startup"
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
                logging.getLogger(__name__).exception("Parallel tasks failed: %s", e)
                dl_results, cl_results = [], []

                # Image monitoring removed: using static clickable HTML preview widgets instead

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

        t = threading.Thread(target=run_installation, daemon=True)
        button_states['startup']['process'] = t
        t.start()
    else:
        # Stop installation / perform cleanup
        button_states['startup']['active'] = False
        b.description = "Start Up"
        # Attempt to terminate processes and cleanup
        try:
            terminate_running_processes()
        except Exception:
            logging.getLogger(__name__).exception("Error terminating processes during stop")
        try:
            cleanup_installation_files()
        except Exception:
            logging.getLogger(__name__).exception("Error during cleanup_installation_files")
        # Reset UI and re-enable the button
        try:
            reset_ui_state()
        except Exception:
            pass
        b.disabled = False

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


# -----------------------------
# Cleanup and process termination helpers
# -----------------------------
def reset_ui_state():
    """Reset UI elements to their initial state (hide progress bars and reset labels)"""
    try:
        progress_container.value = """
        <div style="display:flex; justify-content:center; margin-bottom:20px;">
            <div class="progress-container" style="display:block; visibility: hidden;">
                <div class="progress-bar" style="width:0%;"></div>
            </div>
        </div>
        """
    except Exception:
        pass

    try:
        download_progress_container.value = """
        <div style="display:flex; justify-content:center; margin-bottom:20px;">
            <div class="download-progress-container" style="display:block; visibility: hidden;">
                <div class="download-progress-bar" style="width:0%;"></div>
            </div>
        </div>
        """
    except Exception:
        pass

    try:
        additional_downloads_progress_container.value = """
        <div style="display:flex; justify-content:center; margin-bottom:20px;">
            <div class="additional-progress-container" style="display:block; visibility: hidden;">
                <div class="additional-progress-bar" style="width:0%;"></div>
            </div>
        </div>
        """
    except Exception:
        pass

    try:
        status_label.value = "<div class='status-text' style='height: 26px; visibility: hidden;'>Placeholder</div>"
        download_status_label.value = "<div class='status-text' style='height: 26px; visibility: hidden;'>Placeholder</div>"
        additional_downloads_status_label.value = "<div class='status-text' style='height: 26px; visibility: hidden;'>Placeholder</div>"
    except Exception:
        pass


def cleanup_installation_files():
    """Remove installation artifacts while preserving workspace/Uploads and the start script."""
    import shutil
    import os
    try:
        current_dir = os.getcwd()
        preserve = [os.path.join('workspace', 'Uploads'), os.path.basename(__file__)]
        # List of likely installation targets to remove
        targets = ['ComfyUI', 'venv', '.git', 'models', 'custom_nodes', 'temp', 'downloads']
        for t in targets:
            path = os.path.join(current_dir, t)
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        logging.getLogger(__name__).info('Removed directory during cleanup: %s', path)
                    else:
                        os.remove(path)
                        logging.getLogger(__name__).info('Removed file during cleanup: %s', path)
                except Exception:
                    logging.getLogger(__name__).exception('Failed to remove during cleanup: %s', path)

        # Reset UI
        reset_ui_state()
        logging.getLogger(__name__).info('Cleanup completed successfully')
    except Exception:
        logging.getLogger(__name__).exception('Cleanup error')


def terminate_running_processes():
    """Terminate ComfyUI and common installation subprocesses if running."""
    try:
        if psutil is not None:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmd = ' '.join(proc.info.get('cmdline') or [])
                    if 'main.py' in cmd and 'venv' in cmd:
                        proc.terminate()
                        logging.getLogger(__name__).info('Terminated process: %s', proc.pid)
                except Exception:
                    pass

        # Try to kill pip/git child processes on POSIX-like systems; on Windows these commands are no-ops
        try:
            import subprocess
            # Use shell-safe variants; ignore failures
            subprocess.run('pkill -f "pip install"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run('pkill -f "git clone"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    except Exception:
        logging.getLogger(__name__).exception('Error terminating processes')


# Downloads-only handler: runs only the downloads (no clone/venv/start)
def start_downloads_only(b):
    # Toggle-based start/stop for downloads
    if not button_states['downloads']['active']:
        button_states['downloads']['active'] = True
        b.description = "Stop Downloads"
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

        t = threading.Thread(target=run_downloads, daemon=True)
        button_states['downloads']['process'] = t
        t.start()
    else:
        # stop downloads in-progress
        button_states['downloads']['active'] = False
        b.description = "start selected Downloads"
        try:
            terminate_running_processes()
        except Exception:
            logging.getLogger(__name__).exception("Error terminating processes during downloads stop")
        try:
            cleanup_installation_files()
        except Exception:
            logging.getLogger(__name__).exception("Error during cleanup_installation_files")
        try:
            reset_ui_state()
        except Exception:
            pass
        b.disabled = False


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

# Create all category containers using standard category widget pattern
category_containers = {}

# Reusable helper: zip ComfyUI output directory to a destination path
def _zip_output_and_save(dest_path, progress_callback=None):
    import zipfile, time
    try:
        output_dir = os.path.join('workspace', 'ComfyUI', 'output')
        if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
            raise FileNotFoundError(f'Output folder not found: {output_dir}')

        # collect files first to allow a simple progress estimate
        files = []
        for root, dirs, filenames in os.walk(output_dir):
            for fn in filenames:
                files.append(os.path.join(root, fn))

        total = len(files) or 1
        done = 0

        with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for full in files:
                arcname = os.path.relpath(full, output_dir)
                zf.write(full, arcname)
                done += 1
                pct = int((done / total) * 100)
                if progress_callback:
                    try:
                        progress_callback(pct, f'Zipping: {os.path.basename(full)}')
                    except Exception:
                        pass
        return True, None
    except Exception as e:
        return False, str(e)

# New simplified generation-downloads category data
generation_downloads = [
    {
        "name": "Automatic Generation Downloads every 30 minutes",
        "info": "Download ComfyUI output automatically every 30 minutes",
        "required": False,
        "interval": 30
    },
    {
        "name": "Automatic Generation Downloads every 60 minutes",
        "info": "Download ComfyUI output automatically every 60 minutes",
        "required": False,
        "interval": 60
    },
    {
        "name": "Automatic Generation Downloads every 90 minutes",
        "info": "Download ComfyUI output automatically every 90 minutes",
        "required": False,
        "interval": 90
    },
    {
        "name": "Set Generations Downloads Timer",
        "info": "Master toggle to enable/disable automatic downloads",
        "required": False,
        "master": True
    }
]

# Insert into category_data (replace any existing generation-downloads key)
category_data['generation-downloads'] = generation_downloads

# Create standard category widgets for all categories
for category_id, label in category_labels.items():
    category_containers[category_id] = create_category_widget(
        category_id, label, category_data.get(category_id, [])
    )
    category_containers[category_id].layout.display = 'none'  # Initially hidden

# Post-process: add manual download button to the generation-downloads category content
try:
    gen_container = category_containers.get('generation-downloads')
    if gen_container is not None:
        # gen_container.children[1] is the VBox content box created by create_category_widget
        content_box = gen_container.children[1]
        # create manual download button
        manual_download_btn = widgets.Button(description='Download Generations Now', _dom_classes=['homogenized-button'], layout=widgets.Layout(width='280px', height='40px'))

        def _manual_download(b):
            b.disabled = True
            # build dest path: workspace/downloads/Comfy_Generations_<ts>/Comfy_Generations_<ts>.zip
            try:
                import datetime
                ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                folder_name = f'Comfy_Generations_{ts}'
                dest_dir = os.path.join('workspace', 'downloads', folder_name)
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, f'Comfy_Generations_{ts}.zip')
            except Exception:
                dest_path = os.path.join('workspace', 'downloads', f'Comfy_Generations_{int(time.time())}.zip')

            def _worker():
                update_additional_downloads_progress(0, 'Preparing download...')
                ok, err = _zip_output_and_save(dest_path, progress_callback=update_additional_downloads_progress)
                if ok:
                    update_additional_downloads_progress(100, 'Download ready')
                else:
                    update_additional_downloads_progress(0, f'Download failed: {err}')
                time.sleep(1.0)
                update_additional_downloads_progress(0, 'Additional downloads...')
                b.disabled = False

            threading.Thread(target=_worker, daemon=True).start()

        manual_download_btn.on_click(_manual_download)

        # Append manual button to the content box (standard vertical layout)
        # content_box is a VBox of rows; we append at the end
        try:
            # Center the manual download button and add a small spacer
            centered_btn = widgets.HBox([manual_download_btn], layout=widgets.Layout(justify_content='center', width='100%'))

            # Create timer display (now + 2.5 hours)
            try:
                import datetime
                now = datetime.datetime.now()
                target = now + datetime.timedelta(hours=2.5)
                timer_html = widgets.HTML(value=f"<div style='text-align:center; font-weight:bold; color:#1A237E; margin:10px;'>Set Timer: {now.strftime('%Y-%m-%d %H:%M:%S')} &nbsp; -> &nbsp; {target.strftime('%Y-%m-%d %H:%M:%S')} (+2.5 hours)</div>")
            except Exception:
                timer_html = widgets.HTML(value="<div style='text-align:center; font-weight:bold; color:#1A237E; margin:10px;'>Set Timer: --</div>")

            content_box.children = tuple(list(content_box.children) + [widgets.HTML('<div style="height:8px"></div>'), centered_btn, timer_html])
        except Exception:
            pass
except Exception:
    pass

# Create main container (header_box and downloads_container are inserted later)

# Create a fixed header area under the title that holds status, progress, link and startup controls
# We want the advanced (triangle) button below the Start Up button.
# Create a top row (vertical) that stacks the OPEN link above the Start Up button
open_link_html = widgets.HTML(value=f"<a href=\"{public_url}\" target=\"_blank\" class=\"open-link-text\">Open Comfy UI</a>")

top_row_children = [open_link_html, startup_btn]
# Positioning: increase gap and center vertically between status and Start Up button
top_row = widgets.VBox(top_row_children, layout=widgets.Layout(gap='25px', align_items='center', margin='8vh 0 0 0', justify_content='center'))

# Create a hidden civitai input row that will expand directly under the advanced button
# New compact blue-styled input container with label, input, and Get API Key link

# New label for the token field (keeps layout compact)
civitai_label = widgets.HTML(value='<span class="civitai-label">CivitAI Token:</span>')

# Re-create the token input widget to be consistent with the new layout width
civitai_token_widget = widgets.Text(
    value=load_api_key(),
    placeholder='Enter your CivitAI API token',
    layout=widgets.Layout(width='420px', height='36px')
)
try:
    civitai_token_widget.add_class('civitai-input-field')
except Exception:
    if 'civitai-input-field' not in getattr(civitai_token_widget, '_dom_classes', []):
        civitai_token_widget._dom_classes = getattr(civitai_token_widget, '_dom_classes', []) + ['civitai-input-field']

# Register observer to save changes
civitai_token_widget.observe(save_key_on_change, names='value')

# Compose the inner row: label, input, get-key link
# Compose inner content (token only)
civitai_container_content = widgets.HBox([civitai_token_widget],
                                          layout=widgets.Layout(align_items='center', gap='12px', width='100%'))

# Wrap in the new blue input container (token only, centered, hidden by default)
civitai_input_row = widgets.HBox([civitai_container_content],
                                 layout=widgets.Layout(align_items='center', justify_content='center',
                                                      width='100%', margin='6px 0px', display='none'))
try:
    civitai_input_row.add_class('civitai-input-container')
except Exception:
    if 'civitai-input-container' not in getattr(civitai_input_row, '_dom_classes', []):
        civitai_input_row._dom_classes = getattr(civitai_input_row, '_dom_classes', []) + ['civitai-input-container']

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

# --- User-provided extended code block inserted below 'start selected Downloads' ---
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
try:
    import psutil
except ImportError:
    psutil = None
    # Note: psutil optional - status monitoring will be disabled when absent
    # Use logging to record environment-level issues without spamming stdout
    # logging will be configured below; log this situation later if needed
    pass

# Configure module logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
if psutil is None:
    logger.info("psutil not available; ComfyUI status monitoring will be disabled.")

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
    logging.getLogger(__name__).info(f"Installing missing packages: {missing}")
    try:
        # Use sys.executable to call the same Python interpreter
        cmd = [sys.executable, "-m", "pip", "install"] + missing
        import subprocess
        subprocess.check_call(cmd)
    except Exception as e:
        logging.getLogger(__name__).exception("Automatic installation of requirements failed: %s", e)
        logging.getLogger(__name__).warning("Please manually install the required packages and re-run this script: pip install ipywidgets requests")

_bootstrap_requirements()


# -----------------------------
# API Key File Management
# -----------------------------
def load_api_key():
    """Read API key from workspace/Uploads/Civit Ai Key/CivitAi Api Key.txt
    Returns the last line of the file (most recent key) or empty string if not found"""
    try:
        api_key_path = os.path.join('workspace', 'Uploads', 'Civit Ai Key', 'CivitAi Api Key.txt')
        if os.path.exists(api_key_path):
            with open(api_key_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    # Return the last non-empty line (most recent key)
                    for line in reversed(lines):
                        line = line.strip()
                        if line:
                            return line
        return ""
    except Exception as e:
        logging.getLogger(__name__).exception("Error loading API key: %s", e)
        return ""

def save_api_key(key):
    """Save API key to workspace/Uploads/Civit Ai Key/CivitAi Api Key.txt
    Appends the key as a new line to maintain history"""
    try:
        if not key or not key.strip():
            return
        
        api_key_dir = os.path.join('workspace', 'Uploads', 'Civit Ai Key')
        api_key_path = os.path.join(api_key_dir, 'CivitAi Api Key.txt')
        
        # Create directory if it doesn't exist
        os.makedirs(api_key_dir, exist_ok=True)
        
        # Append new key with timestamp comment
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(api_key_path, 'a', encoding='utf-8') as f:
            f.write(f"# Added {timestamp}\n{key.strip()}\n")
            
    except Exception as e:
        logging.getLogger(__name__).exception("Error saving API key: %s", e)

def save_key_on_change(change):
    """Observer function to automatically save API key when changed"""
    if change['type'] == 'change' and change['name'] == 'value':
        new_value = change['new']
        if new_value and new_value.strip():
            save_api_key(new_value)


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
# (Remaining functions and code reused from the user's block are intentionally omitted here)
# The user asked to add "this section to the code below start selected downloads". The full block
# was already present in the file earlier in the workspace and may duplicate definitions.
# To avoid duplicate-symbol errors, we import only helper functions and constants above,
# and leave the rest of the user's block re-used in the existing file context.
# If you'd like the entire block re-inserted (including duplicate functions), tell me and I will add it.
# --- End inserted block ---

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
    if not hasattr(flux_toggle_btn, '_dom_classes'):
        try:
            flux_toggle_btn._dom_classes = []
        except Exception:
            pass
    if 'custom-toggle' not in getattr(flux_toggle_btn, '_dom_classes', []):
        flux_toggle_btn._dom_classes = getattr(flux_toggle_btn, '_dom_classes', []) + ['custom-toggle']

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

    # call helper to toggle the comprehensive standard installation
    set_standard_installation(enabled)

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
    if not hasattr(all_toggle_btn, '_dom_classes'):
        try:
            all_toggle_btn._dom_classes = []
        except Exception:
            pass
    if 'custom-toggle' not in getattr(all_toggle_btn, '_dom_classes', []):
        all_toggle_btn._dom_classes = getattr(all_toggle_btn, '_dom_classes', []) + ['custom-toggle']

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
        if not hasattr(all_toggle_btn, '_dom_classes'):
            try:
                all_toggle_btn._dom_classes = []
            except Exception:
                pass
        if enabled and 'active' not in getattr(all_toggle_btn, '_dom_classes', []):
            all_toggle_btn._dom_classes = getattr(all_toggle_btn, '_dom_classes', []) + ['active']
        if not enabled and 'active' in getattr(all_toggle_btn, '_dom_classes', []):
            all_toggle_btn._dom_classes = [c for c in getattr(all_toggle_btn, '_dom_classes', []) if c != 'active']

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
    if not hasattr(disney_toggle_btn, '_dom_classes'):
        try:
            disney_toggle_btn._dom_classes = []
        except Exception:
            pass
    if 'custom-toggle' not in getattr(disney_toggle_btn, '_dom_classes', []):
        disney_toggle_btn._dom_classes = getattr(disney_toggle_btn, '_dom_classes', []) + ['custom-toggle']

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
        if not hasattr(disney_toggle_btn, '_dom_classes'):
            try:
                disney_toggle_btn._dom_classes = []
            except Exception:
                pass
        if enabled and 'active' not in getattr(disney_toggle_btn, '_dom_classes', []):
            disney_toggle_btn._dom_classes = getattr(disney_toggle_btn, '_dom_classes', []) + ['active']
        if not enabled and 'active' in getattr(disney_toggle_btn, '_dom_classes', []):
            disney_toggle_btn._dom_classes = [c for c in getattr(disney_toggle_btn, '_dom_classes', []) if c != 'active']

    # preserve existing preset selection behavior
    set_disney_preset(enabled)

disney_toggle_btn.on_click(_on_disney_toggle_click)

disney_row = widgets.HBox([disney_toggle_btn, disney_label], layout=widgets.Layout(align_items='Center', width='800px', margin='5px 0px'))
try:
    disney_row.add_class('item-row')
except Exception:
    if 'item-row' not in disney_row._dom_classes:
        disney_row._dom_classes = disney_row._dom_classes + ['item-row']

# --- Disney preview (simplified PIL/HTML display as requested) ---
disney_row = disney_row  # existing toggle row

# Reuse existing Disney toggle/button and label
disney_toggle_btn = disney_toggle_btn
disney_label = disney_label

def _on_disney_toggle_click_user(b):
    # Reuse existing toggle behavior
    _on_disney_toggle_click(b)

disney_toggle_btn.on_click(_on_disney_toggle_click_user)

disney_row = widgets.HBox([disney_toggle_btn, disney_label], layout=widgets.Layout(align_items='Center', width='800px', margin='5px 0px'))
try:
    disney_row.add_class('item-row')
except Exception:
    if 'item-row' not in getattr(disney_row, '_dom_classes', []):
        try:
            disney_row._dom_classes = disney_row._dom_classes + ['item-row']
        except Exception:
            pass

# Disney container with simplified clickable image
def show_clickable_image_html(image_path, max_width=800):
    """Return a simple clickable-image HTML string that shows an alert when clicked.

    Requires an explicit `image_path` to avoid implicit file references in the module.
    """
    if not image_path:
        raise ValueError("show_clickable_image_html requires an explicit image_path")
    return f'''<div style="text-align:center; padding:10px;"><img src="{image_path}" style="max-width:{max_width}px; height:auto; border-radius:8px; box-shadow:0 4px 8px rgba(0,0,0,0.1); cursor:pointer; display:block; margin:10px auto;" onclick="alert('preset image clicked');"></div>'''

# Removed inline preview image — keep only the toggle row for Disney
# Build 6-method test row for Disney preset
base_img = os.path.join('.', 'Uploads', 'ComfyUI_00083_.png')
disney_images_html = generate_triple_image_html(base_img, 'Disney Animation')

disney_content_row = widgets.HBox([
    disney_row,
    widgets.HTML(value=disney_images_html)
], layout=widgets.Layout(align_items='center', width='100%', gap='20px'))

disney_container = widgets.VBox([disney_content_row], layout=widgets.Layout(width='900px', align_items='center', margin='5px 0px'))


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
    if not hasattr(impasto_toggle_btn, '_dom_classes'):
        try:
            impasto_toggle_btn._dom_classes = []
        except Exception:
            pass
    if 'custom-toggle' not in getattr(impasto_toggle_btn, '_dom_classes', []):
        impasto_toggle_btn._dom_classes = getattr(impasto_toggle_btn, '_dom_classes', []) + ['custom-toggle']

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
        if not hasattr(impasto_toggle_btn, '_dom_classes'):
            try:
                impasto_toggle_btn._dom_classes = []
            except Exception:
                pass
        if enabled and 'active' not in getattr(impasto_toggle_btn, '_dom_classes', []):
            impasto_toggle_btn._dom_classes = getattr(impasto_toggle_btn, '_dom_classes', []) + ['active']
        if not enabled and 'active' in getattr(impasto_toggle_btn, '_dom_classes', []):
            impasto_toggle_btn._dom_classes = [c for c in getattr(impasto_toggle_btn, '_dom_classes', []) if c != 'active']

    # preserve existing preset selection behavior
    set_impasto_preset(enabled)

impasto_toggle_btn.on_click(_on_impasto_toggle_click)

impasto_row = widgets.HBox([impasto_toggle_btn, impasto_label], layout=widgets.Layout(align_items='center', width='800px', margin='5px 0px'))
try:
    impasto_row.add_class('item-row')
except Exception:
    if 'item-row' not in impasto_row._dom_classes:
        impasto_row._dom_classes = impasto_row._dom_classes + ['item-row']

# --- Impasto preview (simplified PIL/HTML display as requested) ---
impasto_row = impasto_row  # existing toggle row

# Reuse existing Impasto toggle/button and label
impasto_toggle_btn = impasto_toggle_btn
impasto_label = impasto_label

def _on_impasto_toggle_click_user(b):
    # Reuse existing toggle behavior
    _on_impasto_toggle_click(b)

impasto_toggle_btn.on_click(_on_impasto_toggle_click_user)

impasto_row = widgets.HBox([impasto_toggle_btn, impasto_label], layout=widgets.Layout(align_items='center', width='800px', margin='5px 0px'))
try:
    impasto_row.add_class('item-row')
except Exception:
    if 'item-row' not in getattr(impasto_row, '_dom_classes', []):
        try:
            impasto_row._dom_classes = impasto_row._dom_classes + ['item-row']
        except Exception:
            pass

# NEW: Simple PIL/HTML image display for Impasto preset
from PIL import Image as PILImage
import matplotlib.pyplot as plt
from IPython.display import HTML, display

# Correct path for Impasto image
img_path = "./Uploads/Impasto_Workflow.png"

# Removed inline preview image — keep only the toggle row for Impasto
# Build 6-method test row for Impasto preset
base_img = os.path.join('.', 'Uploads', 'ComfyUI_00083_.png')
impasto_images_html = generate_triple_image_html(base_img, 'Impasto')

impasto_content_row = widgets.HBox([
    impasto_row,
    widgets.HTML(value=impasto_images_html)
], layout=widgets.Layout(align_items='center', width='100%', gap='20px'))

impasto_container = widgets.VBox([impasto_content_row], layout=widgets.Layout(width='900px', align_items='center', margin='5px 0px'))

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
    if not hasattr(cinematic_toggle_btn, '_dom_classes'):
        try:
            cinematic_toggle_btn._dom_classes = []
        except Exception:
            pass
    if 'custom-toggle' not in getattr(cinematic_toggle_btn, '_dom_classes', []):
        cinematic_toggle_btn._dom_classes = getattr(cinematic_toggle_btn, '_dom_classes', []) + ['custom-toggle']

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
        # TODO: Find correct model ID on Civitai and replace the URL below
        # "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",  # You'll need to find the correct model ID
        "url": None,
        "info": "Crazy Girlfriend Mix [XL/PONY] LoRA",
        "required": False,
        "filename": "Crazy_Girlfriend_Mix_XL_PONY.safetensors",
        "dest_dir": "models/loras"
    },
    {
        "name": "Insta_Baddie_PONY.safetensors",
        # TODO: Find correct model ID on Civitai and replace the URL below
        # "url": "https://civitai.com/api/download/models/[NEED_MODEL_ID]",  # You'll need to find the correct model ID
        "url": None,
        "info": "Insta Baddie[PONY] LoRA",
        "required": False,
        "filename": "Insta_Baddie_PONY.safetensors",
        "dest_dir": "models/loras"
    }
]

# Uncomment the following line to add the missing LoRAs to your list:
# loras.extend(missing_loras)

# Debug messages commented out per UI polish request
# print("Added Disney Animation, Impasto, and Cinematic Realistic Photography preset toggles!")
# print("Note: Some LoRAs may need correct Civitai model IDs to be added to download properly.")

def _on_cinematic_toggle_click(b):
    cinematic_preset_state['enabled'] = not cinematic_preset_state['enabled']
    enabled = cinematic_preset_state['enabled']
    try:
        if enabled:
            cinematic_toggle_btn.add_class('active')
        else:
            cinematic_toggle_btn.remove_class('active')
    except Exception:
        if not hasattr(cinematic_toggle_btn, '_dom_classes'):
            try:
                cinematic_toggle_btn._dom_classes = []
            except Exception:
                pass
        if enabled and 'active' not in getattr(cinematic_toggle_btn, '_dom_classes', []):
            cinematic_toggle_btn._dom_classes = getattr(cinematic_toggle_btn, '_dom_classes', []) + ['active']
        if not enabled and 'active' in getattr(cinematic_toggle_btn, '_dom_classes', []):
            cinematic_toggle_btn._dom_classes = [c for c in getattr(cinematic_toggle_btn, '_dom_classes', []) if c != 'active']

    # preserve existing preset selection behavior
    set_cinematic_preset(enabled)

cinematic_toggle_btn.on_click(_on_cinematic_toggle_click)

cinematic_row = widgets.HBox([cinematic_toggle_btn, cinematic_label], layout=widgets.Layout(align_items='center', width='800px', margin='5px 0px'))
try:
    cinematic_row.add_class('item-row')
except Exception:
    if 'item-row' not in cinematic_row._dom_classes:
        cinematic_row._dom_classes = cinematic_row._dom_classes + ['item-row']

# Removed inline preview image — keep only the toggle row for Cinematic
# Build 6-method test row for Cinematic preset
base_img = os.path.join('.', 'Uploads', 'ComfyUI_00083_.png')
cinematic_images_html = generate_triple_image_html(base_img, 'Cinematic Realistic Photography')

cinematic_content_row = widgets.HBox([
    cinematic_row,
    widgets.HTML(value=cinematic_images_html)
], layout=widgets.Layout(align_items='center', width='100%', gap='20px'))

cinematic_container = widgets.VBox([cinematic_content_row], layout=widgets.Layout(width='900px', align_items='center', margin='5px 0px'))

# Notebook-friendly gallery helper removed to keep file focused on the three preset base64 previews.

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
    civitai_status_link,
    # Download-only progress/status (reserve space below the main progress)
    download_status_label,
    download_progress_container,
    # Additional downloads separate progress bar
    additional_downloads_status_label,
    additional_downloads_progress_container,
    controls_box
], layout=widgets.Layout(align_items='center', width='100%', margin='0px 0px'))

# Main container now places header fixed under title and categories below
main_container = widgets.VBox(
    [title_row, header_box, downloads_container] + list(category_containers.values()),
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
    if not hasattr(main_container, '_dom_classes'):
        try:
            main_container._dom_classes = []
        except Exception:
            pass
    if 'comfy-root' not in getattr(main_container, '_dom_classes', []):
        main_container._dom_classes = getattr(main_container, '_dom_classes', []) + ['comfy-root']

display(main_container)

# -----------------------------
# ComfyUI Status Monitoring
# -----------------------------
def check_comfyui_status():
    """Check if ComfyUI is running on port 8188"""
    if psutil is None:
        return False
    
    try:
        # Check if any process is listening on port 8188
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == 8188 and conn.status == psutil.CONN_LISTEN:
                return True
        return False
    except Exception:
        return False

def update_comfyui_link_status():
    """Background thread to monitor ComfyUI status and update link styling"""
    while True:
        try:
            is_running = check_comfyui_status()
            
            # Update the link styling based on ComfyUI status
            if is_running:
                # Add 'running' class to make link underlined
                open_link_html.value = f'<a href="{public_url}" target="_blank" class="open-link-text running">Open Comfy UI</a>'
            else:
                # Remove 'running' class (no underline)
                open_link_html.value = f'<a href="{public_url}" target="_blank" class="open-link-text">Open Comfy UI</a>'
            
            # Check every 5 seconds
            time.sleep(5)
            
        except Exception as e:
            # If monitoring fails, just continue without status updates
            time.sleep(10)

# Start the monitoring thread if psutil is available
if psutil is not None:
    monitoring_thread = threading.Thread(target=update_comfyui_link_status, daemon=True)
    monitoring_thread.start()
else:
    # ComfyUI status monitoring disabled when psutil is not available. Silent fallback.
    pass

# Debug functions were intentionally removed to reduce console clutter.

# clickable_image_responsive.py

from IPython.display import display, HTML
import os

def show_clickable_image(image_path, write_html=False):
    """
    Display a single responsive, clickable image in a Jupyter notebook.
    - image_path: local path (relative to notebook working dir) or absolute path.
    - write_html: if True, writes 'clickable_image.html' (standalone) next to notebook.
    
    Behavior on click:
    1) Attempts to execute `print('image clicked')` in the Jupyter kernel (classic Jupyter).
    2) Always shows a browser alert 'image clicked' (fallback).
    """
    # Ensure path is URL-friendly for HTML. If file exists locally, convert to a relative path.
    # (Jupyter will serve it if it's in the working dir or accessible path.)
    if image_path is None:
        raise ValueError("show_clickable_image requires an explicit image_path")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Minimal responsive CSS + JS that attempts to call back to the Python kernel then alerts.
    html = f"""
    <style>
      /* responsive image: scales with container, keeps aspect ratio */
      .clickable-img {{
        display: block;
        max-width: 90vw;   /* at most 90% of viewport width */
        width: 100%;       /* shrink/grow with container */
        height: auto;      /* keep aspect ratio */
        cursor: pointer;
        margin: 0 auto;
      }}
      /* optional wrapper to limit image width in large screens */
      .img-wrapper {{
        max-width: 900px;  /* choose max pixel width you like */
        margin: 0 auto;
      }}
    </style>

    <div class="img-wrapper">
      <img
        src="{image_path}"
        class="clickable-img"
        alt="clickable image"
        onclick="(function(){{
            // Try to send a command to the classic Jupyter kernel (works in notebook)
            try {{
                if (typeof IPython !== 'undefined' && IPython.notebook && IPython.notebook.kernel) {{
                    IPython.notebook.kernel.execute(\"print('image clicked')\");
                }}
            }} catch(e) {{
                // ignore kernel errors
            }}
            // Always show a browser alert as fallback and visual confirmation
            alert('image clicked');
        }})();"
      />
    </div>
    """

    display(HTML(html))

    if write_html:
        fname = "clickable_image.html"
        with open(fname, "w", encoding="utf-8") as f:
            # wrap html in a full document for standalone opening
            f.write(f"<!doctype html><html><head><meta charset='utf-8'><title>Clickable Image</title>{html}</head><body></body></html>")
        print(f"Wrote standalone HTML to: {fname}")


# Example usage: call `show_clickable_image('/path/to/image.png')` in a notebook cell when needed.

