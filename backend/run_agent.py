import os
import sys
import json
import subprocess
import time
import tempfile
import re
from pathlib import Path
import google.genai as genai
from google.genai import types


def log(message):
    """Prints a log message to stdout for real-time streaming."""
    print("LOG: " + str(message), flush=True)


def read_prompt_template(filename):
    """Reads a prompt template from the 'prompts' directory."""
    script_dir = Path(__file__).parent
    template_path = script_dir / "prompts" / filename
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def initialize_llm(api_key):
    """Initializes the language model with the provided API key."""
    log("--- DEBUG: Initializing LLM. ---")
    log(f"--- DEBUG: API key length: {len(api_key) if api_key else 0} ---")
    if not api_key:
        raise ValueError("API key must be set when using the Google AI API.")
    client = genai.Client(api_key=api_key)
    log("--- DEBUG: LLM Initialized successfully. ---")
    return client


def call_gemini_with_retries(client, contents, temperature, context_label):
    """Calls Gemini with retries for quota/rate limit errors."""
    max_retries = 5
    base_delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )
        except Exception as e:
            error_message = str(e)
            log(
                f"--- WARNING: {context_label} attempt {attempt} failed with error: {error_message} ---"
            )
            quota_exhausted = (
                "RESOURCE_EXHAUSTED" in error_message
                or "quota" in error_message.lower()
                or "429" in error_message
            )
            if not quota_exhausted or attempt == max_retries:
                log("--- ERROR: Exhausted retries for Gemini call. ---")
                raise

            delay = base_delay * attempt
            log(
                f"--- INFO: Retrying {context_label} in {delay} seconds due to quota exhaustion. ---"
            )
            time.sleep(delay)


def get_video_scenes(client, concept_name, concept_description):
    """Uses an AI call to split a concept into logical, thematic scenes for a video."""
    log("--- DEBUG: Calling LLM to determine video scenes. ---")
    template = read_prompt_template("split_scenes.txt")
    prompt = template.format(
        concept_name=concept_name, concept_description=concept_description
    )

    log("--- PROMPT FOR SCENE SPLITTING ---")
    log(prompt)
    response = call_gemini_with_retries(
        client,
        prompt,
        temperature=0.3,
        context_label="Scene splitting",
    )
    response_text = response.text.strip()
    log("--- AI RESPONSE (SCENES) ---")
    log(response_text)

    json_match = re.search(r"\[.*\]", response_text, re.DOTALL)

    if json_match:
        json_string = json_match.group(0)
        try:
            scenes = json.loads(json_string)
            if isinstance(scenes, list) and all(isinstance(s, str) for s in scenes):
                log(
                    "--- DEBUG: Successfully parsed "
                    + str(len(scenes))
                    + " scenes. ---"
                )
                return scenes
        except json.JSONDecodeError:
            log(
                "--- WARNING: Found a JSON-like string, but it was invalid. Falling back. ---"
            )

    log(
        "--- WARNING: Failed to find or parse scenes from AI response. Falling back to sentence splitting. ---"
    )
    return [
        s.strip() for s in concept_description.split(".") if len(s.strip()) > 10
    ] or [concept_description]


def replace_tex_with_text(code):
    """Replaces any Tex/MathTex usage with Text to avoid LaTeX dependency."""
    replaced = False

    def _sub(match):
        nonlocal replaced
        replaced = True
        return "Text("

    code = re.sub(r"\b(?:MathTex|Tex)\s*\(", _sub, code)
    if replaced:
        log("--- DEBUG: Replaced Tex/MathTex with Text to avoid LaTeX dependency. ---")
    return code


def normalize_latex_markup(code):
    """
    Converts common LaTeX markup that slips through into friendly unicode/plain text
    so Text() labels don't show raw commands like \\textbf{}.
    """

    def strip_wrapper(pattern, text):
        def _repl(match):
            return match.group(1)

        return re.sub(pattern, _repl, text)

    original_code = code
    # Strip common wrappers
    wrappers = [
        r"\\textbf\{([^{}]+)\}",
        r"\\textit\{([^{}]+)\}",
        r"\\mathbf\{([^{}]+)\}",
        r"\\mathit\{([^{}]+)\}",
        r"\\text\{([^{}]+)\}",
    ]
    for pattern in wrappers:
        code = strip_wrapper(pattern, code)

    # Replace common commands with unicode equivalents
    replacements = {
        r"\\alpha": "α",
        r"\\beta": "β",
        r"\\gamma": "γ",
        r"\\delta": "δ",
        r"\\theta": "θ",
        r"\\lambda": "λ",
        r"\\mu": "μ",
        r"\\pi": "π",
        r"\\sigma": "σ",
        r"\\phi": "φ",
        r"\\psi": "ψ",
        r"\\omega": "ω",
        r"\\cdot": "·",
        r"\\times": "×",
        r"\\rightarrow": "→",
        r"\\leftarrow": "←",
        r"\\approx": "≈",
        r"\\leq": "≤",
        r"\\geq": "≥",
        r"\\neq": "≠",
    }
    for needle, replacement in replacements.items():
        code = code.replace(needle, replacement)

    # Clean escaped braces leftover from \text{} removal
    code = code.replace(r"\{", "{").replace(r"\}", "}")

    if code != original_code:
        log("--- DEBUG: Normalized LaTeX markup inside Text labels. ---")

    return code


def ensure_rate_functions_usage(code):
    """Ensures custom easing functions import and usage use rate_functions namespace."""
    needs_import = False

    def replace_ease(match):
        nonlocal needs_import
        needs_import = True
        return f"rate_functions.{match.group(0)}"

    code = re.sub(r"(?<!rate_functions\.)\bease_[a-z0-9_]+\b", replace_ease, code)

    if needs_import and "from manim.utils import rate_functions" not in code:
        lines = code.splitlines()
        insert_idx = 0
        for idx, line in enumerate(lines):
            if line.strip().startswith("from manim import *"):
                insert_idx = idx + 1
                break
        lines.insert(insert_idx, "from manim.utils import rate_functions")
        code = "\n".join(lines)
        log("--- DEBUG: Added rate_functions import for easing helpers. ---")

    return code


def sanitize_code(code):
    """Aggressively sanitizes the AI's code output."""
    log("--- DEBUG: Sanitizing AI response. ---")
    code_pattern = re.compile(r"```python\n(.*?)\n```", re.DOTALL)
    match = code_pattern.search(code)

    if match:
        code = match.group(1).strip()
        log("--- DEBUG: Extracted Python code from markdown block. ---")

    if "from manim import *" not in code:
        code = "from manim import *\n\n" + code
        log("--- DEBUG: Added missing 'from manim import *' import. ---")

    code = replace_tex_with_text(code)
    code = normalize_latex_markup(code)
    code = ensure_rate_functions_usage(code)

    return code


def generate_manim_code(client, description):
    """Generates the initial Manim code for a single scene."""
    template = read_prompt_template("generate_code.txt")
    prompt = template.format(description=description)

    log("--- PROMPT FOR MANIM CODE ---")
    log(prompt)
    response = call_gemini_with_retries(
        client,
        prompt,
        temperature=0.3,
        context_label="Initial Manim code generation",
    )
    code = response.text.strip()
    log("--- AI RESPONSE (RAW CODE) ---")
    log(code)
    return sanitize_code(code)


def correct_manim_code(client, code, error):
    """Corrects the Manim code based on an error message."""
    template = read_prompt_template("correct_code.txt")
    prompt = template.format(code=code, error=error)

    log("--- PROMPT FOR CODE CORRECTION ---")
    log(prompt)
    response = call_gemini_with_retries(
        client,
        prompt,
        temperature=0.3,
        context_label="Manim code correction",
    )
    new_code = response.text.strip()
    log("--- AI RESPONSE (RAW CORRECTED CODE) ---")
    log(new_code)
    return sanitize_code(new_code)


def render_manim_code(code, output_dir, file_name):
    """
    Renders a single Manim scene and returns the full path to the complete video file,
    ignoring the partial movie files.
    """
    class_name = "Scene"
    for line in code.split("\n"):
        if line.strip().startswith("class ") and "Scene" in line:
            class_name = line.split("class ")[1].split("(")[0].strip()
            break
    log("--- DEBUG: Detected scene class name: " + class_name + " ---")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        cmd = [
            sys.executable,
            "-m",
            "manim",
            temp_file_path,
            class_name,
            "-o",
            file_name,
            "--media_dir",
            output_dir,
            "-v",
            "WARNING",
            "-ql",
        ]
        log("--- DEBUG: Executing Manim command: " + " ".join(cmd) + " ---")
        process = subprocess.run(
            cmd, capture_output=True, text=True, check=False, encoding="utf-8"
        )

        if process.returncode != 0:
            # --- THIS IS THE DEFINITIVE FIX FOR THE SYNTAX ERROR ---
            # Build the error message safely to prevent parsing errors.
            error_parts = [
                "--- MANIM STDOUT ---\\n",
                process.stdout,
                "\\n\\n--- MANIM STDERR ---\\n",
                process.stderr,
            ]
            error_message = "".join(error_parts)
            return None, error_message

        for root, dirs, files in os.walk(output_dir):
            if file_name in files and "partial_movie_files" not in root:
                found_path = os.path.join(root, file_name)
                log("--- DEBUG: Found final rendered video at: " + found_path + " ---")
                return found_path, None

        return (
            None,
            "--- AGENT ERROR: Could not find the rendered video file after a successful render. ---",
        )

    finally:
        os.unlink(temp_file_path)


def main():
    try:
        if len(sys.argv) != 5:
            log("--- FATAL ERROR: Agent requires 4 arguments. ---")
            print(
                "FINAL_RESULT: "
                + json.dumps({"success": False, "error": "Invalid arguments"})
            )
            return

        concept_name, concept_description, output_dir, api_key = (
            sys.argv[1],
            sys.argv[2],
            sys.argv[3],
            sys.argv[4],
        )

        client = initialize_llm(api_key)

        scenes = get_video_scenes(client, concept_name, concept_description)
        captions = [
            {"clip": idx + 1, "text": scene_description, "rendered": False}
            for idx, scene_description in enumerate(scenes)
        ]
        successful_clips = 0

        for i, scene_description in enumerate(scenes):
            log(
                "--- Generating Clip "
                + str(i + 1)
                + "/"
                + str(len(scenes))
                + ": "
                + scene_description
                + " ---"
            )
            output_filename = "clip_" + str(i) + ".mp4"

            code = None
            error = "Initial code generation failed."

            for attempt in range(1, 4):
                log("--- Clip " + str(i + 1) + ", Attempt " + str(attempt) + " ---")
                if code is None:
                    code = generate_manim_code(client, scene_description)
                else:
                    code = correct_manim_code(client, code, error)

                video_path, error = render_manim_code(code, output_dir, output_filename)

                if error is None:
                    log("--- Clip " + str(i + 1) + " rendered successfully. ---")
                    print("CLIP_SUCCESS: " + video_path, flush=True)
                    successful_clips += 1
                    if i < len(captions):
                        captions[i]["rendered"] = True
                    break

                log(
                    "--- Clip "
                    + str(i + 1)
                    + ", Attempt "
                    + str(attempt)
                    + " failed. ---"
                )

            if error is not None:
                log(
                    "--- FAILED to generate clip "
                    + str(i + 1)
                    + " after 3 attempts. Skipping this clip. ---"
                )

        if successful_clips == 0:
            log("--- All clips failed to generate. Aborting video generation. ---")
            print(
                "FINAL_RESULT: "
                + json.dumps(
                    {
                        "success": False,
                        "error": "All clips failed to render.",
                        "captions": captions,
                    }
                )
            )
        else:
            log("--- Agent finished generating clips. ---")
            print("FINAL_RESULT: " + json.dumps({"success": True, "captions": captions}))

    except Exception as e:
        log("--- FATAL CRASH in agent's main loop: " + str(e) + " ---")
        print(
            "FINAL_RESULT: "
            + json.dumps({"success": False, "error": "Agent crashed unexpectedly"})
        )


if __name__ == "__main__":
    main()
