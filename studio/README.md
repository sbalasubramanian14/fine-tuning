# Local Model Studio

A local web UI for this repository's image experiments. It uses the existing
Python environment and GPU dependencies; no additional web framework is required.

From the repository root in PowerShell:

```powershell
.\studio\start.ps1
```

Open **http://127.0.0.1:7860** in your browser. Keep that terminal running;
Ctrl+C stops the server. Use `-Port 7861` if 7860 is occupied.
The server binds to loopback and is intended for use on this computer.

## Test the models

1. Select **DreamShaper 8** or **Waifu Diffusion 1.3**.
2. Uncheck **Use LoRA adapter** for the original base model. Check it and select
   a checkpoint for the trained character. Start with Final, strength **0.8**.
3. Enter an image prompt and click **Generate image**. **Compare base + LoRA**
   generates both with the same prompt, seed, scheduler and settings.
4. Expand **Generation settings** to change the negative prompt, seed, steps,
   guidance, size or LoRA strength. A fixed seed makes comparisons reproducible.
5. **Browse saved tests** reopens previous results. Download images or their
   **Settings JSON** to keep the precise prompt and model/adapter hashes.

Example:

```text
soraskychar, solo, 1girl, adult woman, short teal hair, amber eyes,
cream jacket, red scarf, dark trousers, brown boots, brown satchel,
standing beside a wooden bridge at sunset, anime illustration
```

The image models accept prompts; they do not hold a text conversation. The
`soraskychar` trigger activates the trained identity. Clothing, hands and actions
can still vary; see [the experiment report](../docs/dreamshaper8-results.md).
Only adapters registered for the selected model are offered. Changing models
resets settings and the example prompt. Original model files are read without
modification. Each generation runs in its own process so GPU memory is released
between tests; one job runs at a time.

Results and request history live in `studio/artifacts/jobs/` and stay out of Git.
This includes every browser prompt, settings file, generated image, job log and
saved test. Both the root and Studio ignore rules exclude the entire runtime
folder. Browser jobs are never automatically exported into versioned experiment
results. Only the app code and documentation are published; publishing an
individual browser result requires a separate, explicit action.
Downloaded base models and the Python environment also stay local. A fresh clone
needs the environment setup and model downloads described in the root README.

## Extend the workspace

Working now: SD1.x image generation using local Diffusers model folders and
sd-scripts LoRAs. DreamShaper and the preserved Waifu experiment are discovered
from `experiments/image/*/profile.json`.

To support another architecture or modality:

- Add a catalog provider to `catalog.PROVIDERS`. It supplies available models,
  compatible adapters, example prompts and validated setting fields.
- Register an inference function in `worker.BACKENDS`. It receives a normalized
  request, output directory and progress callback. Return an `outputs` list;
  each item has `kind`, `label`, and a local `file` (image/audio/video) or `text`.
  Media paths must name files in the job directory.
- Implement that model's loader, adapter handling and memory strategy. Use a
  separate environment/worker launcher if dependencies conflict.
- For conversational text models, add conversation history, a message input
  contract and chat backend. The current prompt interface has no chat memory.

The UI already renders image, text, audio and video results. Actual text, voice
and video inference/training backends are **not installed or implemented yet**.
SDXL, Flux and video models need their own training backend; this SD1.x trainer
does not fine-tune arbitrary architectures. Compatible, captioned image sets can
be used after configuring a new isolated profile and dataset.

## Existing apps

- **ComfyUI** is the strongest existing option for image workflows and later
  supported video/audio models. Its [official LoRA tutorial](https://docs.comfy.org/tutorials/basic/lora)
  uses DreamShaper 8. Put a compatible **single checkpoint** in
  `ComfyUI/models/checkpoints/` and the exported LoRA in `ComfyUI/models/loras/`.
  Our downloaded base is a **Diffusers component directory**, so obtain or convert
  the full checkpoint; the U-Net file alone is not a complete model. For this
  UNet-only LoRA, use `strength_model=0.8`, `strength_clip=0`; bypass Load LoRA for
  the base comparison. See the [local model hub](https://comfy.org/hub/models/local/)
  for supported image, video and audio workflows. GPU requirements vary.
- **LM Studio** provides [local text-model chat](https://lmstudio.ai/docs/app/basics/chat).
  It would need a separately downloaded compatible language model; these image
  models and image LoRAs are not text chat models.
- **Open WebUI** can provide a chat interface with
  [image generation through ComfyUI](https://docs.openwebui.com/features/chat-conversations/image-generation-and-editing/comfyui/).
  That adds another service and its own setup; the linked integration guide is
  community maintained.

## Verification

```powershell
. .\scripts\common.ps1
& $PythonExe studio/test_catalog.py
& $PythonExe studio/test_local_storage.py
```

Initial validation also ran real GPU comparisons for both models, standalone
base/LoRA generation, model switching, saved history and API boundaries. Both
comparison pairs matched the existing experiment PNGs byte for byte, and single
generation outputs matched their comparison counterparts. Browser checks cover
the actual comparison button, disabled controls during work, model/LoRA toggles,
history and desktop/mobile layouts.
