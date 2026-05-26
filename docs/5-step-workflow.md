# 5-Step Workflow

The active CLI and Web pipeline now runs five steps:

1. Script brief: generates `script_brief.json` with `theme`, `summary`, `style`, and `body`.
2. Storyboard: generates `storyboard.json` and `script.md`; `storyboard.json` contains shots plus character, scene, and prop image prompts.
3. Asset generation: generates character, scene, and prop images from storyboard prompts and writes `img_results.json`.
4. Video generation: generates `video_prompts.json`, preserves `manual_reference_image_paths`, and calls Seedance 2.0 for per-shot clips.
5. Concat: combines generated clips into `final.mp4`.

System prompts are configured through `prompts/pipeline_prompts.json`. You can replace the whole registry with `MANGA_PIPELINE_PROMPTS_CONFIG`, or override individual prompt files:

- `STEP01_SCRIPT_SYSTEM_PROMPT_FILE`
- `STEP02_STORYBOARD_SYSTEM_PROMPT_FILE`
- `STEP02_ASSET_CATALOG_SYSTEM_PROMPT_FILE`
- `STEP02_ASSET_IMAGE_SYSTEM_PROMPT_FILE`
- `STEP04_VIDEO_SYSTEM_PROMPT_FILE`

Legacy step modules remain in the repository as compatibility helpers, but `pipeline.py` and `server/pipeline_runner.py` now execute the five-step workflow.
