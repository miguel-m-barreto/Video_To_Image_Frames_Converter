import os
import argparse
import time
import subprocess
import math
import logging
import datetime

from utils import (
    format_time, find_video, get_unique_output_folder, get_timestamp_output_folder, 
    round_floor_decimals, round_ceiling_decimals,
    trim_video, convert_video_to_lossless, get_video_frame_count, supported_formats
)

supported_given_image_format = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff']

"""
SETUP LOGGING
"""
# Setup logging to store error messages
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

# Generate log filename with timestamp
log_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_path = os.path.join(log_folder, log_filename)

# Configure logging
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,  # Change to DEBUG for more details
    format="%(asctime)s - %(levelname)s - %(message)s",
)

"""
AUXILIARY FUNCTIONS FOR VIDEO TO JPG CONVERSION
"""
# Get the video path
def get_video_path(video_path):
    # If no video path is provided, search for it in the directory and subdirectories
    if video_path is None or not os.path.exists(video_path):
        print("No valid video file provided. Searching in the current directory and subdirectories...")
        found_video = find_video(video_path if video_path else "", os.getcwd())
        if found_video:
            video_path = found_video
            print(f"Found video: {os.path.relpath(video_path, os.getcwd())}")
        else:
            print("No video files found.")
            return
    else:
        print(f"Using provided video path: {os.path.relpath(video_path, os.getcwd())}")

    return video_path

# Calculate the frame interval based on the FPS and seconds interval
# Ensure the frame interval is at least 1
# get's interval type based on the provided interval
def get_interval_type(given_frames_interval, given_seconds_interval, fps):
    """Get the interval type based on the provided interval."""
    if given_seconds_interval is not None:
        return given_seconds_interval, f"{given_seconds_interval}s_interval"
    elif given_frames_interval > 1:
        return given_frames_interval, f"{given_frames_interval}_frames_interval"
    else:
        return given_frames_interval, f"{given_frames_interval}_given_frame_interval"

# Get the output folder path
# If no output folder is provided, create a folder in the current directory
# If timestamps are enabled create a timestamped folder inside the default location
def get_output_folder(output_folder, video_name, interval_type, enable_timestamp_folder):
    if output_folder is None:
        if not os.path.exists(os.path.join(os.getcwd(), "Video_converter_Folder")):
                os.makedirs(os.path.join(os.getcwd(), "Video_converter_Folder"), exist_ok=True)
    else:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

    if enable_timestamp_folder:
        if output_folder is None:
            # If no output folder is provided, create a timestamped folder inside the default location
            return get_timestamp_output_folder(
                os.path.join(
                    os.getcwd(), 
                    "Video_converter_Folder", 
                    f"{video_name}_frames_{interval_type}"))
        else:
            # If an output folder is provided, create a timestamped subfolder inside it
            parent_folder_name = os.path.basename(os.path.normpath(output_folder))  # Get the last folder name
            return get_timestamp_output_folder(os.path.join(output_folder, f"{parent_folder_name}_{video_name}_frames_{interval_type}"))
    else:
        if output_folder is None:
            base_output_folder = os.path.join(
                os.getcwd(),
                "Video_converter_Folder",
                f"{video_name}_frames_{interval_type}"
            )
            return get_unique_output_folder(base_output_folder) or base_output_folder  # Ensure a valid folder path
        else:
            return get_unique_output_folder(output_folder) or output_folder  # Ensure a valid folder path

# Set the start_time and end_time frame based on the provided frame number or time
# Default to the start_time of the video if the provided start_time frame or time exceeds the video duration
def get_start(given_start_frame, given_start_time, 
              frame_count, fps, dur):
    """Set the start_time frame based on the provided frame number or time."""
    start_time = 0

    if given_start_time is not None:
        if given_start_time > dur:
            print(f"start_time time {given_start_time}s exceeds video duration. Total time in video: {dur}s, defaulting to start time of video.")
        else:
            start_time = given_start_time

    elif given_start_frame is not None:
        if given_start_frame > frame_count:
            print(f"start_time frame {given_start_frame} exceeds total frames. Total frames in video: {frame_count}, defaulting to the first frame of video.")
        else:
            start_time = given_start_frame / fps

    return start_time

# Default to the end_time of the video if the provided end_time frame or time exceeds the video duration 
def get_end(given_end_frame, given_end_time,
              frame_count, fps, dur):
    """Set the end_time frame based on the provided frame number or time."""
    end_time = dur

    if given_end_time is not None:
        if given_end_time > dur:
            print(f"end_time time {given_end_time}s exceeds video duration. Total time in video: {dur}s, defaulting to end time of video.")
        else:
            end_time = given_end_time

    elif given_end_frame is not None:
        if given_end_frame > frame_count:
            print(f"end_time frame {given_end_frame} exceeds total frames. Total frames in video: {frame_count}, defaulting to end time of video.")
        else:
            end_time = given_end_frame / fps

    return end_time

"""
MAIN FUNCTION FOR VIDEO TO IMAGES CONVERSION
"""
# Convert a video to JPG frames
def video_converter(video_path, output_folder=None, 
                 given_start_frame=None, given_end_frame=None, 
                 given_start_time=None, given_end_time=None, 
                 given_frames_interval=1, given_seconds_interval=None, 
                 enable_lossless=False, disable_checking_existing_frames=False, enable_timestamp_folder=False, 
                 given_image_format="jpg"):
    
    """
    Converts a video into a sequence of JPG frames, skipping already existing frames.
    Provides estimated time completion.
    """ 

    start_exec = time.time()

    logs_folder = os.path.join(os.getcwd(), "logs")

    if logs_folder is None:
        os.makedirs(logs_folder, exist_ok=True)

    # Get the video path
    video_path = get_video_path(video_path)
    # Check if a valid video file is found
    if video_path is None:
        print("Error: No valid video file found.")
        return
    
    # Check if the file format is supported
    if not any(video_path.lower().endswith(ext) for ext in supported_formats):
        print("Unsupported video format.")
        return

    # Check if the image exists in the supported image formats
    if given_image_format is None:
        given_image_format = "jpg"
    elif given_image_format.lower() not in supported_given_image_format:
        print("Unsupported image format.")
        logging.error("Unsupported image format.")
        return

    dur, frame_count, fps = get_video_frame_count(video_path)

    if dur < 0 or frame_count < 0 or fps < 0:
        print("Error: Invalid video properties.")
        logging.error("Invalid video properties.")
        return
    
    # TO DELETE: this print
    # Print video duration, frame count, and FPS
    print("-----------------------------"
        f"\nTotal video duration: {format_time(dur)} = {dur} seconds"
        f"\nTotal frames in video: {frame_count}" 
        f"\nVideo FPS: {fps:.3f}")

    interval, interval_type = get_interval_type(given_frames_interval, given_seconds_interval, fps)

    # Set the start_time frame based on the provided frame number or time
    start_time = get_start(given_start_frame, given_start_time, frame_count, fps, dur)
    end_time = get_end(given_end_frame, given_end_time, frame_count, fps, dur)

    # Swap start_time and end_time if start_time is greater than end_time
    if start_time == end_time:
        print("Warning: start_time time is equal to end_time time. \nDefaulting to start of the video.")
        start_time = 0
    elif start_time > end_time:
        print("Warning: start_time time is greater than end_time time. \nSwapping start_time and end_time.")
        start_time, end_time = end_time, start_time

    remaining_frames = max(frame_count, math.ceil(((end_time - start_time) * round_ceiling_decimals(fps, 2)) / interval))

    if start_time > 0 or end_time < dur:
        # Trim the video to the specified start_time and end_time
        trim_time = time.time()
        print("-----------------------------"
            f"\nTrimming video from {video_path}")
        print(f"Trimming video from {start_time} to {end_time} seconds.")            
        video_path = trim_video(video_path, start_time, end_time)
        print(f"Trimmed video saved: {video_path}")
        
        dur, frame_count, fps = get_video_frame_count(video_path)

        # TO DELETE: this print
        # Print video duration, frame count, and FPS
        elapsed_trim_time = time.time() - trim_time
        print("-----------------------------"
            f"\nTrimmed video duration: {format_time(dur)} = {dur} seconds"
            f"\nTrimmed frames in video: {frame_count}" 
            f"\nVideo FPS: {fps:.3f}"
            f"\nTrimming time taken: {format_time(elapsed_trim_time)}")
        
        remaining_frames = frame_count

    # Convert video to lossless format
    if enable_lossless:
        video_path = convert_video_to_lossless(video_path)

    # Extract video name without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    # Get the output folder path
    output_folder = get_output_folder(output_folder, video_name, interval_type, enable_timestamp_folder)

    os.makedirs(output_folder, exist_ok=True)
    
    # Preload existing frame filenames into a set
    #existing_files = get_existing_filenames(output_folder) if not disable_checking_existing_frames else set()

    # Define FFmpeg filter for frame extraction
    # Extract frames at the specified interval, or at the exact FPS rate
    # The filter is applied to the video stream to extract frames
    if given_seconds_interval is not None:
        if given_seconds_interval <= 0:
            print("Error: Seconds interval must be greater than 0.")
            logging.error("Seconds interval must be greater than 0.")
            return
        else:
            fps_filter = f"fps=1/{interval}" if interval > 1 else f"fps=1"
    else:
        if interval <= 0:
            print("Error: Frame interval must be greater than 0.")
            logging.error("Frame interval must be greater than 0.")
            return
        else:
            fps_filter = f"fps={fps/interval}" if interval > 1 else f"fps={fps}"

    # Set the start_time and end_time frame positions
    #start_option = f"-ss {start_time}"
    #end_option = f"-to {end_time}"
    
    output_pattern = os.path.join(output_folder, f"frame_%04d.{given_image_format}")
    
    # FFmpeg Command (Fully Replaces OpenCV)
    #command = f'ffmpeg -y {start_option} -i "{video_path}" {end_option} -vsync vfr -vf "{fps_filter}" "{output_pattern}"'
    command = ["ffmpeg", "-y", "-accurate_seek"]
    if not disable_checking_existing_frames:
        command.append("-n")
    
    command.extend(["-i", video_path, "-fps_mode", "passthrough", "-vf", fps_filter,])

    if given_image_format == "png":
        command.extend(["-compression_level", "100"])
    else:
        command.extend(["-q:v", "1", "-vsync", "vfr", "-pix_fmt", "yuvj420p"])
    
    command.append(output_pattern)

    """ 
    if given_image_format == "png":
            command = [
                "ffmpeg", "-y", "-i", video_path,
                "-fps_mode", "passthrough", "-vf", fps_filter, "-compression_level", "100", output_pattern
            ]
        #else:
            command = [
                "ffmpeg", "-y", "-i", video_path,
                "-fps_mode", "passthrough", "-vf", fps_filter, "-q:v", "1", "-vsync", "vfr",
                "-pix_fmt", "yuvj420p", output_pattern
            ]
    else:
        if given_image_format == "png":
                command = [
                    "ffmpeg", "-y", "-n", "-i", video_path,
                    "-fps_mode", "passthrough", "-vf", fps_filter, "-compression_level", "100", output_pattern
                ]
        else:
                command = [
                    "ffmpeg", "-y", "-n", "-i", video_path,
                    "-fps_mode", "passthrough", "-vf", fps_filter, "-q:v", "1", "-vsync", "vfr",
                    "-pix_fmt", "yuvj420p", output_pattern
                ]
    """

    # TO DELETE: this print
    # Print information about the video extraction
    print("-----------------------------"
        f"\nFrames to process: {remaining_frames}"
        f"\nStart_time time: {start_time}"
        f"\nEnd_time time: {end_time}"
        f"\nVideo time to process to images: {format_time(end_time - start_time)}")

    start_ffmpeg_time = time.time()
    try:
        print(f"{command}")
        print("Running FFmpeg command...")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            logging.error(f"FFmpeg error: {result.stderr}")
            return
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg frame extraction failed: {e}")
        print("Error: FFmpeg frame extraction failed.")

    # Count saved frames
    processed_frames = len([f for f in os.listdir(output_folder) if f.endswith(given_image_format)])
    elapsed_time = time.time() - start_exec
    elapsed_time_ffmpeg = time.time() - start_ffmpeg_time

    # TO DELETE: this print
    # Print final message, including the time taken and FPS, and log the results to a file
    print("-----------------------------"
        f"\nExtraction Ended!"
        f"\nSaved frames in {output_folder} with an interval of {interval_type}."
        f"\nTotal time taken: {format_time(elapsed_time)}"
        f"\nFFmpeg time taken: {format_time(elapsed_time_ffmpeg)}"
        f"\nFPS: {processed_frames / elapsed_time:.2f}" 
        "\n-----------------------------")

    if processed_frames != remaining_frames:
        logging.error(f"Expected frames: {remaining_frames}, frames processed: {processed_frames}, FPS: {fps}, Duration: {format_time(end_time - start_time)} = {end_time - start_time} seconds")
        print(f"ERROR: Expected frames: {remaining_frames}, frames processed: {processed_frames} \nFPS: {fps}, Duration: {format_time(end_time - start_time)} = {end_time - start_time} seconds")
    else:
        logging.info(f"Extraction Completed Successfuly! Expeected frames: {remaining_frames}, Frames processed: {processed_frames}, FPS: {fps}, Duration: {format_time(end_time - start_time)} = {end_time - start_time} seconds")
        print(f"Extraction Completed Successfuly! \nExpected frames: {remaining_frames}, Frames processed: {processed_frames} \nFPS: {fps}, Duration: {format_time(end_time - start_time)} = {end_time - start_time} seconds")

    print(f"Log file: {log_path}" 
        "\n-----------------------------")

# Command-line interface
# Extract frames from a video and save as JPEG images
# time in seconds is prioritized over frame number
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from a video and save as JPEG images.")
    parser.add_argument("video", help='Path to the video file (wrap in "quotes" if it contains spaces)')
    parser.add_argument("--output_folder", help="Path to the output folder", default=None)
    parser.add_argument("--start_frame", type=int, help="start_time frame number", default=None)
    parser.add_argument("--end_frame", type=int, help="end_time frame number", default=None)
    parser.add_argument("--start_time", type=int, help="start_time time in seconds", default=None)
    parser.add_argument("--end_time", type=int, help="end_time time in seconds", default=None)
    parser.add_argument("--frames_interval", type=int, help="Frame interval to extract frames", default=1)
    parser.add_argument("--seconds_interval", type=float, help="Extract frames every X seconds", default=None)
    parser.add_argument("--enable_lossless", action="store_true", help="Enable lossless conversion (default is enabled)")
    parser.add_argument("--disable_checking_existing_frames", action="store_true", help="Stop Checking for duplicate frames to skip them")
    parser.add_argument("--enable_timestamp_folder", action="store_true", help="Save frames in a folder with a timestamp")
    parser.add_argument("--image_format", choices=supported_given_image_format, help="Output image format (default: jpg)",  default="jpg")

    args = parser.parse_args()
    
    video_converter(args.video, args.output_folder, args.start_frame, args.end_frame, args.start_time, args.end_time, args.frames_interval, args.seconds_interval, args.enable_lossless, args.disable_checking_existing_frames, args.enable_timestamp_folder, args.image_format)