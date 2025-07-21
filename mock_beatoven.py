import uuid
import time
import json
from typing import Dict, Any, Optional

# Hardcoded mock URL for testing purposes
DEFAULT_MOCK_MUSIC_URL = " https://composition-lambda.s3-accelerate.amazonaws.com/f048176f-138e-4aad-bbab-b54021fb4d3d_1ppvt/full_track.mp3?AWSAccessKeyId=ASIA57U76BH67LRXCR67&Signature=MzW9yqklVDSNQo8pXReKRlSKIXg%3D&x-amz-security-token=IQoJb3JpZ2luX2VjELv%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCmFwLXNvdXRoLTEiRzBFAiEAjCFfMyAUzTE9vKTXylEVcY9jjHaTLvsrAckoU9tJIxoCIGfYU5ZFpHXV5e4EmkHqGL1UNY0a2s%2BLPMCbi4ChoMOyKoIDCNT%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQAhoMOTYxMzM0MzQ4Mjg1IgwFS4pL6ibe%2BTGWyxIq1gKATNR%2FCibfTlL5Nth19dE18WVg%2BvmAFWYPENBunfecXG%2FwYapiF469lPAWsG%2BgF97GUttnSpPIGSzuDj%2BGGdL9LJZMyrWoTst2Scs%2BYcJrD9sg%2FoMTXeyUCxLYXFpBCd9PmiOihli3TcdnyE0pdUfeAfdrdJgqBtaaapFqWjE2r9vjp%2FPhEELV7cx4DlYOmE8meebVu5f4BcQsxjU7dKT6D3hRs2WCVSmJGyY%2FZquppHfv6XDF1rozpGnQHPRyBPy4jlxmmR%2Fi6YyKckwj4nyq%2BL0s2yaeSGvxD7xsUeLRAxEucNDU9LvxFE120hiquqImFi5vwN7i59ayMenqG7D9g4K7MPqYAgIE1u5Y3zzRORWRH0dDJlsMEVPFGr2fZqsm2OidHnOLEF8t2%2Fk%2BD2%2FxYzzxYgf3ekMAYYF2Wf8mQ1gRr2inNa3ltNUk30mXnO%2BVLrrGA6cwob%2F4wwY6ngGT%2BQf4KqxxcuAOef3YcD%2B0Z45JOSccqc1m1xjrD%2FUyUpSoBQeaAxxkLQwoSDtj5zrcwf7sChj4t61f8XfyyAHf%2BZnVYKJf7Lpbx70EsVu%2BsZ0f%2FWWTxbFO3fxFehfxJGuqyi3vzvaagCUXo2PFXghc6qh%2B7lcKOlP9qaaTipTTs3AhCVQqbnLw4k9thqnvx6NE1XCo1kjqYnsY25nW%2Fw%3D%3D&Expires=1753098207"

def handle_mock_music_generation(
    internal_task_id: str,
    mood: str,
    duration_seconds: int,
    intensity: float,
    mock_music_url: Optional[str],
    mock_beatoven_tasks: Dict[str, Dict[str, Any]],
    backend_v1_api_url: str # Added to print the mock URL
) -> str:
    """
    Handles the mock music generation response, updating the internal task store.
    Prints what the Beatoven.ai compose request would have been.
    """
    # Construct what would be the Beatoven.ai compose request for logging
    compose_url = f"{backend_v1_api_url}/tracks/compose"
    track_meta_would_be = {
        "prompt": {"text": f"A {mood} music track with a mood intensity of {intensity}."},
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

