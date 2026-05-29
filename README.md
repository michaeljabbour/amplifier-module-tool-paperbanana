# PaperBanana Tool - AI-Generated Academic Figures

Publication-ready academic illustrations using Google's Imagen 4 image generation model.

Based on research from [arXiv:2601.23265](https://arxiv.org/abs/2601.23265) - "PaperBanana: Automating Academic Illustration for AI Scientists"

## What It Does

Generates professional methodology diagrams and architecture figures for academic papers using AI image generation (not matplotlib boxes).

**Input:** Paper abstract + methods text  
**Output:** High-resolution PNG diagram (1024x1024)

## Usage via Bundle

```bash
# The scientificpaper bundle includes this tool
amplifier run --bundle scientificpaper "Generate a methodology diagram about transformer attention mechanisms"
```

## Requirements

**API Key:** You need a Google API key with Imagen access:

```bash
export GOOGLE_API_KEY="your-google-api-key-here"
```

Get a key at: https://aistudio.google.com/apikey

**Dependencies:** Auto-installed when bundle is used (no manual setup required)

## How It Works

1. **Retriever Agent** - Extracts key concepts from paper text
2. **Planner Agent** - Plans diagram content and structure  
3. **Visualizer** - Calls Imagen 4 API with detailed prompt
4. **Critic Agent** - Validates against 8 quality veto rules
5. **Iterative Refinement** - Up to 3 refinement cycles

## Architecture Pattern

This is an **Amplifier tool** (not a provider integration). It:
- Calls Google Imagen API directly
- Returns generated figure paths
- Integrates with the 5-agent PaperBanana workflow

Tools call external APIs directly - this is the standard Amplifier pattern for capabilities like image generation, web search, etc.

## Quality Veto Rules

Enforces 8 publication standards:
1. No low-quality artifacts
2. Professional colors (ColorBrewer palettes)
3. No black backgrounds
4. Modern typography
5. Vector format preferred
6. Appropriate aspect ratios
7. Clear labels
8. Data integrity

## Alternative

For multi-provider support (DALL-E, Imagen, GPT-Image), consider:
- [robotdad/amplifier-module-image-generation](https://github.com/robotdad/amplifier-module-image-generation)

## Implementation Details

- **Model:** `imagen-4.0-generate-001` (Google's latest)
- **Output:** 1024x1024 PNG (4:3 for methodology diagrams)
- **Safety:** BLOCK_ONLY_HIGH filter level
- **Cost:** ~$0.04 per image (Imagen 4 pricing)

## Development

```bash
cd modules/tool-paperbanana
pip install -e ".[dev]"
pytest
pyright
ruff check .
```

## License

MIT License - Part of the Amplifier Scientific Paper Bundle
