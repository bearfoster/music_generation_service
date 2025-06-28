# Music Generation Service

This service is a core component of the "Weather to Mood to Music" agentic AI system. Its primary responsibility is to translate a standardized "mood" into a generated music composition.

**NOTE:** In this current implementation, the music generation is simulated. It does not interact with a real third-party music generation API (like Beatoven.ai) but instead provides mock URLs after a simulated processing time. This allows the overall system workflow to be tested without external API dependencies or costs.

---

## Features

- **Mood to Music Translation:** Accepts a standardized mood and desired duration as input.
- **Asynchronous Simulation:** Simulates the asynchronous nature of real music generation APIs by initiating a task and allowing for status polling.
- **Standardized Output:** Provides a `task_id` for tracking and, upon completion, a mock `music_url`.
- **MCP Server:** Exposes its capabilities via the Model Context Protocol, making its `initiate_music_generation` and `get_music_generation_status` tools discoverable and invocable by other services (e.g., the Orchestration Layer).
- **FastAPI Backend:** Built on FastAPI, offering robust and asynchronous API handling.

---

## API Endpoints (MCP Tools)

The service exposes its functionality as HTTP endpoints that are automatically wrapped and described as MCP tools:

### 1. `POST /initiate_music_generation/`

**Description:** Initiates music generation based on a given mood and duration (in seconds). Returns a task ID for status tracking.

**Input Schema (`InitiateMusicGenerationInput`):**
```json
{
  "mood": "joyful",
  "duration_seconds": 90
}
```
- `mood` (string): One of the predefined moods (consistent with the Mood Analysis Service's output).
- `duration_seconds` (integer): Desired duration of the music in seconds (10-300).

**Output Schema (`InitiateMusicGenerationOutput`):**
```json
{
  "status": "generation_initiated",
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

---

### 2. `POST /get_music_generation_status/`

**Description:** Retrieves the current status and (if completed) the download URL of a music generation task.

**Input Schema (`GetMusicGenerationStatusInput`):**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

**Output Schema (`GetMusicGenerationStatusOutput`):**
```json
{
  "status": "completed" | "processing" | "failed",
  "music_url": "https://mock-music-cdn.com/generated_music/task_id_mood.mp3",
  "error": null
}
```
> **Note:** `music_url` will be null if status is "processing" or "failed". `error` will be null if status is "completed" or "processing".

---

## Setup and Installation

### Prerequisites

- Python 3.12 (recommended)
- pip (Python package installer)
- Git Bash (or another terminal where `source` command works on Windows)

### Steps

#### 1. Clone the Repository or Navigate to the Service Directory

```sh
cd path/to/your/project/music_generation_service
```

#### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

```sh
python -m venv venv_music_gen
```

#### 3. Activate the Virtual Environment

- **Git Bash:**
  ```sh
  source venv_music_gen/Scripts/activate
  ```
- **Command Prompt:**
  ```sh
  venv_music_gen\Scripts\activate
  ```
- **PowerShell:**
  ```sh
  .\venv_music_gen\Scripts\Activate.ps1
  ```

You should see `(venv_music_gen)` at the start of your terminal prompt.

#### 4. Install Dependencies

Ensure you have the `requirements.txt` file in your `music_generation_service` directory. Then, with your virtual environment activated:

```sh
pip install -r requirements.txt
```

---

## Running the Service

With the virtual environment activated, run the FastAPI application using Uvicorn:

```sh
uvicorn main:app --reload --port 8002
```

The service will start and be accessible at [http://127.0.0.1:8002](http://127.0.0.1:8002). The `--reload` flag ensures that the server automatically reloads if you make changes to the code.

---

## Testing the Service (Directly)

You can test the endpoints directly using `curl` or a tool like Postman/Insomnia.

### Initiate Music Generation

```sh
curl -X POST "http://127.0.0.1:8002/initiate_music_generation/" \
     -H "Content-Type: application/json" \
     -d '{
           "mood": "calm",
           "duration_seconds": 60
         }'
```

**Expected Output (example):**
```json
{
  "status": "generation_initiated",
  "task_id": "d1e2f3g4-h5i6-7890-abcd-ef1234567890"
}
```
(Copy the `task_id` for the next step.)

### Get Music Generation Status

```sh
curl -X POST "http://127.0.0.1:8002/get_music_generation_status/" \
     -H "Content-Type: application/json" \
     -d '{
           "task_id": "d1e2f3g4-h5i6-7890-abcd-ef1234567890"
         }'
```

**Expected Output (initially):**
```json
{
  "status": "processing",
  "music_url": null,
  "error": null
}
```

**Expected Output (after a few seconds):**
```json
{
  "status": "completed",
  "music_url": "https://mock-music-cdn.com/generated_music/d1e2f3g4-h5i6-7890-abcd-ef1234567890_calm.mp3",
  "error": null
}
```

---

You can also discover the MCP tools exposed by this service:

```sh