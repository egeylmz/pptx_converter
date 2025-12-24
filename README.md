# Presentation to Lecture Video Generator

This application is an AI-powered tool designed to convert PowerPoint presentations into narrated video lectures with multi-language support. The system leverages Google Gemini AI to generate context-aware explanations and supports both premium (Google Cloud TTS) and free (gTTS) text-to-speech engines. 

## Key Features

* *AI-Powered Narration:* Utilizes Google Gemini to generate coherent, context-aware explanations for each slide.
* *Multiple Narration Styles:* Offers five distinct presentation styles: Professional, Engaging, Enthusiastic, Casual, and Storyteller.
* *Multi-Language Support:* Translates content into over 10 languages using DeepL (premium) or Google Translate (free).
* *Dual TTS Options:*
* *Google Cloud TTS:* Premium neural voices with gender selection.
* *gTTS:* Free, standard quality text-to-speech.


* *Legacy Support:* Automatically converts older .ppt files to the modern .pptx format.
* *Modern GUI:* Developed with Flet to provide a user-friendly interface.

## Workflow

1. *Upload:* The user inputs a PowerPoint file (.pptx or .ppt).
2. *AI Analysis:* Gemini analyzes the content and generates context-aware narration for each slide.
3. *Translation:* The generated narration is translated into the target language.
4. *TTS Generation:* Audio narration is generated from the translated text.
5. *Video Export:* A final video (.mp4) is rendered, synchronizing the slides with the audio.

## Prerequisites

### System Requirements

* *Operating System:* Windows (Required for PowerPoint COM automation).
* *Python:* Version 3.8 or higher.
* *Software:* Microsoft PowerPoint must be installed.

### API Keys

* *Google Gemini API Key:* Required for AI narration generation.
* *DeepL API Key:* Optional (Required only for premium translation).
* *Google Cloud Credentials:* Optional (Required only for premium TTS).

## Installation

### 1. Clone the Repository

bash
git clone <repository-url>
cd presentation-to-lecture



### 2. Install Dependencies

You may install the core dependencies and choose your preferred translation/TTS packages.

*All-in-One Installation:*

bash
pip install flet python-pptx pywin32 python-dotenv google-genai gtts moviepy Pillow deepl deep-translator googletrans==3.1.0a0 google-cloud-texttospeech



*Core Dependencies Only:*

bash
pip install flet python-pptx pywin32 python-dotenv google-genai gtts moviepy Pillow



### 3. Environment Configuration

Create a .env file in the project root directory. Do not commit this file to version control.

```ini
*Required: Google Gemini API Key*
GOOGLE_API_KEY=your_gemini_api_key_here

*Optional: DeepL API Key (for premium translation)*
DEEPL_API_KEY=your_deepl_api_key_here

*Optional: Google Cloud credentials path (for premium TTS)*
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```


## Usage

### Running the Application

Execute the main script to launch the GUI:

bash
python main.py



### Operational Steps

1. *Launch:* Run the application script.
2. *Upload:* Click or drag-and-drop a .pptx or .ppt file into the interface.
3. *Configuration:*
* Select a *Narration Style* (e.g., Professional, Engaging).
* Select *Voice Quality* (Cloud TTS or gTTS).
* Select *Voice Gender* (Available for Cloud TTS).
* Select *Target Language*.


4. *Convert:* Click "START CONVERSION" and monitor the terminal for progress.
5. *View:* Upon completion, click "OPEN FOLDER" to access the generated video.

### Supported Languages

* English, Turkish, German, French, Spanish, Italian, Russian, Japanese, Korean, Chinese (Simplified).

### Narration Styles

* *Professional Lecturer:* Formal, academic tone (Temperature: 0.5).
* *Engaging Teacher:* Conversational and friendly (Temperature: 0.7).
* *Enthusiastic Presenter:* Energetic and passionate (Temperature: 0.8).
* *Casual Explainer:* Relaxed with everyday language (Temperature: 0.7).
* *Story Teller:* Narrative-driven structure (Temperature: 0.8).

## Project Structure

```text
presentation-to-lecture/
├── main.py                     # Main GUI application
├── ai_narrator.py              # Gemini AI narration generation
├── translator.py               # Multi-service translation logic
├── tts_generator.py            # Free TTS (gTTS) implementation
├── cloud_tts_generator.py      # Premium TTS (Google Cloud) implementation
├── video_generator.py          # Video rendering via FFmpeg
├── pptx_reader.py              # PowerPoint text extraction
├── ppt_converter.py            # Legacy .ppt conversion utility
├── config.py                   # Configuration management
├── .env                        # API keys (Excluded from Git)
├── .env.example                # Template for environment variables
├── requirements.txt            # Python dependencies
└── output/                     # Generated files directory
    ├── *.json                  # Slide data with translations
    ├── *_audio/                # Generated audio files per slide
    ├── *_images/               # Exported slide images
    └── *_video.mp4             # Final rendered video
```


## Troubleshooting

* *"No API key found!":* Ensure the .env file exists in the root directory and GOOGLE_API_KEY is set.
* *"This application requires Windows":* PowerPoint COM automation is strictly a Windows feature. Use a Windows VM if working on macOS or Linux.
* *Translation Errors:* If DeepL fails or is not configured, the system defaults to free alternatives.
* *Cloud TTS Not Available:* Ensure google-cloud-texttospeech is installed and the GOOGLE_APPLICATION_CREDENTIALS path is valid.
* *Video Rendering:* Ensure FFmpeg is installed and accessible in your system PATH.

## Team Setup & Security

* *Team Access:* Share the .env contents securely (e.g., via encrypted email). Never commit .env files to Git.
* *Setup:* New members should clone the repo, install requirements, and place the provided .env file in the root.
* *Security:* Regular rotation of API keys is recommended for production environments.

## Dependencies

| Package | Purpose | Requirement Status |
| --- | --- | --- |
| *flet* | GUI framework | Required |
| *python-pptx* | PowerPoint reading | Required |
| *pywin32* | PowerPoint COM automation | Required (Windows) |
| *python-dotenv* | Environment variable management | Required |
| *google-genai* | Gemini AI narration | Required |
| *gtts* | Free text-to-speech | Required |
| *moviepy* | Video rendering | Required |
| *Pillow* | Image processing | Required |
| *deepl* | Premium translation | Optional |
| *deep-translator* | Free translation | Optional |
| *google-cloud-texttospeech* | Premium TTS | Optional |
