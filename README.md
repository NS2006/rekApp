# 🎥 RekApp - AI Video Summarizer

**RekApp** is an intelligent web application that automatically generates concise summaries from video files. By leveraging computer vision and natural language processing, it extracts audio from videos, transcribes the speech to text, and uses advanced AI models to provide a digestible summary of the content. And it also supports **Direct Text Summarization** for users who already have transcripts.

---

## 🚀 Live Demo

Check out the running application on Hugging Face Spaces:

👉 **[Try RekApp Live Here](https://huggingface.co/spaces/NSutiono/rekApp)**

---

## ✨ Features

* **🎬 Video Summarization:** Upload video files (MP4, AVI, MOV, MKV, WEBM) to get an automatic summary.
* **📝 Direct Text Input:** Paste long articles or transcripts directly to generate summaries instantly.
* **🔊 Audio Extraction:** Automatically extracts and processes audio from video files using `moviepy` and `librosa`.
* **🧠 AI-Powered:** Uses deep learning models (PyTorch/Transformers) for accurate abstractive summarization.
* **📊 Real-time Progress:** Visual progress bar tracking loading, extraction, transcription, and summarization steps.
* **📱 Responsive UI:** Clean, modern interface with tabbed inputs for easy navigation.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **AI/ML:** PyTorch, Transformers (Hugging Face)
* **Media Processing:** MoviePy, Librosa, FFmpeg
* **Deployment:** Docker, Hugging Face Spaces

---

## 📂 Project Structure

```text
rekApp/
├── app.py                  # Main Flask application entry point
├── Dockerfile              # Docker configuration for deployment
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css       # Application styling
│   └── js/
│       └── script.js       # Frontend logic (drag & drop, progress polling)
├── templates/
│   ├── home.html           # Upload Page
│   ├── index.html           # Landing page
│   ├── processing.html     # Progress tracking page
│   └── result.html         # Final result page
├── utils/
│   ├── video_processor.py  # Audio extraction & transcription logic
│   └── summarizer.py       # AI Summarization model logic
└── model/                # Model
```

## 💻 How to Run Locally

You can run RekApp on your local machine using **Docker**.

### Using Docker 
This is the easiest way to run the app. Docker automatically handles all system dependencies (like FFmpeg and C++ compilers).

#### Prerequisites
* **Git** installed.
* **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux) installed and running.

#### Steps
1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/NS2006/rekApp.git](https://github.com/NS2006/rekApp.git)
    cd rekApp
    ```

2.  **Build the Image**
    *Note: This may take a few minutes as it compiles necessary libraries.*
    ```bash
    docker build -t rekapp .
    ```

3.  **Run the Container**
    ```bash
    docker run -p 7860:7860 rekapp
    ```

4.  **Access the App**
    Open your browser and go to: `http://localhost:7860`

---