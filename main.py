# music_generation_service/main.py

import os
import uuid
import time
import asyncio # Explicitly import asyncio for sleep
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional

# Corrected Import for fastapi-mcp v0.1.8
# MCPService and tool decorator are no longer directly imported.
# Instead, we use `add_mcp_server` to get the server instance,
# which then automatically discovers tools from FastAPI routes.
from fastapi_mcp.server import add_mcp_server
from mcp.server.fastmcp import FastMCP # Need to import FastMCP for type hinting

# Initialize the FastAPI application
app = FastAPI(
    title="Music Generation Service",
    description="Agent for translating a given mood into a generated music composition (simulated).",
    version="0.2.1" # Updated version to reflect MCP API change
)

# In-memory store to simulate Beatoven.ai task statuses and results.
# In a real-world scenario, this would interact with a persistent database or a message queue
# and the actual Beatoven.ai API.
mock_beatoven_tasks: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Models for MCP Tools ---

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

# --- MCP Server Initialization (Updated for fastapi-mcp v0.1.8 API) ---
# Instead of initializing an MCPService class, we use add_mcp_server function
# This function creates and mounts the MCP server to the FastAPI app.
mcp_server: FastMCP = add_mcp_server(
    app=app,
    name="Music Generation Agent",
    description="Generates music based on a given mood using a simulated Beatoven.ai API.",
)

# --- Simulated Beatoven.ai Background Task ---

async def simulate_music_generation(task_id: str, mood: str, duration: int):
    """
    Simulates the asynchronous music generation process.
    In a real system, this would involve calling the actual Beatoven.ai API
    and waiting for its completion callback or polling.
    """
    print(f"Simulating music generation for task_id: {task_id}, mood: {mood}, duration: {duration}s")
    # Simulate processing time, max 10 seconds for quick demo
    await asyncio.sleep(min(duration / 10, 10))

    # After simulation, mark as completed and provide a mock URL
    mock_beatoven_tasks[task_id]["status"] = "completed"
    mock_beatoven_tasks[task_id]["music_url"] = f"https://mock-music-cdn.com/generated_music/{task_id}_{mood}.mp3"
    print(f"Music generation completed for task_id: {task_id}. URL: {mock_beatoven_tasks[task_id]['music_url']}")


# --- Define the FastAPI routes that implement the tool logic ---
# These routes themselves act as the "tools" that MCP will discover.

@app.post("/initiate_music_generation/", response_model=InitiateMusicGenerationOutput, status_code=status.HTTP_200_OK)
async def initiate_music_generation_route(
    input_data: InitiateMusicGenerationInput,
    background_tasks: BackgroundTasks
) -> InitiateMusicGenerationOutput:
    """
    Initiates a simulated music generation task. A unique task ID is generated and returned.
    The actual 'generation' is simulated in a background task.
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

    # Add the simulation to background tasks so the API can respond immediately
    background_tasks.add_task(
        simulate_music_generation, task_id, input_data.mood, input_data.duration_seconds
    )

    return InitiateMusicGenerationOutput(task_id=task_id)

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

# --- Register the tools with the MCP server ---
# Tools are automatically discovered from the FastAPI app routes by `add_mcp_server`.
# No explicit add_tool() calls needed if the routes are defined with proper Pydantic models.

# If there were any other specific configurations needed for the tools for MCP:
# mcp_server.add_tool(route=initiate_music_generation_route)
# mcp_server.add_tool(route=get_music_generation_status_route)
# (These lines are commented out as add_mcp_server generally handles it implicitly)

# To run this service:
# 1. Save the code as 'main.py' inside the 'music_generation_service' directory.
# 2. Ensure all requirements are installed in your active virtual environment.
# 3. Navigate to that directory in your terminal (with venv activated).
# 4. Run the command: uvicorn main:app --reload --port 8002
