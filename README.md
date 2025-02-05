# Video to Image Frames Converter

**A powerful and easy-to-use script that extracts frames from videos and saves them as images.**  
Perfect for **content creators, video analysts, and developers** who need high-quality frame extraction.

---

## **Features**
- **Auto-detects video files inside the folder if only name is given and path is not specified**  
- **Automatically prevents duplicate frame extraction**
- **Creates video output folder if none is specified**
- **Enables lossless frame extraction for highest quality** (via **FFmpeg**)  
- **Enables creation of timestamped folders for better organization**
- **Extract frames based on time (`seconds_interval`) or frame count (`frames_interval`)**
- **Saves images in multiple formats** (`jpg`, `png`, `webp`, `bmp`, `tiff`)    
- **Supports multiple video formats** (`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`)  

---

## **Installation**
Make sure you have **Python or Python 3.x** installed along with the following dependencies.
### **Requirements**

### **Install Python (Required)**

- **Windows and MacOS**: Go to https://www.python.org/downloads/ and download the latest version, then

  ```bash
  python get-pip.py
  ```
  
- **Ubuntu/Debian**: By default, Ubuntu already has Python available. But if you want to install a specific version of Python:
  &nbsp;

  Check the default Python version on Ubuntu.
  ```bash
  python3 --version
  ```
  &nbsp;
  ***If the version you want is incorrect:***
  &nbsp;
  
  1. Update software packages in Ubuntu.
  ```bash
  sudo apt update
  ```
  
  2. Install Python on Ubuntu: Change X.XX to the version you want.
  ```bash
  sudo apt install pythonX.XX
  ```
  
  3. Install Pip on Ubuntu
  ```bash
  sudo apt install python3-pip
  ```

### **Install FFmpeg (Required)**
- **Windows**: Use pip command or download from [FFmpeg Official Site](https://ffmpeg.org/download.html)

  ```bash
  pip install ffmpeg-python
  ```

- **Ubuntu/Debian**: compilation guide - https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu
  &nbsp
  Update repository
  ```bash
    sudo apt update && sudo apt upgrade
  ```
  &nbsp
  Install FFmpeg
  ```bash
    sudo apt install ffmpeg
  ```

- **macOS (Homebrew)**:

  ```bash
  brew install ffmpeg
  ```

### **Install OpenCV (Required)**
- **Windows**: Use pip command or download from [FFmpeg Official Site](https://ffmpeg.org/download.html)
   
  ```bash
  pip install opencv-python
  ```

- **Ubuntu/Debian**: tutorial - https://docs.opencv.org/4.x/d2/de6/tutorial_py_setup_in_ubuntu.html

  ```bash
  sudo apt-get install python3-opencv
  ```

- **macOS (Homebrew)**: tutorial - https://docs.opencv.org/4.x/d0/db2/tutorial_macos_install.html

  ```bash
  brew install opencv
  ```

---

## **Usage**
### **Command-Line Usage**
Run the script with a video file to extract frames:

```bash
python video_converter.py input_video.mp4
```

### **Available Arguments**
| Argument | Description | Example |
|----------|------------|---------|
| `--output_folder` | Folder to save extracted frames | `--output_folder FOLDER_PATH` |
| `--start_time` | Start time in seconds | `--start_time 10` |
| `--end_time` | End time in seconds | `--end_time 30` |
| `--frames_interval` | Extract every X frames | `--frames_interval 5` |
| `--seconds_interval` | Extract every X seconds | `--seconds_interval 2` |
| `--image_format` | Output format (`jpg`, `png`, `webp`, etc.) | `--image_format png` |
| `--enable_lossless` | Convert video into lossless format for better quality and avoid corruption | `--enable_lossless` |
| `--enable_timestamp_folder` | Save images in a timestamped folder | `--enable_timestamp_folder` |


---

## **How It Works**
1. The script **reads the video file** and determines its **frame count, FPS, and duration**.
2. Based on the **chosen extraction method** (`frame interval` or `time interval`), it calculates which frames to extract.
3. Uses **FFmpeg** (for best performance) or **OpenCV** as a fallback to extract frames.
4. Saves frames in the **output folder**, naming them sequentially (`frame_0001.jpg`, `frame_0002.jpg`).
5. **Prevents duplicate frame extraction** by checking for existing files.
    
---

## **Example Uses**
### **Extract one frame every 5 seconds and save as PNG:**
```bash
python video_converter.py input.mp4 --seconds_interval 5 --image_format png
```
### **Extract frames between 10s and 30s of the video:**
```bash
python video_converter.py input.mp4 --start_time 10 --end_time 30
```
### **Extract every 10th frame as JPG:**
```bash
python video_converter.py input.mp4 --frames_interval 10 --image_format jpg
```

---


## **Troubleshooting**
### **FFmpeg Not Found?**
Check if FFmpeg is installed:

```bash
ffmpeg -version
```

If missing, install it from **[FFmpeg’s official site](https://ffmpeg.org/download.html)**.

### **Video File Not Found?**
Ensure the file path is correct, or place the video in the script's directory to be auto-detected.

### **Unsupported Video Format?**
Supported formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`.  

---

## **License**
This software is licensed under a **Custom Source-Available License**:

- You **can use this software freely**, including for YouTube, content creation, and personal projects.
- You **can share it**, but **must credit the author**.
- **You cannot modify, sell, or redistribute it without permission.**

**For full terms, see the [LICENSE](LICENSE) file.**

Copyright (C) 2025 Miguel Matos Barreto  

---

## **Acknowledgments**
- Built using **OpenCV, FFmpeg, and Python**.

---

## **Contact**
For special permissions, support, or business inquiries, contact:  
**Email:** ***I'll add it later***  
**GitHub** ***I'll add it later***
**Portfolio Link** ***I'll add it later***
**WebSite** ***I'll add it later***

---

## Future Improvements
GUI Version: A graphical user interface for easier usage, maybe web based.
Multi-threading Support: To improve extraction speed, in progress.

## TODO
- Convert video to other formats, can be done using:

```bash
ffmpeg -i input.video output.mp4
```

Incorporate this in the code.

- **Automatically prevents duplicate frame extraction** check this functionality

