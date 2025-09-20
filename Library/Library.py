DOWNLOAD_LIBRARY = {
    # Core ComfyUI Components
    "custom_nodes": "Custom Nodes",
    "checkpoints": "Model Checkpoints", 
    "loras": "LoRA Models",
    "embeddings": "Text Embeddings",
    "clip_models": "CLIP Text Encoders",
    "clip_vision_models": "CLIP Vision Models",
    "vae_models": "VAE Models",
    "controlnet_models": "ControlNet Models",
    "upscale_models": "Upscale Models",
    "additional_downloads": "Additional Downloads",

    # Checkpoint Subcategories
    "checkpoint_subcategories": {
        "sd15_checkpoints": "SD1.5 Checkpoints",
        "sdxl_checkpoints": "SDXL Checkpoints",
        "flux_checkpoints": "FLUX Checkpoints"
    },

    # LoRA Subcategories  
    "lora_subcategories": {
        "sd15_loras": "SD1.5 LoRAs",
        "sdxl_loras": "SDXL LoRAs", 
        "flux_loras": "FLUX LoRAs"
    },

    # SDXL Sub-subcategories
    "sdxl_subcategories": {
        "pony_models": "Pony Models",
        "illustrious_models": "Illustrious Models"
    },

    # Custom Nodes
    "custom_nodes": [
        {
            "display_title": "RGThree Comfy Utilities",
            "name": "rgthree-comfy",
            "source_page": "https://github.com/rgthree/rgthree-comfy",
            "url": "https://github.com/rgthree/rgthree-comfy.git",
            "filename": "rgthree-comfy",
            "dest_dir": "custom_nodes",
            "info": "Quality of life nodes and utilities for ComfyUI",
            "required": False
        },
        {
            "display_title": "LoRA Info Node",
            "name": "lora-info",
            "source_page": "https://github.com/jitcoder/lora-info",
            "url": "https://github.com/jitcoder/lora-info.git",
            "filename": "lora-info",
            "dest_dir": "custom_nodes",
            "info": "LoRA information display node",
            "required": False
        },
        {
            "display_title": "ComfyUI Impact Pack",
            "name": "ComfyUI-Impact-Pack",
            "source_page": "https://github.com/ltdrdata/ComfyUI-Impact-Pack",
            "url": "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git",
            "filename": "ComfyUI-Impact-Pack",
            "dest_dir": "custom_nodes",
            "info": "Advanced image processing and segmentation nodes",
            "required": False
        },
        {
            "display_title": "ComfyUI Easy Use",
            "name": "ComfyUI-Easy-Use",
            "source_page": "https://github.com/yolain/ComfyUI-Easy-Use",
            "url": "https://github.com/yolain/ComfyUI-Easy-Use.git",
            "filename": "ComfyUI-Easy-Use",
            "dest_dir": "custom_nodes",
            "info": "Simplified workflow nodes for beginners",
            "required": False
        },
        {
            "display_title": "ComfyUI Manager (Essential)",
            "name": "ComfyUI-Manager",
            "source_page": "https://github.com/ltdrdata/ComfyUI-Manager",
            "url": "https://github.com/ltdrdata/ComfyUI-Manager.git",
            "filename": "ComfyUI-Manager",
            "dest_dir": "custom_nodes",
            "info": "Essential node manager for ComfyUI",
            "required": True
        },
        {
            "display_title": "ComfyUI Custom Scripts",
            "name": "ComfyUI-Custom-Scripts",
            "source_page": "https://github.com/pythongosssss/ComfyUI-Custom-Scripts",
            "url": "https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git",
            "filename": "ComfyUI-Custom-Scripts",
            "dest_dir": "custom_nodes",
            "info": "Custom scripts and workflow enhancements",
            "required": False
        },
        {
            "display_title": "ComfyUI Inspyrenet Rembg",
            "name": "ComfyUI-Inspyrenet-Rembg",
            "source_page": "https://github.com/john-mnz/ComfyUI-Inspyrenet-Rembg",
            "url": "https://github.com/john-mnz/ComfyUI-Inspyrenet-Rembg.git",
            "filename": "ComfyUI-Inspyrenet-Rembg",
            "dest_dir": "custom_nodes",
            "info": "Advanced background removal using Inspyrenet",
            "required": False
        },
        {
            "display_title": "Bjornulf Custom Nodes",
            "name": "Bjornulf_custom_nodes",
            "source_page": "https://github.com/justUmen/Bjornulf_custom_nodes",
            "url": "https://github.com/justUmen/Bjornulf_custom_nodes.git",
            "filename": "Bjornulf_custom_nodes",
            "dest_dir": "custom_nodes",
            "info": "Specialized custom nodes by Bjornulf",
            "required": False
        },
        {
            "display_title": "Comfy Image Saver",
            "name": "comfy-image-saver",
            "source_page": "https://github.com/giriss/comfy-image-saver",
            "url": "https://github.com/giriss/comfy-image-saver.git",
            "filename": "comfy-image-saver",
            "dest_dir": "custom_nodes",
            "info": "Enhanced image saving with metadata",
            "required": False
        },
        {
            "display_title": "ComfyUI Impact Subpack",
            "name": "ComfyUI-Impact-Subpack",
            "source_page": "https://github.com/ltdrdata/ComfyUI-Impact-Subpack",
            "url": "https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git",
            "filename": "ComfyUI-Impact-Subpack",
            "dest_dir": "custom_nodes",
            "info": "Additional impact pack nodes and utilities",
            "required": False
        },
        {
            "display_title": "WAS Node Suite ComfyUI",
            "name": "was-node-suite-comfyui",
            "source_page": "https://github.com/ltdrdata/was-node-suite-comfyui",
            "url": "https://github.com/ltdrdata/was-node-suite-comfyui.git",
            "filename": "was-node-suite-comfyui",
            "dest_dir": "custom_nodes",
            "info": "Comprehensive node suite with text and image tools",
            "required": False
        }
    ],

    # Model Checkpoints by Subcategory
    "checkpoints": {
        "sd15_checkpoints": [
{
    "display_title": "SD1.5",
                "name": "SD_1,5.safetensors",
                "source_page": "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5",
                "url": "https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors?download=true",
                "filename": "SD_1,5.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "Stable Diffusion 1.5 pruned EMA-only model",
                "required": False
            },
            {
                "display_title": "SD1.5 Epic Realism",
                "name": "SD1.5_Epic_Realism.safetensors",
                "source_page": "https://civitai.com/models/143906",
                "url": "https://civitai.com/api/download/models/143906?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SD1.5_Epic_Realism.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "SD1.5 Epic Realism model from Civitai",
                "required": False
            },
            {
                "display_title": "SD1.5 DreamShaper",
                "name": "SD1.5_DreamShaper.safetensors",
                "source_page": "https://civitai.com/models/128713",
                "url": "https://civitai.com/api/download/models/128713?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SD1.5_DreamShaper.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "SD1.5 DreamShaper model for versatile generation",
                "required": False
            },
            {
                "display_title": "SD1.5 ReV Animated",
                "name": "SD1.5_ReVAnimated.safetensors",
                "source_page": "https://civitai.com/models/425083",
                "url": "https://civitai.com/api/download/models/425083?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SD1.5_ReVAnimated.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "SD1.5 ReV Animated model for animation styles",
                "required": False
            },
            {
                "display_title": "SD1.5 Deliberate",
                "name": "SD1.5_Deliberate.safetensors",
                "source_page": "https://huggingface.co/XpucT/Deliberate",
                "url": "https://huggingface.co/XpucT/Deliberate/resolve/main/Deliberate_v6.safetensors?download=true",
                "filename": "SD1.5_Deliberate.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "SD1.5 Deliberate v6 model for high-quality generation",
                "required": False
            },
            {
                "display_title": "SD1.5 Realistic Vision V60B1",
                "name": "SD1.5_Realistic_Vision_V60B1_v51VAE.safetensors",
                "source_page": "https://civitai.com/models/130072",
                "url": "https://civitai.com/api/download/models/130072?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SD1.5_Realistic_Vision_V60B1_v51VAE.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "SD1.5 Realistic Vision V60B1 with VAE",
                "required": False
            },
            {
                "display_title": "SD1.5 Perfect Deliberate",
                "name": "SD1.5_PerfectDeliberate.safetensors",
                "source_page": "https://civitai.com/models/253055",
                "url": "https://civitai.com/api/download/models/253055?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SD1.5_PerfectDeliberate.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "SD1.5 Perfect Deliberate model for enhanced quality",
                "required": False
            }
        ],
        "sdxl_checkpoints": {
            "general": [
                {
                    "display_title": "SDXL",
                    "name": "SDXL.safetensors",
                    "source_page": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
                    "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors?download=true",
                    "filename": "SDXL.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Stable Diffusion XL Base 1.0 model",
                    "required": False
                },
                {
                    "display_title": "SDXL WildCard",
                    "name": "SDXL_WildCard.safetensors",
                    "source_page": "https://civitai.com/models/345685",
                    "url": "https://civitai.com/api/download/models/345685?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "SDXL_WildCard.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "SDXL WildCard model from Civitai",
                    "required": False
                },
                {
                    "display_title": "SDXL CyberRealistic XL",
                    "name": "SDXL_CyberRealisticXL.safetensors",
                    "source_page": "https://civitai.com/models/1609607",
                    "url": "https://civitai.com/api/download/models/1609607?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "SDXL_CyberRealisticXL.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "SDXL CyberRealistic XL model for cyberpunk styles",
                    "required": False
                },
                {
                    "display_title": "ZavyChromaXL v80",
                    "name": "zavychromaxl_v80.safetensors",
                    "source_page": "https://huggingface.co/misri/zavychromaxl_v80",
                    "url": "https://huggingface.co/misri/zavychromaxl_v80/resolve/main/zavychromaxl_v80.safetensors",
                    "filename": "zavychromaxl_v80.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "ZavyChromaXL v80 model for enhanced color and detail",
                    "required": False
                },
                {
                    "display_title": "JuggernautXL v6",
                    "name": "juggernautXL_version6Rundiffusion.safetensors",
                    "source_page": "https://huggingface.co/lllyasviel/fav_models",
                    "url": "https://huggingface.co/lllyasviel/fav_models/resolve/main/fav/juggernautXL_version6Rundiffusion.safetensors",
                    "filename": "juggernautXL_version6Rundiffusion.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "JuggernautXL v6 model for high-quality generation",
                    "required": False
                },
                {
                    "display_title": "DreamShaper XL",
                    "name": "DreamShaperXL.safetensors",
                    "source_page": "https://civitai.com/models/351306",
                    "url": "https://civitai.com/api/download/models/351306?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "DreamShaperXL.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "DreamShaper XL model for versatile SDXL generation",
                    "required": False
                },
                {
                    "display_title": "SDXL Perfect Deliberate",
                    "name": "SDXL_PerfectDeliberate.safetensors",
                    "source_page": "https://civitai.com/models/2001227",
                    "url": "https://civitai.com/api/download/models/2001227?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "SDXL_PerfectDeliberate.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "SDXL Perfect Deliberate model for enhanced quality",
                    "required": False
                }
            ],
            "pony_models": [
                {
                    "display_title": "Pony Comix",
                    "name": "Pony_Comix.safetensors",
                    "source_page": "https://civitai.com/models/984463",
                    "url": "https://civitai.com/api/download/models/984463?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony_Comix.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Pony Comix model from Civitai",
                    "required": False
                },
                {
                    "display_title": "Pony Diffusion V6 XL",
                    "name": "Pony.safetensors",
                    "source_page": "https://civitai.com/models/290640",
                    "url": "https://civitai.com/api/download/models/290640?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Pony Diffusion V6 XL - Versatile SDXL",
                    "required": False
                },
                {
                    "display_title": "Pony CyberRealistic",
                    "name": "Pony_CyberRealistic.safetensors",
                    "source_page": "https://civitai.com/models/2178176",
                    "url": "https://civitai.com/api/download/models/2178176?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony_CyberRealistic.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "CyberRealistic Pony model",
                    "required": False
                },
                {
                    "display_title": "Pony Lucent",
                    "name": "Pony_Lucent.safetensors",
                    "source_page": "https://civitai.com/models/1971591",
                    "url": "https://civitai.com/api/download/models/1971591?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony_Lucent.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Pony Lucent checkpoint",
                    "required": False
                },
                {
                    "display_title": "Pony DucHaiten Real",
                    "name": "Pony_DucHaiten_Real.safetensors",
                    "source_page": "https://civitai.com/models/695106",
                    "url": "https://civitai.com/api/download/models/695106?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony_DucHaiten_Real.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "DucHaiten Real Pony model",
                    "required": False
                },
                {
                    "display_title": "Pony Real Dream",
                    "name": "Pony_Real_Dream.safetensors",
                    "source_page": "https://civitai.com/models/2129811",
                    "url": "https://civitai.com/api/download/models/2129811?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony_Real_Dream.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Real Dream Pony checkpoint",
                    "required": False
                },
                {
                    "display_title": "Pony Real Merge",
                    "name": "Pony_Real_Merge.safetensors",
                    "source_page": "https://civitai.com/models/994131",
                    "url": "https://civitai.com/api/download/models/994131?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony_Real_Merge.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Real Merge Pony model",
                    "required": False
                },
                {
                    "display_title": "Pony Realism",
                    "name": "Pony_Realism.safetensors",
                    "source_page": "https://civitai.com/models/914390",
                    "url": "https://civitai.com/api/download/models/914390?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Pony_Realism.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Realism Pony checkpoint",
                    "required": False
                }
            ],
            "illustrious_models": [
                {
                    "display_title": "Illustrious",
                    "name": "Illustrious.safetensors",
                    "source_page": "https://civitai.com/models/889818",
                    "url": "https://civitai.com/api/download/models/889818?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Illustrious.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Illustrious base model",
                    "required": False
                },
                {
                    "display_title": "Illustrious AnIco",
                    "name": "Illustrious_AnIco.safetensors",
                    "source_page": "https://civitai.com/models/1641205",
                    "url": "https://civitai.com/api/download/models/1641205?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Illustrious_AnIco.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Illustrious AnIco variant",
                    "required": False
                },
                {
                    "display_title": "Illustrious Illustrij",
                    "name": "Illustrious_Illustrij.safetensors",
                    "source_page": "https://civitai.com/models/2186168",
                    "url": "https://civitai.com/api/download/models/2186168?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Illustrious_Illustrij.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Illustrious Illustrij model",
                    "required": False
                },
                {
                    "display_title": "Illustrious ToonMerge",
                    "name": "Illustrious_ToonMerge.safetensors",
                    "source_page": "https://civitai.com/models/1622588",
                    "url": "https://civitai.com/api/download/models/1622588?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Illustrious_ToonMerge.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Illustrious ToonMerge checkpoint",
                    "required": False
                },
                {
                    "display_title": "Illustrious SEMImergeij V6",
                    "name": "Illustrious_SEMImergeijV6.safetensors",
                    "source_page": "https://civitai.com/models/1920758",
                    "url": "https://civitai.com/api/download/models/1920758?token=fd4ae815a82358dab77c19eb48c9f2cf",
                    "filename": "Illustrious_SEMImergeijV6.safetensors",
                    "dest_dir": "models/checkpoints",
                    "info": "Illustrious SEMImergeij V6 model",
                    "required": False
                }
            ]
        },
        "flux_checkpoints": [
            {
                "display_title": "Flux Dev FP8",
                "name": "flux1-dev-fp8.safetensors",
                "source_page": "https://huggingface.co/Comfy-Org/flux1-dev",
                "url": "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors?download=true",
                "filename": "flux1-dev-fp8.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "FLUX.1 Dev FP8 model",
                "required": False
            },
            {
                "display_title": "Flux Schnell",
                "name": "Flux_Schnell.safetensors",
                "source_page": "https://huggingface.co/black-forest-labs/FLUX.1-schnell",
                "url": "https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/flux1-schnell.safetensors?download=true",
                "filename": "Flux_Schnell.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "FLUX.1 Schnell model",
                "required": False
            },
            {
                "display_title": "Flux Krea",
                "name": "Flux_Krea.safetensors",
                "source_page": "https://huggingface.co/black-forest-labs/FLUX.1-Krea-dev",
                "url": "https://huggingface.co/black-forest-labs/FLUX.1-Krea-dev/resolve/main/flux1-krea-dev.safetensors?download=true",
                "filename": "Flux_Krea.safetensors",
                "dest_dir": "models/checkpoints",
                "info": "FLUX.1 Krea development model",
                "required": False
            }
        ]
    },

    # LoRA Models by Subcategory
    "loras": {
        "sd15_loras": [],
        "sdxl_loras": [
            {
                "display_title": "SDXL ClassiPaint",
                "name": "SDXL_ClassiPaint.safetensors",
                "source_page": "https://civitai.com/models/356771",
                "url": "https://civitai.com/api/download/models/356771?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SDXL_ClassiPaint.safetensors",
                "dest_dir": "models/loras",
                "info": "SDXL ClassiPaint LoRA for classical painting styles",
                "required": False
            },
            {
                "display_title": "SDXL Greg Rutkowski",
                "name": "SDXL_Greg_Rutkowski.safetensors",
                "source_page": "https://civitai.com/models/127510",
                "url": "https://civitai.com/api/download/models/127510?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SDXL_Greg_Rutkowski.safetensors",
                "dest_dir": "models/loras",
                "info": "SDXL Greg Rutkowski LoRA for fantasy art styles",
                "required": False
            },
            {
                "display_title": "SDXL Pop Art Style",
                "name": "SDXL_Pop_Art_Style.safetensors",
                "source_page": "https://civitai.com/models/192584",
                "url": "https://civitai.com/api/download/models/192584?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SDXL_Pop_Art_Style.safetensors",
                "dest_dir": "models/loras",
                "info": "Pop Art Style for SDXL",
                "required": False
            },
            {
                "display_title": "SDXL LoRAs 2Steps",
                "name": "SDXL_loras_2Steps.safetensors",
                "source_page": "https://huggingface.co/ByteDance/SDXL-Lightning",
                "url": "https://huggingface.co/ByteDance/SDXL-Lightning/resolve/main/sdxl_lightning_2step_lora.safetensors?download=true",
                "filename": "SDXL_loras_2Steps.safetensors",
                "dest_dir": "models/loras",
                "info": "SDXL Lightning 2-step LoRA",
                "required": False
            },
            {
                "display_title": "Hyper-SDXL 8steps CFG LoRA",
                "name": "Hyper-SDXL-8steps-CFG-lora.safetensors",
                "source_page": "https://huggingface.co/ByteDance/Hyper-SD",
                "url": "https://huggingface.co/ByteDance/Hyper-SD/resolve/main/Hyper-SDXL-8steps-CFG-lora.safetensors",
                "filename": "Hyper-SDXL-8steps-CFG-lora.safetensors",
                "dest_dir": "models/loras",
                "info": "Hyper-SDXL 8-steps CFG LoRA",
                "required": False
            },
            {
                "display_title": "SDXL Lightning 8 Steps",
                "name": "SDXL_lightning_8_steps.safetensors",
                "source_page": "https://civitai.com/models/391999",
                "url": "https://civitai.com/api/download/models/391999?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SDXL_lightning_8_steps.safetensors",
                "dest_dir": "models/loras",
                "info": "SDXL Lightning 8-step LoRA",
                "required": False
            },
            {
                "display_title": "SDXL Lightning 2 Steps",
                "name": "SDXL_lightning_2_steps.safetensors",
                "source_page": "https://civitai.com/models/391994",
                "url": "https://civitai.com/api/download/models/391994?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "SDXL_lightning_2_steps.safetensors",
                "dest_dir": "models/loras",
                "info": "SDXL Lightning 2-step LoRA",
                "required": False
            }
        ],
        "flux_loras": [
            {
                "display_title": "USO FLUX1 DIT LoRA v1",
                "name": "uso-flux1-dit-lora-v1.safetensors",
                "source_page": "https://huggingface.co/Comfy-Org/USO_1.0_Repackaged",
                "url": "https://huggingface.co/Comfy-Org/USO_1.0_Repackaged/resolve/main/split_files/loras/uso-flux1-dit-lora-v1.safetensors",
                "filename": "uso-flux1-dit-lora-v1.safetensors",
                "dest_dir": "models/loras",
                "info": "USO FLUX1 DIT LoRA model",
                "required": False
            }
        ],
        "pony_loras": [
            {
                "display_title": "PONY Fernando Style",
                "name": "PONY_Fernando_Style.safetensors",
                "source_page": "https://civitai.com/models/452367",
                "url": "https://civitai.com/api/download/models/452367?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "PONY_Fernando_Style.safetensors",
                "dest_dir": "models/loras",
                "info": "Fernando Style for Pony models",
                "required": False
            },
            {
                "display_title": "PONY Majo",
                "name": "PONY_Majo.safetensors",
                "source_page": "https://civitai.com/models/835055",
                "url": "https://civitai.com/api/download/models/835055?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "PONY_Majo.safetensors",
                "dest_dir": "models/loras",
                "info": "Majo style for Pony models",
                "required": False
            },
            {
                "display_title": "PONY Western Comic Art Style",
                "name": "PONY_Western_Comic_Art_Style.safetensors",
                "source_page": "https://civitai.com/models/871611",
                "url": "https://civitai.com/api/download/models/871611?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "PONY_Western_Comic_Art_Style.safetensors",
                "dest_dir": "models/loras",
                "info": "Western Comic Art Style for Pony",
                "required": False
            },
            {
                "display_title": "PONY Incase Unaesthetic Style",
                "name": "PONY_Incase_unaesthetic_style.safetensors",
                "source_page": "https://civitai.com/models/1128016",
                "url": "https://civitai.com/api/download/models/1128016?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "PONY_Incase_unaesthetic_style.safetensors",
                "dest_dir": "models/loras",
                "info": "Incase Unaesthetic Style for Pony",
                "required": False
            },
            {
                "display_title": "Pony LoRA Water Color Anime",
                "name": "Pony_Lora_Water_Color_Anime.safetensors",
                "source_page": "https://civitai.com/models/725772",
                "url": "https://civitai.com/api/download/models/725772?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "Pony_Lora_Water_Color_Anime.safetensors",
                "dest_dir": "models/loras",
                "info": "Water Color Anime style for Pony",
                "required": False
            },
            {
                "display_title": "Pony LoRA Water Color",
                "name": "Pony_Lora_Water_Color.safetensors",
                "source_page": "https://civitai.com/models/720004",
                "url": "https://civitai.com/api/download/models/720004?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "Pony_Lora_Water_Color.safetensors",
                "dest_dir": "models/loras",
                "info": "Water Color style for Pony",
                "required": False
            },
            {
                "display_title": "Pony LoRA Sketch Illustration",
                "name": "Pony_Lora_Sketch_Illustration.safetensors",
                "source_page": "https://civitai.com/models/882225",
                "url": "https://civitai.com/api/download/models/882225?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "Pony_Lora_Sketch_Illustration.safetensors",
                "dest_dir": "models/loras",
                "info": "Sketch Illustration style for Pony",
                "required": False
            },
            {
                "display_title": "Pony Peoples Work",
                "name": "Pony_Peoples_Work.safetensors",
                "source_page": "https://civitai.com/models/1036362",
                "url": "https://civitai.com/api/download/models/1036362?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "Pony_Peoples_Work.safetensors",
                "dest_dir": "models/loras",
                "info": "Peoples Work style for Pony",
                "required": False
            }
        ],
        "illustrious_loras": [
            {
                "display_title": "Illustrious USNR Style",
                "name": "Illustrious_USNR_Style.safetensors",
                "source_page": "https://civitai.com/models/959419",
                "url": "https://civitai.com/api/download/models/959419?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "Illustrious_USNR_Style.safetensors",
                "dest_dir": "models/loras",
                "info": "USNR Style for Illustrious",
                "required": False
            },
            {
                "display_title": "Illustrious Gennesis",
                "name": "Illustrious_Gennesis.safetensors",
                "source_page": "https://civitai.com/models/1219983",
                "url": "https://civitai.com/api/download/models/1219983?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "Illustrious_Gennesis.safetensors",
                "dest_dir": "models/loras",
                "info": "Gennesis style for Illustrious",
                "required": False
            },
            {
                "display_title": "Illustrious LoRAs Hassaku Shiro Styles",
                "name": "Illustrious_Loras_Hassaku_Shiro_Styles.safetensors",
                "source_page": "https://civitai.com/models/1580764",
                "url": "https://civitai.com/api/download/models/1580764?token=fd4ae815a82358dab77c19eb48c9f2cf",
                "filename": "Illustrious_Loras_Hassaku_Shiro_Styles.safetensors",
                "dest_dir": "models/loras",
                "info": "Hassaku Shiro Styles for Illustrious",
                "required": False
            }
        ]
    },

    # CLIP Text Encoders
    "clip_models": [
        {
            "display_title": "CLIP L (FLUX)",
            "name": "clip_l.safetensors",
            "source_page": "https://huggingface.co/comfyanonymous/flux_text_encoders",
            "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors?download=true",
            "filename": "clip_l.safetensors",
            "dest_dir": "models/clip",
            "info": "FLUX CLIP L text encoder",
            "required": False
        },
        {
            "display_title": "T5XXL FP16",
            "name": "t5xxl_fp16.safetensors",
            "source_page": "https://huggingface.co/comfyanonymous/flux_text_encoders",
            "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors?download=true",
            "filename": "t5xxl_fp16.safetensors",
            "dest_dir": "models/clip",
            "info": "T5XXL text encoder in FP16",
            "required": False
        },
        {
            "display_title": "CLIP G",
            "name": "clip_g.safetensors",
            "source_page": "https://huggingface.co/calcuis/sd3.5-large-gguf",
            "url": "https://huggingface.co/calcuis/sd3.5-large-gguf/resolve/7f72f2a432131bba82ecd1aafb931ac99f0f05f7/clip_g.safetensors?download=true",
            "filename": "clip_g.safetensors",
            "dest_dir": "models/clip",
            "info": "Large CLIP G text encoder",
            "required": False
        }
    ],

    # VAE Models
    "vae_models": [
        {
            "display_title": "SDXL VAE",
            "name": "SDXL_Vae.safetensors",
            "source_page": "https://huggingface.co/stabilityai/sdxl-vae",
            "url": "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors?download=true",
            "filename": "SDXL_Vae.safetensors",
            "dest_dir": "models/vae",
            "info": "SDXL VAE model from Stability AI",
            "required": False
        }
    ],

    # CLIP Vision Models
    "clip_vision_models": [
        {
            "display_title": "CLIP ViT-H-14 (IP-Adapter)",
            "name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
            "source_page": "https://huggingface.co/h94/IP-Adapter",
            "url": "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors",
            "filename": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
            "dest_dir": "models/clip_vision",
            "info": "CLIP ViT-H-14 encoder (IP-Adapter repack)",
            "required": False,
            "vram": "~12GB",
            "size": "2.5GB"
        },
        {
            "display_title": "CLIP ViT-bigG-14 (SDXL IP-Adapter)",
            "name": "CLIP-ViT-bigG-14-laion2B-39B-b160k.safetensors",
            "source_page": "https://huggingface.co/h94/IP-Adapter",
            "url": "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/image_encoder/model.safetensors",
            "filename": "CLIP-ViT-bigG-14-laion2B-39B-b160k.safetensors",
            "dest_dir": "models/clip_vision",
            "info": "CLIP ViT bigG encoder for SDXL",
            "required": False,
            "vram": "~16GB",
            "size": "4.2GB"
        },
        {
            "display_title": "OpenAI CLIP ViT-L",
            "name": "model_l.safetensors",
            "source_page": "https://huggingface.co/openai/clip-vit-large-patch14",
            "url": "https://huggingface.co/openai/clip-vit-large-patch14/resolve/main/model.safetensors?download=true",
            "filename": "model_l.safetensors",
            "dest_dir": "models/clip_vision",
            "info": "OpenAI CLIP ViT-L model",
            "required": False,
            "vram": "~6GB",
            "size": "890MB"
        },
        {
            "display_title": "CLIP Vision ViT-H (Alternative)",
            "name": "clip-vision_vit-h.safetensors",
            "source_page": "https://huggingface.co/h94/IP-Adapter",
            "url": "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors",
            "filename": "clip-vision_vit-h.safetensors",
            "dest_dir": "models/clip_vision",
            "info": "Alternate vit-h encoder",
            "required": False,
            "vram": "~12GB",
            "size": "2.5GB"
        },
        {
            "display_title": "ComfyUI CLIP Vision H",
            "name": "clip_vision_h.safetensors",
            "source_page": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged",
            "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors?download=true",
            "filename": "clip_vision_h.safetensors",
            "dest_dir": "models/clip_vision",
            "info": "Comfy repackaged clip_vision_h",
            "required": False,
            "vram": "~12GB",
            "size": "2.5GB"
        },
        {
            "display_title": "SigCLIP Vision 384",
            "name": "sigclip_vision_patch14_384.safetensors",
            "source_page": "https://huggingface.co/Comfy-Org/sigclip_vision_384",
            "url": "https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors?download=true",
            "filename": "sigclip_vision_patch14_384.safetensors",
            "dest_dir": "models/clip_vision",
            "info": "SigCLIP vision model",
            "required": False,
            "vram": "~8GB",
            "size": "1.6GB"
        }
    ],

    # Upscale Models
    "upscale_models": [
        {
            "display_title": "4x Foolhardy Remacri",
            "name": "4x_foolhardy_Remacri.pth",
            "source_page": "https://huggingface.co/FacehugmanIII/4x_foolhardy_Remacri",
            "url": "https://huggingface.co/FacehugmanIII/4x_foolhardy_Remacri/resolve/main/4x_foolhardy_Remacri.pth?download=true",
            "filename": "4x_foolhardy_Remacri.pth",
            "dest_dir": "models/upscale_models",
            "info": "4x upscaling model for realistic images",
            "required": False
        },
        {
            "display_title": "Real-ESRGAN 4x Plus",
            "name": "RealESRGAN_x4plus.pth",
            "source_page": "https://github.com/xinntao/Real-ESRGAN/releases",
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            "filename": "RealESRGAN_x4plus.pth",
            "dest_dir": "models/upscale_models",
            "info": "4x upscaling for photorealistic images",
            "required": False
        },
        {
            "display_title": "4x NMKD Siax 200k",
            "name": "4x_NMKD_Siax_200k.pth",
            "source_page": "https://huggingface.co/uwg/upscaler",
            "url": "https://huggingface.co/uwg/upscaler/resolve/main/ESRGAN/4x_NMKD-Siax_200k.pth?download=true",
            "filename": "4x_NMKD_Siax_200k.pth",
            "dest_dir": "models/upscale_models",
            "info": "4x upscaling model trained on 200k images",
            "required": False
        },
        {
            "display_title": "Real-ESRGAN Anime 6B",
            "name": "RealESRGAN_x4plus_anime_and_illustrations_6B.pth",
            "source_page": "https://github.com/xinntao/Real-ESRGAN/releases",
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
            "filename": "RealESRGAN_x4plus_anime_and_illustrations_6B.pth",
            "dest_dir": "models/upscale_models",
            "info": "4x upscaling optimized for anime images",
            "required": False
        },
        {
            "display_title": "4x UltraSharp",
            "name": "4x-UltraSharp.safetensors",
            "source_page": "https://civitai.com/models/125843",
            "url": "https://civitai.com/api/download/models/125843?token=fd4ae815a82358dab77c19eb48c9f2cf",
            "filename": "4x-UltraSharp.safetensors",
            "dest_dir": "models/upscale_models",
            "info": "Ultra-sharp 4x upscaling model",
            "required": False
        },
        {
            "display_title": "4x NMKD Superscale SP 178000 G",
            "name": "4x_NMKD-Superscale-SP_178000_G.pth",
            "source_page": "https://huggingface.co/gemasai/4x_NMKD-Superscale-SP_178000_G",
            "url": "https://huggingface.co/gemasai/4x_NMKD-Superscale-SP_178000_G/resolve/main/4x_NMKD-Superscale-SP_178000_G.pth",
            "filename": "4x_NMKD-Superscale-SP_178000_G.pth",
            "dest_dir": "models/upscale_models",
            "info": "High-quality 4x upscaling model",
            "required": False
        },
        {
            "display_title": "OmniSR X2 DIV2K",
            "name": "OmniSR_X2_DIV2K.safetensors",
            "source_page": "https://huggingface.co/Acly/Omni-SR",
            "url": "https://huggingface.co/Acly/Omni-SR/resolve/main/OmniSR_X2_DIV2K.safetensors",
            "filename": "OmniSR_X2_DIV2K.safetensors",
            "dest_dir": "models/upscale_models",
            "info": "2x upscaling with OmniSR architecture",
            "required": False
        },
        {
            "display_title": "OmniSR X3 DIV2K",
            "name": "OmniSR_X3_DIV2K.safetensors",
            "source_page": "https://huggingface.co/Acly/Omni-SR",
            "url": "https://huggingface.co/Acly/Omni-SR/resolve/main/OmniSR_X3_DIV2K.safetensors",
            "filename": "OmniSR_X3_DIV2K.safetensors",
            "dest_dir": "models/upscale_models",
            "info": "3x upscaling with OmniSR architecture",
            "required": False
        },
        {
            "display_title": "OmniSR X4 DIV2K",
            "name": "OmniSR_X4_DIV2K.safetensors",
            "source_page": "https://huggingface.co/Acly/Omni-SR",
            "url": "https://huggingface.co/Acly/Omni-SR/resolve/main/OmniSR_X4_DIV2K.safetensors",
            "filename": "OmniSR_X4_DIV2K.safetensors",
            "dest_dir": "models/upscale_models",
            "info": "4x upscaling with OmniSR architecture",
            "required": False
        }
    ],

    # Diffusion Models (for Flux Fill)
    "diffusion_models": [
        {
            "display_title": "Flux Fill",
            "name": "Flux_Fill.safetensors",
            "source_page": "https://civitai.com/models/1086292",
            "url": "https://civitai.com/api/download/models/1086292?token=fd4ae815a82358dab77c19eb48c9f2cf",
            "filename": "Flux_Fill.safetensors",
            "dest_dir": "models/diffusion_models",
            "info": "FLUX Fill model for inpainting",
    "required": False
        }
    ]
}