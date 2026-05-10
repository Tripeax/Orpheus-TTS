# RunPod Serverless Deployment

## Quick start

### 1. Build and push the Docker image

```bash
# From the repo root
docker build -t your-dockerhub-username/orpheus-tts:latest .
docker push your-dockerhub-username/orpheus-tts:latest
```

**Smaller image (skip baking the LLM weights — use a network volume instead):**
```bash
docker build --build-arg PRELOAD_MODEL=false \
  -t your-dockerhub-username/orpheus-tts:slim .
```

### 2. Create a RunPod serverless endpoint

1. Go to **RunPod → Serverless → New Endpoint**
2. Select **Custom** container source
3. Container image: `your-dockerhub-username/orpheus-tts:latest`
4. GPU: **24 GB VRAM minimum** (RTX 3090 / A5000 / L4 or better)
5. Container disk: **20 GB** (or 5 GB if using the slim image + network volume)

**If using slim image + network volume:**
- Attach a network volume mounted at `/runpod-volume`
- Set env var: `HF_HOME=/runpod-volume/hf-cache`
- The first cold start will download ~6 GB of model weights to the volume;
  subsequent starts reuse the cache.

### 3. Call the endpoint

```bash
curl -X POST https://api.runpod.io/v2/<ENDPOINT_ID>/runsync \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "Hello, world!",
      "voice": "tara"
    }
  }'
```

The response contains a base64-encoded WAV file:
```json
{
  "output": {
    "audio_base64": "<base64 WAV>",
    "sample_rate": 24000,
    "encoding": "pcm_s16le",
    "channels": 1
  }
}
```

Decode it:
```python
import base64, json

data = json.loads(response.text)
audio = base64.b64decode(data["output"]["audio_base64"])
with open("output.wav", "wb") as f:
    f.write(audio)
```

### Input fields

| Field | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | **required** | Text to synthesize |
| `voice` | string | `"tara"` | Speaker voice. Options: `tara`, `zoe`, `zac`, `jess`, `leo`, `mia`, `julia`, `leah` |
| `temperature` | float | `0.4` | Sampling temperature |
| `top_p` | float | `0.9` | Top-p sampling |
| `max_tokens` | int | `2000` | Max output tokens |
| `repetition_penalty` | float | `1.1` | Repetition penalty |

### Local test (without RunPod)

```bash
pip install runpod vllm snac transformers
cd /path/to/Orpheus-TTS
PYTHONPATH=orpheus_tts_pypi python runpod/handler.py \
  --rp_serve_api   # starts a local HTTP server on port 8000
```

Then POST to `http://localhost:8000/runsync` with the body from `test_input.json`.
