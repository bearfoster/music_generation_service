import uuid
import time
import json
from typing import Dict, Any, Optional

# Hardcoded mock URL for testing purposes
DEFAULT_MOCK_MUSIC_URL = " https://composition-lambda.s3-accelerate.amazonaws.com/bdf29f2f-4ae9-4903-91c6-3ff62a438b9a_1vemn/full_track.mp3?AWSAccessKeyId=ASIA57U76BH6TRTE7GRW&Signature=MbmliD2vyhNKx1HVf8SXMn6weeM%3D&x-amz-security-token=IQoJb3JpZ2luX2VjELz%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCmFwLXNvdXRoLTEiRzBFAiA5Zy6OL758X6Nc9%2BRD4Ab%2FZT42fxBi0DIHfEirbIxbhgIhAJyR09q9fluSsNHSF%2FWvdWh%2FOuB5bECwy3LVAdEhUhhDKoIDCNX%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQAhoMOTYxMzM0MzQ4Mjg1IgxyJz%2BgyqRVNGA7JlQq1gLaGEjpi8cJf3Ks4EJM2ThekRR1U6vhkMlbmAkDSiUt2yyHOV4dW%2F0ISHd%2FEC0F1mxlQAmmcocru4a2rweia9fD1auF9%2FUpL5ftk4Q0BgZTGrH%2BM6zeBBaDcnM9FVgV14fFvgrKBSN9Js42EQCB8xRSM%2BAbFf9M7W%2BwPDTXhve%2FzTF%2FIK%2BTeMyS8gX342om%2Bq0l165AkMa82zjp67Kq5Bi4UNrTP49lwPaPkbqUJ7wJgQA3Uc6CdXUuH3PKWi3PO%2BiNaVbLlAnJe6bEd6ExVbIVvtTfqWx3kNFt%2FYu6JBQ5DOW1NpB0LAnNoHVA4KwdifGIV2UVwRNNhkBPvh00yIyGS1zNJFNYUAfCrVgF%2BoABZ5DjSQTONCmTrJbVchtpPUk%2BmRDJhgMEseX0TWJ5qq%2Bmg3Kl3pP%2F80wiTsZyPhNmprsHITzzlgbg1Qfc521tSM2KYVqG6dYwkM%2F4wwY6ngFNV2Ssk%2FMc3D8XckhjDfLrOBXkRgMiiPyY0mccGwQjEmluDmGMWbGFNHNXu1ETq%2F9SCn%2FSpRxA0h0NXqJVwRilwzc%2BazOsLh5iCFKTu3GRE%2BS%2B3RW4qP6xXVx99txwndDa9HteBI1BvyXV3zR1uxzgaI7c%2Bf%2BfAqRMz2I05QK9%2Bh3Gu00zvKvntwVJOPyLpfwNNOU8Fr9O9uzRqdUlEA%3D%3D&Expires=1753100089"

# Function to handle the mock music generation response

def handle_mock_music_generation(
    internal_task_id: str,
    mood: str,
    duration_seconds: int,
    intensity: float,
    mock_music_url: Optional[str],
    mock_beatoven_tasks: Dict[str, Dict[str, Any]],
    backend_v1_api_url: str,
    theme: Optional[str]
) -> str:
    """
    Handles the mock music generation response, updating the internal task store.
    Prints what the Beatoven.ai compose request would have been.
    """
    # Construct what would be the Beatoven.ai compose request for logging
    compose_url = f"{backend_v1_api_url}/tracks/compose"
    
    prompt_text = f"A {mood} music track with a mood intensity of {intensity}."
    if theme:
        prompt_text += f" In a {theme} style."

    track_meta_would_be = {
        "prompt": {"text": prompt_text},
        "duration": duration_seconds,
        "format": "mp3",
    }
    print("\n--- MOCK RESPONSE: What would have been the Beatoven.ai Compose Request ---")
    print(f"URL: {compose_url}")
    print(f"Method: POST")
    print(f"Headers: {{'Authorization': 'Bearer <YOUR_API_KEY>', 'Content-Type': 'application/json'}}")
    print(f"Body: {json.dumps(track_meta_would_be, indent=2)}")
    print("---------------------------------------------------------------------------\n")

    # Set up the mock response in the internal task store
    music_url = mock_music_url if mock_music_url else DEFAULT_MOCK_MUSIC_URL
    mock_beatoven_tasks[internal_task_id] = {
        "status": "completed",
        "mood": mood,
        "duration": duration_seconds,
        "music_url": music_url,
        "error": None,
        "start_time": time.time(),
        "beatoven_task_id": "MOCKED_TASK_" + str(uuid.uuid4()) # A distinct ID for mock tasks
    }
    print(f"Initiated MOCKED music generation task with internal ID: {internal_task_id}. URL: {music_url}")
    
    return internal_task_id
