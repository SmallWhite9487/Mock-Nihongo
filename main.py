from openai import OpenAI
import os
import sys
import json
import re
import csv
import time
from datetime import datetime
from gtts import gTTS
import pygame

pygame.mixer.init()

def resource_path(path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.getcwd(), path)

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

def play_audio(text, lang="ja"):
    try:
        tts = gTTS(text=text, lang=lang)
        temp_file = resource_path("temp_audio.mp3")
        tts.save(temp_file)
        
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception as e:
        print(f"\n[!] Audio playback error: {e}")

def init_app():
    os.makedirs(resource_path("data"), exist_ok=True)
    os.makedirs(resource_path(os.path.join("data", "questions")), exist_ok=True)
    api_file = resource_path(os.path.join("data", "api.txt"))
    if not os.path.exists(api_file):
        init_api()
    load_api()

def init_api():
    print("API configuration not found. Please initialize:")
    api = input("1. API Key: ").strip()
    url = input("2. Base URL: ").strip()
    mod = input("3. Model Name: ").strip()
    with open(resource_path(os.path.join("data", "api.txt")), "w", encoding="utf-8") as f:
        f.write(f'API: "{api}"\nBase URL: "{url}"\nModel: "{mod}"')

def load_api():
    global API_KEYS
    with open(resource_path(os.path.join("data", "api.txt")), "r", encoding="utf-8") as f:
        lines = f.readlines()
        API_KEYS = [line.split(": ", 1)[1].strip().replace('"', '') for line in lines]

def load_saved_exam():
    folder = resource_path(os.path.join("data", "questions"))
    files = [f for f in os.listdir(folder) if f.endswith(".csv")]
    if not files:
        print("No saved exams found.")
        input("Press Enter to return...")
        return
    print("\n--- Saved Exams ---")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    choice = input("\nSelect exam number: ")
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(files):
        return
    filename = files[int(choice)-1]
    questions = []
    with open(os.path.join(folder, filename), "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            opts = row.get("Options", "[]")
            try:
                opts_list = json.loads(opts)
            except:
                opts_list = opts.split("|")
            if len(opts_list) < 4:
                opts_list += ["N/A"]*(4-len(opts_list))
            questions.append({
                "section": row["Section"],
                "content": row["Content"],
                "question": row["Question"],
                "options": opts_list,
                "answer": row["Answer"],
                "note": row.get("Note", "")
            })
    start_quiz(questions)

def ask_ai(details):
    client = OpenAI(api_key=API_KEYS[0], base_url=API_KEYS[1])
    exam, difficulty = details
    if exam == "JLPT":
        struct_info = (
            "1. Language Knowledge: Kanji (5 q's), Vocabulary (5 q's), Grammar (5 q's)\n"
            "2. Reading: 1 long passage (5 q's)\n"
            "3. Listening: 2 dialogue scenarios, 3 questions each (6 q's total)"
        )
    else:
        struct_info = (
            "1. Listening: 2 dialogue scenarios, 5 questions each (10 q's total)\n"
            "2. Reading & Grammar: 2 short passages (3 q's each), 1 long passage (5 q's), 10 grammar questions"
        )
    prompt = f"""
You are a professional Japanese teacher. Create a mock {exam} ({difficulty}) exam.
Strictly follow this structure:
{struct_info}

[Output Requirements]
Return a JSON array where each object contains:
- section: The section name (e.g., "Kanji", "Grammar", "Reading", "Listening")
- content: The main text (For Listening, this MUST be the full Japanese dialogue transcript)
- question: The specific question
- options: [A, B, C, D] (A JSON array of four full Japanese answer choices (e.g., ["バスで","電車で","自転車で","車で"]))
- answer: Correct letter
- note: Brief explanation

IMPORTANT: Output ONLY the raw JSON array.
"""
    try:
        completion = client.chat.completions.create(
            model=API_KEYS[2],
            messages=[{"role": "system", "content": "You are a specialized Japanese exam generator that outputs pure JSON."},
                        {"role": "user", "content": prompt}],
            temperature=0.3,
            timeout=180.0)
        return completion.choices[0].message.content
    except Exception as e:
        print(f"\n[!] AI request failed: {e}")
        return ""

def start_quiz(questions):
    clear_console()
    print("========== Mock Exam Session Starting ==========\n")
    score = 0
    idx = 0
    total = len(questions)
    while idx < total:
        q = questions[idx]
        sec = q.get("section", "General")
        content = q.get("content", "")
        if "Listening" in sec:
            group = []
            current_content = content
            temp_idx = idx
            while temp_idx < total and questions[temp_idx].get("content") == current_content:
                group.append(questions[temp_idx])
                temp_idx += 1
            print(f"--- Question {idx+1} to {temp_idx} [{sec}] ---\n")
            for sub_i, sub_q in enumerate(group):
                opts = sub_q.get("options", ["N/A"]*4)
                print(f"Question: {chr(65+sub_i)}. {sub_q.get("question")}")
                print(f"A: {opts[0]}    B: {opts[1]}")
                print(f"C: {opts[2]}    D: {opts[3]}")
            audio_played = False
            while True:
                choice = input("\nAction: [1] Play Audio (ONCE) | [2] Show Transcript | [3] Start Answering: ")
                if choice == "1":
                    if not audio_played:
                        print("Playing audio now...")
                        play_audio(current_content)
                        audio_played = True
                    else:
                        print("[!] Audio has already been played once.")
                elif choice == "2":
                    print(f"Transcript:\n{current_content}")
                elif choice == "3":
                    break
            for sub_i, sub_q in enumerate(group):
                ans = sub_q.get("answer", "A")
                user_ans = input(f"\nYour answer for Question {chr(65+sub_i)} (A-D) or 'Q' to quit: ").upper()
                if user_ans == "Q":
                    return
                if user_ans == ans:
                    print("✔ Correct!")
                    score += 1
                else:
                    print(f"✘ Incorrect. Correct answer is: {ans}")
                print(f"Explanation: {sub_q.get("note","")}")
            idx = temp_idx
            input("\nPress Enter to continue...")
            clear_console()
            continue
        print(f"--- Question {idx+1} [{sec}] ---")
        if "Reading" in sec:
            print(f"Reading Passage:\n{content}")
        else:
            print(f"Content: {content}")
        print(f"\nQuestion: {q.get("question","")}")
        opts = q.get("options", ["N/A"]*4)
        print(f"A: {opts[0]}    B: {opts[1]}")
        print(f"C: {opts[2]}    D: {opts[3]}")
        user_ans = input("\nYour answer (A-D) or 'Q' to quit: ").upper()
        if user_ans == "Q":
            break
        if user_ans == q.get("answer","A"):
            print("✔ Correct!")
            score += 1
        else:
            print(f"✘ Incorrect. Correct answer is: {q.get("answer","A")}")
        print(f"Explanation: {q.get("note", "")}\n")
        idx += 1
        input("Press Enter to continue...")
        clear_console()
    print(f"Exam Completed! Final Score: {score}/{total}")
    input("Press Enter to return to main menu...")

def main():
    init_app()
    while True:
        clear_console()
        print("========== Mock Nihongo ===========")
        print("1. Generate New Exam")
        print("2. Load Saved Exam")
        print("3. Update API Configuration")
        print("4. Exit")
        choice = input("Select an option: ")
        if choice == "1":
            type_choice = input("Choose Exam: [1] JLPT [2] JPT: ")
            if type_choice == "1":
                exam = "JLPT" 
            else: 
                exam = "JPT"
            diff = input("Difficulty (e.g., N2): ").upper()
            print("\n> Requesting from AI...")
            raw_data = ask_ai([exam, diff])
            match = re.search(r"(\[.*\])", raw_data, re.DOTALL)
            if match:
                parsed_list = json.loads(match.group(1))
                filename = f"{exam}_{diff}_{datetime.now().strftime("%H%M%S")}.csv"
                save_path = resource_path(os.path.join("data", "questions", filename))
                with open(save_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Section", "Content", "Question", "Options", "Answer", "Note"])
                    for item in parsed_list:
                        writer.writerow([
                            item.get("section"), item.get("content"), item.get("question"),
                            json.dumps(item.get("options", ["N/A"]*4)), item.get("answer"), item.get("note")
                        ])
                print(f"Saved! Starting exam...")
                start_quiz(parsed_list)
        elif choice == "2":
            load_saved_exam()
        elif choice == "3":
            init_api()
        elif choice == "4":
            break

if __name__ == "__main__":
    main()