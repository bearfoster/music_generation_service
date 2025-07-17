# music_generation_service/main.py

from dotenv import load_dotenv # ADDED
load_dotenv() # ADDED: Load environment variables from .env file

import os
import uuid
import time
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional, Callable, Type

# Initialize the FastAPI application
app = FastAPI(
    title="Music Generation Service",
    description="Agent for translating a given mood into a generated music composition (simulated).",
    version="0.2.1"
)

# In-memory store to simulate Beatoven.ai task statuses and results.
mock_beatoven_tasks: Dict[str, Dict[str, Any]] = {}

# --- Tool Registry Pattern ---
TOOLS = {}

def register_tool(name: str, input_model: Type[BaseModel], output_model: Type[BaseModel], description: str):
    def decorator(func: Callable):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "input_schema": input_model.schema(),
            "output_schema": output_model.schema(),
            "function": func
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

# --- Simulated Beatoven.ai Background Task ---

async def simulate_music_generation(task_id: str, mood: str, duration: int):
    """
    Simulates the asynchronous music generation process.
    """
    print(f"Simulating music generation for task_id: {task_id}, mood: {mood}, duration: {duration}s")
    await asyncio.sleep(min(duration / 10, 10))

    mock_beatoven_tasks[task_id]["status"] = "completed"
    mock_beatoven_tasks[task_id]["music_url"] = f"https://mock-music-cdn.com/generated_music/{task_id}_{mood}.mp3"
    print(f"Music generation completed for task_id: {task_id}. URL: {mock_beatoven_tasks[task_id]['music_url']}")


# --- Define the FastAPI routes that implement the tool logic ---

@register_tool(
    name="initiate_music_generation",
    input_model=InitiateMusicGenerationInput,
    output_model=InitiateMusicGenerationOutput,
    description="Initiates a simulated music generation task for a given mood and duration. Returns a unique task ID."
)
@app.post("/initiate_music_generation/", response_model=InitiateMusicGenerationOutput, status_code=status.HTTP_200_OK)
async def initiate_music_generation_route(
    input_data: InitiateMusicGenerationInput,
    background_tasks: BackgroundTasks
) -> InitiateMusicGenerationOutput:
    """
    Initiates a simulated music generation task. A unique task ID is generated and returned.
    """
    task_id = str(uuid.uuid4())
    mock_beatoven_tasks[task_id] = {
        "status": "processing",
        "mood": input_data.mood,
        "duration": input_data.duration_seconds,
        "music_url": None,
        "error": None,
        "start_time": time.time()
    }
    print(f"Initiated music generation task with ID: {task_id}")

    background_tasks.add_task(
        simulate_music_generation, task_id, input_data.mood, input_data.duration_seconds
    )

    return InitiateMusicGenerationOutput(task_id=task_id)

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
    Retrieves the status of a simulated music generation task using its task ID.
    """
    task_id = input_data.task_id
    task_info = mock_beatoven_tasks.get(task_id)

    if not task_info:
        print(f"Task ID '{task_id}' not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID '{task_id}' not found.")

    print(f"Checking status for task_id: {task_id}. Current status: {task_info['status']}")
    return GetMusicGenerationStatusOutput(
        status=task_info["status"],
        music_url=task_info["music_url"],
        error=task_info["error"]
    )
