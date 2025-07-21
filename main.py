# music_generation_service/main.py

from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import time
import asyncio
import aiohttp
# Removed: import aiofiles # Not directly used for URL return in this version
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional, Callable, Type
import json # ADDED: For pretty-printing JSON bodies

# Initialize the FastAPI application
app = FastAPI(
    title="Music Generation Service",
    description="Agent for translating a given mood into a generated music composition using Beatoven.ai.",
    version="0.3.4" # Updated version
)

# In-memory store to track Beatoven.ai task statuses and results.
# This will now store Beatoven's task_id and status, along with our internal task_id
mock_beatoven_tasks: Dict[str, Dict[str, Any]] = {}

# --- Beatoven.ai Configuration ---
BACKEND_V1_API_URL = "https://public-api.beatoven.ai/api/v1"
# It's best practice to get the API key from environment variables.
# The user provided it directly in the prompt, so we'll use that as a fallback.
BEATOVEN_API_KEY = os.getenv("BEATOVEN_API_KEY", "PW9-2-rgHde49gg03xlErA")

# --- Tool Registry Pattern ---
TOOLS = {}

def register_tool(name: str, input_model: Type[BaseModel], output_model: Type[BaseModel], description: str):
    def decorator(func: Callable):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "input_schema": input_model.schema(),
            "output_schema": output_model.schema()
        }
        return func
    return decorator

@app.get("/tools")
def list_tools():
    """
    Returns a list of available tools and their schemas.
    """
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["input_schema"],
            "output_schema": tool["output_schema"]
        }
        for tool in TOOLS.values()
    ]

# --- Pydantic Models for Tool Schemas ---

class InitiateMusicGenerationInput(BaseModel):
    mood: Literal[
        "joyful", "calm", "melancholy", "energetic", "relaxing", "gloomy", "serene", "adventurous", "upbeat",
        "contemplative", "exhilarated", "peaceful", "frantic", "optimistic", "pensive", "giddy", "tranquil",
        "reflective", "vibrant", "somber", "eager", "content", "restless", "hopeful", "wistful", "euphoric",
        "composed", "agitated", "blissful", "apprehensive", "inspired", "nostalgic", "curious", "playful",
        "solemn", "determined", "bewildered", "grateful", "weary", "proud", "anxious", "elated", "tender",
        "disturbed", "thoughtful", "excited", "sullen", "reverent", "dreamy", "alert"
    ] = Field(..., description="The mood for which to generate music.")
    duration_seconds: int = Field(..., ge=10, le=300, description="Desired duration of the music in seconds (10-300).")

class InitiateMusicGenerationOutput(BaseModel):
    status: Literal["generation_initiated"] = "generation_initiated"
    task_id: str = Field(..., description="Unique ID for the initiated music generation task.")

class GetMusicGenerationStatusInput(BaseModel):
    task_id: str = Field(..., description="The ID of the music generation task to check.")

class GetMusicGenerationStatusOutput(BaseModel):
    status: Literal["completed", "processing", "failed"] = Field(..., description="Current status of the music generation task.")
    music_url: Optional[str] = Field(None, description="URL of the generated music, if completed.")
    error: Optional[str] = Field(None, description="Error message, if the task failed.")

# --- Beatoven.ai API Interaction Functions (adapted from user's example) ---

async def compose_track(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends a request to Beatoven.ai to start music composition.
    Includes print statements for the full request.
    """
    async with aiohttp.ClientSession() as session:
        compose_url = f"{BACKEND_V1_API_URL}/tracks/compose"
        headers = {"Authorization": f"Bearer {BEATOVEN_API_KEY}", "Content-Type": "application/json"}
        
        print("\n--- Beatoven.ai Compose Request ---")
        print(f"URL: {compose_url}")
        print(f"Method: POST")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Body: {json.dumps(request_data, indent=2)}")
        print("-----------------------------------\n")

        try:
            async with session.post(
                compose_url,
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60.0)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                if not data.get("task_id"):
                    raise Exception({"error": "Beatoven.ai did not return a task_id.", "details": data})
                return data
        except aiohttp.ClientConnectionError as exc:
            raise Exception({"error": f"Could not connect to beatoven.ai: {exc}"}) from exc
        except aiohttp.ClientResponseError as exc:
            status_code = exc.status
            error_details = "No response text available."
            if exc.response:
                try:
                    error_details = await exc.response.text()
                except Exception:
                    pass
            raise Exception({"error": f"Beatoven.ai API error {status_code}: {error_details}"}) from exc
        except Exception as exc:
            raise Exception({"error": f"Failed to make a request to beatoven.ai: {exc}"}) from exc


async def get_track_status(beatoven_task_id: str) -> Dict[str, Any]:
    """
    Retrieves the status of a Beatoven.ai music generation task.
    Includes print statements for the full request.
    """
    async with aiohttp.ClientSession() as session:
        status_url = f"{BACKEND_V1_API_URL}/tasks/{beatoven_task_id}"
        headers = {"Authorization": f"Bearer {BEATOVEN_API_KEY}"}

        print("\n--- Beatoven.ai Status Request ---")
        print(f"URL: {status_url}")
        print(f"Method: GET")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print("----------------------------------\n")

        try:
            async with session.get(
                status_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30.0)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientConnectionError as exc:
            raise Exception({"error": f"Could not connect to beatoven.ai for status check: {exc}"}) from exc
        except aiohttp.ClientResponseError as exc:
            status_code = exc.status
            error_details = "No response text available."
            if exc.response:
                try:
                    error_details = await exc.response.text()
                except Exception:
                    pass
            raise Exception({"error": f"Beatoven.ai status API error {status_code}: {error_details}"}) from exc
        except Exception as exc:
            raise Exception({"error": f"Failed to get track status from beatoven.ai: {exc}"}) from exc


async def watch_beatoven_task_status(internal_task_id: str, beatoven_task_id: str, interval=5):
    """
    Polls Beatoven.ai for task status and updates our internal store.
    """
    max_retries = 60 # Max 5 minutes (60 * 5 seconds)
    for i in range(max_retries):
        try:
            track_status = await get_track_status(beatoven_task_id)
            print(f"Beatoven.ai Task status for {beatoven_task_id}: {track_status}")

            current_beatoven_status = track_status.get("status")
            
            if current_beatoven_status == "composing":
                mock_beatoven_tasks[internal_task_id]["status"] = "processing"
                await asyncio.sleep(interval)
            elif current_beatoven_status in ["completed", "composed"]: # CHANGED: Added "composed" status
                track_url = track_status.get("meta", {}).get("track_url")
                if track_url:
                    mock_beatoven_tasks[internal_task_id]["status"] = "completed"
                    mock_beatoven_tasks[internal_task_id]["music_url"] = track_url
                    print(f"Music generation completed for internal task_id: {internal_task_id}. URL: {track_url}")
                    return # Exit polling
                else:
                    error_msg = "Beatoven.ai reported completed/composed but no track_url found." # CHANGED: Updated message
                    mock_beatoven_tasks[internal_task_id]["status"] = "failed"
                    mock_beatoven_tasks[internal_task_id]["error"] = error_msg
                    print(error_msg)
                    return # Exit polling
            elif current_beatoven_status == "failed":
                error_msg = track_status.get("error_message", "Beatoven.ai task failed.")
                mock_beatoven_tasks[internal_task_id]["status"] = "failed"
                mock_beatoven_tasks[internal_task_id]["error"] = error_msg
                print(f"Beatoven.ai task failed for {internal_task_id}: {error_msg}")
                return # Exit polling
            else:
                # Handle other potential statuses if Beatoven.ai has them
                print(f"Beatoven.ai task {beatoven_task_id} in unexpected status: {current_beatoven_status}. Retrying...")
                await asyncio.sleep(interval)

        except Exception as e:
            error_msg = f"Error during Beatoven.ai status watch for {internal_task_id}: {e}"
            mock_beatoven_tasks[internal_task_id]["status"] = "failed"
            mock_beatoven_tasks[internal_task_id]["error"] = str(e) # Store the exception message
            print(error_msg)
            return # Exit polling

    # If loop finishes without returning, it means max_retries were reached
    mock_beatoven_tasks[internal_task_id]["status"] = "failed"
    mock_beatoven_tasks[internal_task_id]["error"] = "Beatoven.ai generation timed out after multiple retries."
    print(f"Beatoven.ai generation timed out for internal task_id: {internal_task_id}")


# --- Main Background Task for Music Generation ---

async def generate_music_with_beatoven(internal_task_id: str, mood: str, duration: int):
    """
    Orchestrates the music generation process with Beatoven.ai.
    """
    print(f"Starting Beatoven.ai integration for internal task_id: {internal_task_id}")
    try:
        # Construct the text prompt for Beatoven.ai
        track_meta = {
            "prompt": {"text": f"A {mood} music track."},
            "duration": duration,
            "format": "mp3" # Request MP3 format
        } 

        # 1. Initiate Composition
        compose_res = await compose_track(track_meta)
        beatoven_task_id = compose_res["task_id"]
        
        mock_beatoven_tasks[internal_task_id]["beatoven_task_id"] = beatoven_task_id
        print(f"Beatoven.ai composition initiated. Beatoven Task ID: {beatoven_task_id}")

        # 2. Watch for Task Status Completion
        await watch_beatoven_task_status(internal_task_id, beatoven_task_id)

    except Exception as e:
        error_msg = f"Failed to initiate or track Beatoven.ai generation for internal task_id {internal_task_id}: {e}"
        mock_beatoven_tasks[internal_task_id]["status"] = "failed"
        mock_beatoven_tasks[internal_task_id]["error"] = str(e) # Store the exception message
        print(error_msg)


# --- Define the FastAPI routes that implement the tool logic ---

@register_tool(
    name="initiate_music_generation",
    input_model=InitiateMusicGenerationInput,
    output_model=InitiateMusicGenerationOutput,
    description="Initiates a music generation task using Beatoven.ai for a given mood and duration. Returns a unique task ID."
)
@app.post("/initiate_music_generation/", response_model=InitiateMusicGenerationOutput, status_code=status.HTTP_200_OK)
async def initiate_music_generation_route(
    input_data: InitiateMusicGenerationInput,
    background_tasks: BackgroundTasks
) -> InitiateMusicGenerationOutput:
    """
    Initiates a music generation task with Beatoven.ai. A unique task ID is generated and returned.
    """
    internal_task_id = str(uuid.uuid4())
    mock_beatoven_tasks[internal_task_id] = {
        "status": "processing",
        "mood": input_data.mood,
        "duration": input_data.duration_seconds,
        "music_url": None,
        "error": None,
        "start_time": time.time(),
        "beatoven_task_id": None # To store the Beatoven.ai's task ID
    }
    print(f"Initiated music generation task with internal ID: {internal_task_id}")

    background_tasks.add_task(
        generate_music_with_beatoven, internal_task_id, input_data.mood, input_data.duration_seconds
    )

    return InitiateMusicGenerationOutput(task_id=internal_task_id)

@register_tool(
    name="get_music_generation_status",
    input_model=GetMusicGenerationStatusInput,
    output_model=GetMusicGenerationStatusOutput,
    description="Retrieves the status and result of a music generation task by its task ID."
)
@app.post("/get_music_generation_status/", response_model=GetMusicGenerationStatusOutput, status_code=status.HTTP_200_OK)
async def get_music_generation_status_route(
    input_data: GetMusicGenerationStatusInput
) -> GetMusicGenerationStatusOutput:
    """
    Retrieves the status of a music generation task using its internal task ID.
    This will now reflect the actual Beatoven.ai status.
    """
    internal_task_id = input_data.task_id
    task_info = mock_beatoven_tasks.get(internal_task_id)

    if not task_info:
        print(f"Task ID '{internal_task_id}' not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID '{internal_task_id}' not found.")

    print(f"Checking status for internal task_id: {internal_task_id}. Current status: {task_info['status']}")
    return GetMusicGenerationStatusOutput(
        status=task_info["status"],
        music_url=task_info["music_url"],
        error=task_info["error"]
    )
