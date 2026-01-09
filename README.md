# AI Article Generator

A web application that uses AI to generate articles on any topic in multiple languages. Features include article editing and downloading in TXT, DOC, and PDF formats. For Chinese articles, Pinyin is automatically added to difficult characters for elementary students.

## Features

- 🤖 AI-powered article generation using OpenAI GPT models
- 🌍 Support for multiple languages (English, Chinese, Spanish, French, German, Japanese, Korean)
- 📝 Customizable word count (100-5000 words)
- ✏️ In-browser article editing
- 📥 Download articles in TXT, DOC, or PDF formats
- 🈶 Automatic Pinyin annotation for difficult Chinese characters (elementary level)

## Prerequisites

- Python 3.11
- Conda (for environment management)
- OpenAI API key

## Setup

1. **Activate the conda environment:**
   ```bash
   conda activate composition
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
   
   Or create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Running the Application

1. **Start the Flask server:**
   ```bash
   python app.py
   ```

2. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

## Usage

1. Enter a topic for your article
2. Select the desired language
3. Specify the total word count
4. Click "Generate Article"
5. Edit the article if needed
6. Download in your preferred format (TXT, DOC, or PDF)

## Project Structure

```
composition/
├── app.py              # Flask backend application
├── templates/
│   └── index.html     # Frontend HTML/CSS/JS
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Notes

- The application uses OpenAI's GPT-4o-mini model for article generation
- Chinese articles automatically include Pinyin annotations for characters that are typically difficult for elementary students
- The word count is approximate and may vary slightly depending on the language and topic

## License

This project is open source and available for personal and educational use.

