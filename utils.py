import os
import datetime
import subprocess
import math
import cv2
import logging

# Supported video formats
supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
time_decimal_places = 3  # Number of decimal places for time values


# Format elapsed/remaining time into a human-readable string
def format_time(seconds):
    """Formats elapsed/remaining time into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f} Seconds"
    elif seconds < 3600:
        return f"{int(seconds // 60)} Minutes and {int(seconds % 60)} Seconds"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} Hours, {int((seconds % 3600) // 60)} Minutes and {int(seconds % 60)} Seconds"
    elif seconds < 2626560:
        return f"{int(seconds // 86400)} Days, {int((seconds % 86400) // 3600)} Hours, {int((seconds % 3600) // 60)} Minutes and {int(seconds % 60)} Seconds"
    elif seconds < 31536000:
        return f"{int(seconds // 2626560)} Months, {int((seconds % 2626560) // 86400)} Days, {int((seconds % 86400) // 3600)} Hours, {int((seconds % 3600) // 60)} Minutes and {int(seconds % 60)} Seconds"
    else:
        return f"{int(seconds // 31536000)} Years, {int((seconds % 31536000) // 2626560)} Months, {int((seconds % 2626560) // 86400)} Days, {int((seconds % 86400) // 3600)} Hours, {int((seconds % 3600) // 60)} Minutes and {int(seconds % 60)} Seconds"


# Find a video file in a given directory or its subdirectories
def find_video(video_name, search_dir="."):
    """Search for the video file efficiently using os.walk (case-insensitively)."""
    video_name_lower = video_name.lower()
    
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.lower() == video_name_lower:
                return os.path.join(root, file)
    return None


# Generate a unique output folder if one already exists
def get_unique_output_folder(base_folder):
    """Generate a unique folder name by appending a number if the folder already exists."""
    if not os.path.exists(base_folder):
        return None
    count = 2
    while True:
        new_folder = f"{base_folder}({count})"
        if not os.path.exists(new_folder):
            return new_folder
        count += 1


# Generate a unique output folder with a timestamp
def get_timestamp_output_folder(base_folder):
    """
    Generate a unique folder name using a timestamp to prevent overwriting.
    
    Parameters:
        base_folder (str): The base folder path where the output should be saved.
    
    Returns:
        str: A unique folder name with a timestamp.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_folder = f"{base_folder}{timestamp}"

    return unique_folder


# Get existing filenames in the output folder
# This is used to skip already existing frames
# for faster processing of large videos with many frames extracted
# O(1) lookup speed
def get_existing_filenames(output_folder):
    """Preload existing frame filenames into a set for O(1) lookup speed."""
    if not os.path.exists(output_folder):
        return set()

    return {filename for filename in os.listdir(output_folder) if filename.endswith(".jpg")}


def is_ffmpeg_installed():
    """Check if FFmpeg is installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False
    

    # Convert a video to a lossless format using FFmpeg
def convert_video_to_lossless(video_path):
    """Converts the video to a high-quality lossless format using FFmpeg and saves it in the same folder as the original video."""
    output_folder = os.path.dirname(video_path)
    output_video = os.path.join(output_folder, os.path.splitext(os.path.basename(video_path))[0] + "_lossless.mkv")

    if os.path.exists(output_video):
        print(f"Lossless video already exists: {output_video}")
        logging.info(f"Lossless video already exists: {output_video}")
        return output_video

    if not is_ffmpeg_installed():
            print("Error: FFmpeg is not installed.")
            print("Please install FFmpeg to enable lossless conversion.")
            logging.error("FFmpeg is not installed.")
            return video_path # Return the original video path if FFmpeg is not installed

    try:
        print(f"Converting {video_path} to lossless format...")
        command = [
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "ffv1", "-level", "3", "-preset", "veryslow",
            "-context", "1", "-g", "1", "-slices", "4",
            "-c:a", "flac", output_video
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        if os.path.exists(output_video):
            print(f"Conversion complete: {output_video}")
            logging.info(f"Lossless video created: {output_video}")
            return output_video
        else:
            raise ValueError("FFmpeg did not produce a valid output file.")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg error: {e}")
        print("Error: FFmpeg conversion failed. Using original video.")
    except Exception as e:
        logging.error(f"Unexpected error in FFmpeg conversion: {e}")
        print("Error: Unexpected issue with FFmpeg conversion.")

    return video_path  # Return the original video path if conversion fails


def get_frames_duration_openCV_fallback(video_path):
    """Get total frames and duration using OpenCV as a fallback method."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return -1, -1

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps if fps > 0 else -1
    cap.release()
    return duration, frame_count


# round a number to n decimal places (floor)
def round_floor_decimals(num, n):
    n = math.pow(10, n)
    print(f"n: {n}")
    print(f"num: {num}")
    return float(math.floor(num * n) / n)


# round a number to n decimal places (ceiling)
def round_ceiling_decimals(num, n):
    n = math.pow(10, n)
    return float(math.ceil(num * n) / n)


# Get the actual video duration by reading the video frame-by-frame
# This helps detect corrupted files where FFmpeg reports incorrect durations
def get_actual_video_duration_OpenCV_FallBack(video_path):
    """
    Reads the video frame-by-frame to determine the actual playable duration.
    This helps detect corrupted files where FFmpeg reports incorrect durations.
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logging.error(f"Could not open video: {video_path}")
        return -1, -1  # Ensure both duration & frame count are returned

    frame_idx = 0
    fps = cap.get(cv2.CAP_PROP_FPS)  # Get FPS to estimate time from frame count
    max_pts_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        if frame is None:
            #stop if frame is None
            # this is a workaround for corrupted video files
            # where OpenCV fails to read the frame
            break 

        timestamp = frame_idx / fps  # Convert frames to time
        frame_idx += 1
        
    print(f"Frame index: {frame_idx}")
    print(f"FPS: {fps}")
    print(f"Timestamp: {timestamp}")
    max_pts_time = round_floor_decimals(max(max_pts_time, timestamp), time_decimal_places) # Round to 3 decimal places
    cap.release()
    
    if frame_idx > math.ceil(max_pts_time * fps):
        frame_idx = max_pts_time * fps
        return max_pts_time, math.ceil(frame_idx)
    
    elif frame_idx < math.ceil(max_pts_time * fps):
        max_pts_time = frame_idx / fps
        return max_pts_time, math.ceil(frame_idx)

    logging.info(f"Actual video duration determined: {max_pts_time:.2f} seconds")
    return max_pts_time, frame_idx  # Ensure both values are returned



def get_video_frame_count(video_path):
    """Gets the total number of frames in a video using FFmpeg's ffprobe."""
    print(f"Getting frame count for {video_path}...")
    try:
        duration = get_video_duration(video_path)
        fps = get_video_fps(video_path)

        # First attempt: Get total frames from metadata
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=nb_frames",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        frame_count = result.stdout.strip()
        print(f"FFmpeg got frame count of {frame_count}")

        # Try to convert to integer, if fails or is empty, use -1
        try:
            frame_count = int(result.stdout.strip())
        except ValueError:
            frame_count = -1

        # If frame count is valid, return the values
        if frame_count > 0:
            return duration, frame_count, fps

        # Get total frames and duration using OpenCV as a fallback
        # Only use this if FFmpeg fails to get the frame count
        duration, frame_count = get_actual_video_duration_OpenCV_FallBack(video_path)

        if frame_count > 0:
            print("OpenCV fallback successful.")
            print(f"Frames: {frame_count}, Duration: {duration}")
            return duration, frame_count, fps

        # Backup method using duration and FPS
        if duration > 0 and fps > 0:
            estimated_frames = math.floor(duration * fps)
            print(f"FFmpeg did not return `nb_frames`. Estimated frames: {estimated_frames}")
            logging.warning(f"FFmpeg did not return `nb_frames`. Estimated frames: {estimated_frames}")
            return duration, estimated_frames, fps  # Ensure fallback is used

        print("FFmpeg failed to determine total frame count.")
        logging.error("FFmpeg failed to determine total frame count.")
        return duration, -1, fps  # Return -1 only if both methods fail

    except Exception as e:
        print(f"FFmpeg failed to determine total frame count: {e}")
        logging.error(f"FFmpeg failed to determine total frame count: {e}")
        return duration, -1, fps  # Return -1 if failed


def get_video_duration(video_path):
    """Gets the total duration of a video in seconds using FFmpeg's ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip()) if result.stdout.strip() else -1
    except Exception as e:
        logging.error(f"FFmpeg failed to determine video duration: {e}")
        return -1  # Return -1 if failed


def get_video_fps(video_path):
    """Gets the frame rate (FPS) of a video using FFmpeg's ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        fps_str = result.stdout.strip()

        # Convert fractional FPS (e.g., 24000/1001) to float
        if '/' in fps_str:
            num, denom = map(int, fps_str.split('/'))
            return float(num / denom) if denom != 0 else -1
        return float(fps_str) if fps_str else -1

    except Exception as e:
        logging.error(f"FFmpeg failed to determine FPS: {e}")
        return -1  # Return -1 if failed

