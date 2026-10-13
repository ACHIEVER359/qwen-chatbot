# Qwen Chat — Standalone AI Chatbot

A standalone web application based on the notebook's `Qwen/Qwen2.5-0.5B-Instruct` model. It uses FastAPI for the backend, Transformers/PyTorch for local model inference, and a responsive HTML/CSS/JavaScript frontend. No Gradio or notebook runtime is required.

## Features

- Responsive, polished chat interface
- Suggested starter prompts
- Multi-turn conversation context
- Public Qwen model downloaded automatically from Hugging Face
- No Hugging Face token normally required
- Model runs on the server; the browser never receives model weights or server files
- Health endpoint and deployment configuration
- No API key required for the default public model

## Important deployment note

This is **server-side local inference**, not a hosted inference API. The host must have enough RAM to load PyTorch and the model. The model is small compared with many LLMs, but CPU-only hosting can be slow and memory-limited. Free web-service plans may not have enough memory or may sleep when idle. Test the selected host's current RAM and disk limits before deploying.

## Run locally

Python 3.10 or 3.11 is recommended.

### 1. Create a virtual environment

**Windows PowerShell**
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PyTorch installation can vary by operating system and hardware. If the `torch` install fails, use the official PyTorch installation selector for your platform: https://pytorch.org/get-started/locally/

### 3. Start the application

```bash
uvicorn app:app --reload
```

Open http://127.0.0.1:8000. The first chat request downloads the model weights, which may take a few minutes and several hundred MB. Keep enough RAM and disk space available.

## Push to a public GitHub repository

1. Create an empty repository: https://github.com/new
2. Extract this ZIP into a folder.
3. From that folder, run:

```bash
git init
git add .
git commit -m "Build standalone Qwen chatbot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the URL with your repository URL. `.gitignore` excludes `.env`, virtual environments, and Python caches.

## Deployment options

### Docker-capable hosting

The included `Dockerfile` starts the app on port 7860. Deploy it on a host that supports Docker and provides enough RAM for PyTorch plus the model. Set the health check path to `/api/health` if your host supports health checks.

### Render

The included `render.yaml` describes a Render web service. Connect the public GitHub repository to Render and deploy. Check the plan's memory, disk, build-time, and sleep limits before choosing it; model loading can exceed very small free instances. If the service repeatedly restarts or fails while loading weights, use a larger instance or host inference separately.

### Hugging Face Spaces

A Docker Space can host this app. Create a Space using the Docker SDK, upload the project files, and set its exposed port to 7860 if requested. Check the current Space hardware limits. The model is public and normally does not need a Hugging Face token.

## API

- `GET /api/health` — application status and whether the model is loaded
- `POST /api/chat` — JSON body:
  ```json
  {
    "message": "Explain Python functions simply.",
    "history": []
  }
  ```

The response shape is `{"reply": "..."}`.

## Limitations

- Qwen2.5-0.5B-Instruct is a small model; answers may be inaccurate, shallow, or repetitive.
- This starter app keeps conversation history in the browser tab, not in a user account or database.
- The server serializes model generation requests to avoid concurrent calls into one model instance.
- Public hosting can be abused for compute consumption. Add rate limiting, authentication, and usage controls before promoting the site widely.
- The default backend is CPU-oriented; CUDA may require a separate PyTorch installation and configuration for GPU inference.

## License

This starter project is provided under the MIT License.
