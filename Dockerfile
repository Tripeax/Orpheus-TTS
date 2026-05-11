# syntax=docker/dockerfile:1
FROM vllm/vllm-openai:v0.8.5

WORKDIR /app

# Install SNAC decoder and RunPod SDK
RUN pip install --no-cache-dir \
    snac \
    runpod>=1.7.0

# Copy the orpheus_tts package and handler
COPY orpheus_tts_pypi/orpheus_tts ./orpheus_tts
COPY runpod/handler.py ./handler.py

# HuggingFace cache — override at runtime to point at a RunPod network volume
# e.g. docker run -e HF_HOME=/runpod-volume/hf-cache ...
ENV HF_HOME=/app/hf-cache
ENV TRANSFORMERS_CACHE=/app/hf-cache

# Pre-download the SNAC decoder model so it is baked into the image
RUN python3 -c "\
from snac import SNAC; \
SNAC.from_pretrained('hubertsiuzdak/snac_24khz'); \
print('SNAC model cached.')"

# Pre-download the Orpheus LLM weights (large — ~6 GB).
# Comment this out and mount a network volume instead if you want a smaller image.
ARG PRELOAD_MODEL=true
RUN if [ "$PRELOAD_MODEL" = "true" ]; then \
      python3 -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('canopylabs/orpheus-tts-0.1-finetune-prod'); \
print('Orpheus model cached.')"; \
    fi

CMD ["python3", "-u", "handler.py"]
