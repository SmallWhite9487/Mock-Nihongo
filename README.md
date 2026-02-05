# Mock Nihongo
    - AI-powered Japanese exam practice

A lightweight Python application for generating and practicing mock Japanese exams (JLPT/JPT).  
It uses AI to create exam questions, supports listening with audio playback, and allows saving/loading exams for repeated practice.  

## Features  
    - Generate mock exams (JLPT or JPT) with customizable difficulty.  
    - Covers Kanji, Vocabulary, Grammar, Reading, and Listening sections.  
    - Listening questions include audio playback.  
    - Save exams to CSV and reload them later.  
    - Interactive quiz mode with scoring and explanations.  

## Requirements  
    * Python 3.9+  
    * Dependencies:  
        - openai  
        - gtts  
        - pygame  
        - Standard libraries: os, sys, json, re, csv, time, datetime  

## Usage
1. Clone or download the repository.
2. Install dependencies:  
    ```bash  
    pip install openai gTTS pygame  
3. Run the application:  
    python main.py  

## Configuration  
API settings are stored in data/api.txt (API Key, Base URL, Model).  
Generated exams are saved in data/questions/.  

## License  
This project is for educational purposes.  