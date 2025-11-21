import os
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path

from ...models.paper import Concept, VideoStatus, ConceptVideo
from ...core.config import settings
from .upload import papers_db, save_papers_to_disk

manager = None

router = APIRouter()


class GenerateVideoRequest(BaseModel):
    concept_id: str = ""


async def run_agent_script(
    paper_id: str, concept_name: str, concept_description: str, output_dir: str
) -> Dict[str, Any]:
    # Calculate paths relative to this file
    # video.py is at: backend/app/api/endpoints/video.py
    # We need to go up to project root: parents[4] = backend/app/api/endpoints -> backend/app/api -> backend/app -> backend -> project_root
    current_file = Path(__file__).resolve()
    
    # Try to find project root by going up from current file
    # In Docker, the path might be /backend/app/api/endpoints/video.py
    # In local, it might be /Users/.../clarifai/backend/app/api/endpoints/video.py
    project_root = current_file.parents[4]
    
    # Check if we're in Docker (path starts with /backend)
    if str(current_file).startswith('/backend'):
        # In Docker, project root is /backend
        project_root = Path('/backend')
        agent_script_path = project_root / "run_agent.py"
        python_executable = project_root / "agent_env" / "bin" / "python"
    else:
        # Local development
        agent_script_path = project_root / "backend" / "run_agent.py"
        python_executable = project_root / "backend" / "agent_env" / "bin" / "python"
    
    # Fallback to system python if agent_env doesn't exist
    if isinstance(python_executable, Path) and not python_executable.exists():
        python_executable = "python3"
    
    api_key = settings.GEMINI_API_KEY

    print(f"[VIDEO] API key present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
    print(f"[VIDEO] Agent script path: {agent_script_path}")
    print(f"[VIDEO] Python executable: {python_executable}")
    print(f"[VIDEO] Output dir: {output_dir}")
    print(f"[VIDEO] Script exists: {agent_script_path.exists()}")
    print(f"[VIDEO] Python exists: {Path(python_executable).exists() if isinstance(python_executable, Path) else True}")

    if not api_key:
        return {
            "success": False,
            "error": "GEMINI_API_KEY not found in backend environment.",
        }

    if not agent_script_path.exists():
        error_msg = f"Agent script not found at {agent_script_path}. Current working directory: {Path.cwd()}"
        print(f"[VIDEO] ERROR: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "clip_paths": [],
        }

    cmd = [
        str(python_executable),
        str(agent_script_path),
        concept_name,
        concept_description,
        output_dir,
        api_key,
    ]

    print(f"[VIDEO] Running command: {' '.join([str(cmd[0]), str(cmd[1]), str(cmd[2])[:30], str(cmd[3])[:30], str(cmd[4]), '***API_KEY***'])}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(project_root),  # Run from project root to ensure relative paths work
    )
    print(f"[VIDEO] Process started with PID: {process.pid}")

    final_result = None
    successful_clips = []

    # Read stdout and stderr concurrently
    async def read_stdout():
        nonlocal final_result, successful_clips
        async for line in process.stdout:
            decoded_line = line.decode("utf-8").strip()

            # Print to console for debugging
            print(f"Agent output: {decoded_line}")

            if decoded_line.startswith("LOG: "):
                log_message = decoded_line[5:]
                print(f"Sending log via WebSocket: {log_message}")
                if manager:
                    try:
                        await manager.send_log(
                            paper_id, json.dumps({"type": "log", "message": log_message})
                        )
                        print(f"Log sent successfully")
                    except Exception as e:
                        print(f"Error sending log: {e}")
            elif decoded_line.startswith("CLIP_SUCCESS: "):
                clip_path = decoded_line[14:]
                successful_clips.append(clip_path)
            elif decoded_line.startswith("FINAL_RESULT: "):
                result_json = decoded_line[14:]
                try:
                    final_result = json.loads(result_json)
                except json.JSONDecodeError:
                    final_result = {
                        "success": False,
                        "error": "Failed to decode agent's final result.",
                    }

    async def read_stderr():
        stderr_lines = []
        async for line in process.stderr:
            decoded_line = line.decode("utf-8").strip()
            print(f"Agent stderr: {decoded_line}")
            stderr_lines.append(decoded_line)
        return stderr_lines

    # Wait for both stdout and stderr
    stdout_task = asyncio.create_task(read_stdout())
    stderr_task = asyncio.create_task(read_stderr())

    stderr_lines = await asyncio.gather(stdout_task, stderr_task)
    stderr_output = stderr_lines[1]

    await process.wait()
    print(f"[VIDEO] Process exited with code: {process.returncode}")

    if final_result:
        final_result["clip_paths"] = successful_clips
        return final_result

    if stderr_output:
        error_message = f"Agent crashed without a final result. STDERR:\n{'\n'.join(stderr_output)}"
        print(f"[VIDEO] Agent error: {error_message}")
        if manager:
            await manager.send_log(
                paper_id, json.dumps({"type": "log", "message": error_message})
            )
        return {
            "success": False,
            "error": error_message,
            "clip_paths": successful_clips,
        }

    return {
        "success": False,
        "error": "Agent finished without providing a result.",
        "clip_paths": successful_clips,
    }


async def generate_video_background(paper_id: str, concept_id: str, concept: Concept):
    paper = papers_db.get(paper_id)
    if not paper:
        return
    concept_video = paper.concept_videos.get(concept_id)
    if not concept_video:
        return

    async def log(message: str):
        print(message)
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        concept_video.logs.append(log_entry)
        if manager:
            await manager.send_log(
                paper_id, json.dumps({"type": "log", "message": log_entry})
            )

    try:
        await log("Handing off to agent for video generation...")

        project_root = Path(__file__).resolve().parents[4]
        clips_dir = project_root / "backend/clips"
        videos_dir = project_root / "backend/videos"

        output_dir = clips_dir / f"{paper_id}_{concept_id}"
        os.makedirs(output_dir, exist_ok=True)

        result = await run_agent_script(
            paper_id, concept.name, concept.description, str(output_dir)
        )

        clip_paths = result.get("clip_paths", [])
        concept_video.captions = result.get("captions", [])

        if not clip_paths:
            await log("Agent did not produce any successful video clips.")
            concept_video.status = VideoStatus.FAILED
            save_papers_to_disk()
            return

        await log(
            "Agent finished. Stitching " + str(len(clip_paths)) + " successful clips..."
        )

        final_video_path = await stitch_clips_simple(
            f"{paper_id}_{concept_id}", clip_paths, str(videos_dir)
        )

        if final_video_path:
            file_name = os.path.basename(final_video_path)
            accessible_path = f"/api/videos/{file_name}"
            await log(f"Video successfully stitched: {accessible_path}")
            concept_video.video_path = accessible_path
            concept_video.status = VideoStatus.COMPLETED
            save_papers_to_disk()
        else:
            await log("Stitching failed.")
            concept_video.status = VideoStatus.FAILED
            save_papers_to_disk()

    except Exception as e:
        await log(f"An unexpected error occurred: {e}")
        concept_video.status = VideoStatus.FAILED
        save_papers_to_disk()


async def stitch_clips_simple(
    file_prefix: str, clip_paths: List[str], videos_dir: str
) -> Optional[str]:
    if not clip_paths:
        return None

    os.makedirs(videos_dir, exist_ok=True)

    output_path = os.path.join(videos_dir, f"{file_prefix}_final.mp4")
    concat_file_path = os.path.join(videos_dir, f"{file_prefix}_concat.txt")

    with open(concat_file_path, "w", encoding="utf-8") as f:
        for path in clip_paths:
            # The agent now returns verified, absolute paths. No modification needed.
            safe_path = str(path).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file_path,
        "-c",
        "copy",
        output_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print("--- FFMPEG STITCHING FAILED ---")
        print(f"STDOUT:\n{stdout.decode()}")
        print(f"STDERR:\n{stderr.decode()}")
        return None

    os.remove(concat_file_path)
    return output_path


@router.post("/papers/{paper_id}/concepts/{concept_id}/generate-video")
async def generate_video_for_concept(
    paper_id: str,
    concept_id: str,
    background_tasks: BackgroundTasks,
    request: GenerateVideoRequest = GenerateVideoRequest(),
) -> Dict[str, str]:
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = papers_db[paper_id]
    concept = next((c for c in paper.concepts if c.id == concept_id), None)

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Check if this specific concept already has a video being generated
    existing_video = paper.concept_videos.get(concept_id)
    if existing_video and existing_video.status == VideoStatus.GENERATING:
        raise HTTPException(
            status_code=400, detail="A video is already being generated for this concept."
        )

    # Allow multiple videos to be generated simultaneously for different concepts
    # But check if there are too many concurrent generations (limit to 3)
    generating_count = sum(1 for cv in paper.concept_videos.values() if cv.status == VideoStatus.GENERATING)
    if generating_count >= 3:
        raise HTTPException(
            status_code=400, detail="Too many videos are being generated simultaneously. Please wait for one to complete."
        )

    paper.concept_videos[concept_id] = ConceptVideo(
        concept_id=concept_id,
        concept_name=concept.name,
        status=VideoStatus.GENERATING,
        created_at=datetime.now(),
    )
    
    # Persist the status change immediately so frontend polling sees it
    save_papers_to_disk()
    print(f"[VIDEO] Set video_status to GENERATING for concept {concept_id}, paper {paper_id}")

    background_tasks.add_task(
        generate_video_background,
        paper_id,
        concept_id,
        concept,
    )

    return {"message": "Video generation started"}


@router.get("/papers/{paper_id}/concepts/{concept_id}/video/status")
async def get_concept_video_status(paper_id: str, concept_id: str) -> Dict[str, Any]:
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = papers_db[paper_id]
    concept_video = paper.concept_videos.get(concept_id)

    if not concept_video:
        return {"status": "not_started", "logs": [], "captions": []}

    # Map backend status to frontend expected values
    status_map = {
        "not_started": "not_started",
        "generating": "generating",
        "completed": "completed",
        "failed": "error"
    }

    return {
        "status": status_map.get(concept_video.status.value, "not_started"),
        "video_url": concept_video.video_path,
        "logs": concept_video.logs,
        "captions": concept_video.captions,
    }
