import os
import threading
from typing import Any

import torch
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()

APP_NAME = "Qwen Chat"
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "4000"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

app = FastAPI(title=APP_NAME, version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

tokenizer = None
model = None
model_lock = threading.Lock()


class ChatMessage(BaseModel):
    role: str
    content: str = Field(max_length=MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    history: list[ChatMessage] = Field(default_factory=list)


def load_model():
    global tokenizer, model
    if model is not None and tokenizer is not None:
        return tokenizer, model

    with model_lock:
        if model is not None and tokenizer is not None:
            return tokenizer, model
        try:
            loaded_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            loaded_model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype="auto",
                low_cpu_mem_usage=True,
            )
            loaded_model.eval()
            tokenizer, model = loaded_tokenizer, loaded_model
        except Exception as exc:
            raise RuntimeError(
                f"Could not load {MODEL_NAME}. Check internet access, available RAM, and MODEL_NAME. Details: {exc}"
            ) from exc
    return tokenizer, model


def generate_reply(message: str, history: list[ChatMessage]) -> str:
    tok, llm = load_model()
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": "You are a helpful, friendly AI assistant. Answer clearly and honestly. If you are unsure, say so."
        }
    ]

    # Keep only recent, valid user/assistant turns to limit prompt growth.
    for item in history[-MAX_HISTORY_MESSAGES:]:
        if item.role in ("user", "assistant") and item.content.strip():
            messages.append({"role": item.role, "content": item.content.strip()})

    messages.append({"role": "user", "content": message.strip()})
    prompt = tok.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tok(prompt, return_tensors="pt")
    input_length = inputs["input_ids"].shape[-1]

    with model_lock, torch.inference_mode():
        output = llm.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tok.eos_token_id,
        )

    answer = tok.decode(output[0][input_length:], skip_special_tokens=True).strip()
    return answer or "I couldn't generate a response. Please try again."


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "model": MODEL_NAME,
        "model_loaded": model is not None,
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please enter a message.")
    if len(message) > MAX_MESSAGE_CHARS:
        raise HTTPException(status_code=413, detail=f"Messages must be {MAX_MESSAGE_CHARS} characters or fewer.")
    try:
        answer = generate_reply(message, request.history)
        return {"reply": answer}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc
