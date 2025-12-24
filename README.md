Presentation to Lecture Video Generator
An AI-powered tool that converts PowerPoint presentations into narrated video lectures with multi-language support. The system uses Google Gemini AI to generate context-aware explanations and supports both premium (Google Cloud TTS) and free (gTTS) text-to-speech engines.

Features
AI-Powered Narration: Uses Google Gemini to generate coherent, context-aware explanations across slides
Multiple Narration Styles: Choose from 5 different presentation styles (Professional, Engaging, Enthusiastic, Casual, Storyteller)
Multi-Language Support: Translate content to 10+ languages with DeepL (premium) or Google Translate (free)
Dual TTS Options: 
-Google Cloud TTS (premium neural voices with gender selection)
-gTTS (free, basic quality)
Legacy Support: Automatically converts old .ppt files to .pptx format
Modern GUI: Built with Flet for a sleek, user-friendly interface

 Workflow
1.Upload a PowerPoint file (.pptx or .ppt)
2.AI Analysis: Gemini generates context-aware narration for each slide
3.Translation: Content is translated to your target language
4.TTS Generation: Audio narration is created from translated text
5.Video Export: Final video with synchronized slides and audio


 Requirements
System Requirements
Operating System: Windows (required for PowerPoint COM automation)
Python: 3.8 or higher
PowerPoint: Microsoft PowerPoint must be installed

API Keys (Required)
Google Gemini API Key: For AI narration generation
DeepL API Key (optional): For premium translation quality
Google Cloud TTS Credentials : For premium voice quality


 Installation
1. Clone the Repository
git clone <repository-url>
cd presentation-to-lecture

3. Install Python Dependencies
Core Dependencies
pip install flet
pip install python-pptx
pip install pywin32
pip install python-dotenv
pip install google-genai
pip install gtts
pip install moviepy
pip install Pillow
Translation Dependencies
# Option 1: Premium translation (recommended)
pip install deepl
# Option 2: Free translation alternatives
pip install deep-translator
pip install googletrans==3.1.0a0
Optional: Google Cloud TTS (Premium Voice)
pip install google-cloud-texttospeech
All-in-One Installation
pip install flet python-pptx pywin32 python-dotenv google-genai gtts moviepy Pillow deepl deep-translator googletrans==3.1.0a0 google-cloud-texttospeech

3. Set Up Environment Variables
Create a .env file in the project root directory:
# Required: Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here
# Optional: DeepL API Key (for premium translation)
DEEPL_API_KEY=your_deepl_api_key_here
# Optional: Google Cloud credentials path (for premium TTS)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json

Important Notes:
The .env file should NEVER be committed to Git
Share the .env file securely with team members (encrypted email, secure file sharing, etc.)
Each team member should place their .env file in the project root

4. Obtain API Keys

Google Gemini API Key (Required)
1.Go to Google AI Studio
2.Create a new API key
3.Add it to your .env file as GOOGLE_API_KEY

DeepL API Key (Optional)
1.Sign up at DeepL API
2.Get your API key from the account dashboard
3.Add it to your .env file as DEEPL_API_KEY

Google Cloud TTS (Optional)
1.Create a project in Google Cloud Console
2.Enable the Cloud Text-to-Speech API
3.Create a service account and download the JSON credentials
4.Add the path to your .env file as GOOGLE_APPLICATION_CREDENTIALS

 Usage
Running the Application
python main.py


Step-by-Step Guide
1.Launch the Application: Run main.py
2.Upload File: Click or drag-and-drop a .pptx or .ppt file
3.Choose Narration Style: Select from 5 AI narration styles
4.Select Voice Quality: Choose between Cloud TTS (premium) or gTTS (free)
5.Choose Voice Gender: Select Male or Female (for Cloud TTS only)
6.Select Target Language: Choose your desired output language
7.Start Conversion: Click "START CONVERSION" and monitor the terminal output
8.Open Result: Once complete, click "OPEN FOLDER" to view your video
Supported Languages
English
Turkish
German
French
Spanish
Italian
Russian
Japanese
Korean
Chinese (Simplified)


 Narration Styles
1.Professional Lecturer: Formal, academic tone (temperature: 0.5)
2.Engaging Teacher: Conversational and friendly (temperature: 0.7)
3.Enthusiastic Presenter: Energetic and passionate (temperature: 0.8)
4.Casual Explainer: Relaxed with everyday language (temperature: 0.7)
5.Story Teller: Narrative-driven storytelling (temperature: 0.8)
 Project Structure
presentation-to-lecture/
├── main.py                      # Main GUI application
├── ai_narrator.py               # Gemini AI narration generation
├── translator.py                # Multi-service translation
├── tts_generator.py             # Free TTS (gTTS)
├── cloud_tts_generator.py       # Premium TTS (Google Cloud)
├── video_generator.py           # Video rendering with FFmpeg
├── pptx_reader.py               # PowerPoint text extraction
├── ppt_converter.py             # Legacy .ppt conversion
├── config.py                    # Configuration management
├── .env                         # API keys (NOT in Git)
├── .env.example                 # Template for .env
├── requirements.txt             # Python dependencies
└── output/                      # Generated files
    ├── *.json                   # Slide data with translations
    ├── *_audio/                 # Generated audio files
    ├── *_images/                # Exported slide images
    └── *_video.mp4              # Final video output


    
 Troubleshooting
 
Common Issues
"No API key found!"
Ensure your .env file exists in the project root
Verify the file is named exactly .env (not .env.txt)
Check that GOOGLE_API_KEY is correctly set
"This application requires Windows"
PowerPoint COM automation only works on Windows
Consider using a Windows VM or WSL2 if on Mac/Linux
"pywin32 is not installed"
pip install pywin32

Translation Errors
If DeepL fails, the system automatically falls back to free alternatives
Check your DEEPL_API_KEY if using premium translation

Cloud TTS Not Available
Ensure google-cloud-texttospeech is installed
Verify GOOGLE_APPLICATION_CREDENTIALS points to a valid JSON file
The system will fall back to gTTS if Cloud TTS fails

Video Rendering Issues
Ensure FFmpeg is installed and in your system PATH
MoviePy may require additional codecs on some systems

 Team Setup
For New Team Members
1.Clone the repository
2.Install dependencies: pip install -r requirements.txt
3.Get the .env file from your team lead (via secure channel)
4.Place .env in the project root
5.Run: python main.py
For Team Leads
1.Create a template .env.example without actual keys
2.Share the actual .env file securely (never via Git)
3.Document any project-specific API key requirements
4.Add .env to .gitignore to prevent accidental commits

 Output Files
Each conversion generates:
*_en_YYYYMMDD_HHMMSS.json - Slide data with AI narrations and translations
*_audio/ - Individual MP3 files for each slide
*_images/ - PNG exports of each slide (with translations applied)
*_video.mp4 - Final rendered video lecture

 Security Notes
Never commit .env files to version control
Never share API keys in plain text via insecure channels
Regularly rotate API keys for production use
Use environment variables for deployment environments

 Known Limitations
Windows-only (PowerPoint COM requirement)
Large presentations may take time to process
Translation quality depends on the service used
Video encoding requires significant CPU resources


 Dependencies Summary
 
Package           	      |       Purpose                   |	Required
flet	                    | GUI framework	                  |   Yes
python-pptx               |	PowerPoint reading	            |   Yes
pywin32     	            | PowerPoint COM automation	      |   Yes (Windows)
python-dotenv             | Environment variable management	|   Yes
google-genai	            | Gemini AI narration	            |   Yes
gtts	                    | Free text-to-speech	            |   Yes
moviepy	                  | Video rendering	                |   Yes
Pillow	                  | Image processing	              |   Yes
deepl	                    | Premium translation	            | Optional
deep-translator	          | Free translation	              | Optional
google-cloud-texttospeech |	Premium TTS	                    | Optional
