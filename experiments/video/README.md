# Video experiments

Reserved for video-generation profiles. A backend must validate clip duration, FPS, resolution, frame counts, captions, and subject-disjoint evaluation splits; record the temporal model, VAE, scheduler and cache identities. Image LoRA training alone does not train motion. Start with baseline inference and a memory smoke test before choosing a local video training recipe; the current 6 GB GPU is not yet validated for video training.
