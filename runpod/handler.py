import os
import sys
import base64
import struct
import runpod

sys.path.insert(0, "/app")

from orpheus_tts import OrpheusModel

MODEL_NAME = os.environ.get("MODEL_NAME", "canopylabs/orpheus-tts-0.1-finetune-prod")

print(f"Loading model: {MODEL_NAME}")
model = OrpheusModel(model_name=MODEL_NAME)
print("Model loaded.")


def _wav_header(sample_rate: int = 24000, bits_per_sample: int = 16, channels: int = 1) -> bytes:
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36,
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        0,
    )


def handler(job):
    job_input = job.get("input", {})

    prompt = job_input.get("prompt", "")
    if not prompt:
        return {"error": "Missing required field: prompt"}

    voice = job_input.get("voice", "tara")
    temperature = float(job_input.get("temperature", 0.4))
    top_p = float(job_input.get("top_p", 0.9))
    max_tokens = int(job_input.get("max_tokens", 2000))
    repetition_penalty = float(job_input.get("repetition_penalty", 1.1))

    chunks = [_wav_header()]
    for chunk in model.generate_speech(
        prompt=prompt,
        voice=voice,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        repetition_penalty=repetition_penalty,
        stop_token_ids=[128258],
    ):
        chunks.append(chunk)

    audio_bytes = b"".join(chunks)

    # Fix WAV data-chunk size in header (bytes 40–44)
    data_size = len(audio_bytes) - 44
    audio_bytes = (
        audio_bytes[:4]
        + struct.pack("<I", 36 + data_size)
        + audio_bytes[8:40]
        + struct.pack("<I", data_size)
        + audio_bytes[44:]
    )

    return {
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        "sample_rate": 24000,
        "encoding": "pcm_s16le",
        "channels": 1,
    }


runpod.serverless.start({"handler": handler})
