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

def del_api():
    api_file = resource_path(os.path.join("data", "api.txt"))
    if os.path.exists(api_file):
        os.remove(api_file)
        print("API configuration deleted.")
    else:
        print("No API configuration found.")
    input("Press Enter to return...")

def del_questions():
    folder = resource_path(os.path.join("data", "questions"))
    files = [f for f in os.listdir(folder) if f.endswith(".csv")]
    if not files:
        print("No saved exams to delete.")
        input("Press Enter to return...")
        return
    print("\n--- Saved Exams ---")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    choice = input("\nSelect exam number to delete (or 'q' to cancel): ")
    if choice.lower() == 'q':
        return
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(files):
        return
    filename = files[int(choice)-1]
    os.remove(os.path.join(folder, filename))
    print(f"Deleted {filename}.")
    input("Press Enter to return...")

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
    exam, difficulty, options = details
    if exam == "JLPT":
        struct_info = (
            f"1. Language Knowledge: Kanji ({options["K"]} q's), Vocabulary ({options["V"]} q's), Grammar ({options["G"]} q's)\n"
            f"2. Reading: {options["RS"][0]} short passages ({options["RS"][1]} q's each), {options["RL"][0]} long passage ({options["RL"][1]} q's)\n"
            f"3. Listening: {options["L"][0]} dialogue scenarios, {options["L"][1]} questions each ({options["L"][0]*options["L"][1]} q's total)"
        )
    else:
        struct_info = (
        f"1. Listening: {options["L"][0]} dialogue scenarios, {options["L"][1]} questions each ({options["L"][0]*options["L"][1]} q's total)\n"
        f"2. Reading & Grammar: {options["RS"][0]} short passages ({options["RS"][1]} q's each), {options["RL"][0]} long passage ({options["RL"][1]} q's), {options["G"][0]} grammar questions"
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

def generation_settings():
    while True:
        type_choice = input("Choose Exam with numbers: [1] JLPT [2] JPT: ")
        if type_choice in ["1", "2"]:
            break
    while True:
        diff = input("Difficulty (JLPT: N5->N1 // JPT: 315->990): ").upper()
        if type_choice == "1" and diff in ["N5", "N4", "N3", "N2", "N1"]:
            break
        elif type_choice == "2":
            try:
                score = int(diff)
                if 315 <= score <= 990:
                    break
            except ValueError:
                pass
    if type_choice == "1":
        exam = "JLPT"
        options = {"K": 5, "V": 5, "G": 5, "RS": [2, 3], "RL": [1, 5], "L": [2, 5]}
        opt_keys = ["K", "V", "G", "RS", "RL", "L"]
    else:
        exam = "JPT"
        options = {"G": 10, "RS": [2, 3], "RL": [1, 5], "L": [2, 5]}
        opt_keys = ["G", "RS", "RL", "L"]
    while True:
        reply = input("Would you like to customize question distribution? Press Enter to confirm, or type 'n' to skip: ")
        if reply.lower() == "n":
            return exam, diff, options
        keys = {"K": "Please enter number of Kanji questions",
                "V": "Please enter number of Vocabulary questions",
                "G": "Please enter number of Grammar questions",
                "L": [
                    "Please enter number of Listening scenarios (e.g., 2)",
                    "Please enter number of questions per Listening scenario (e.g., 5)"],
                "RS": [
                    "Please enter number of Short Reading passages (e.g., 2)",
                    "Please enter number of questions per Short Reading passage (e.g., 3)"],
                "RL": [
                    "Please enter number of Long Reading passages (e.g., 1)",
                    "Please enter number of questions per Long Reading passage (e.g., 5)"]}
        for key in opt_keys:
            if key in ["K", "V", "G"]:
                temp = input(f"{keys[key]} (default {options[key]}): ")
                if temp.isdigit():
                    options[key] = int(temp)
            else:
                temp1 = input(f"{keys[key][0]} (default {options[key][0]}): ")
                temp2 = input(f"{keys[key][1]} (default {options[key][1]}): ")
                if temp1.isdigit() and temp2.isdigit():
                    options[key] = [int(temp1), int(temp2)]
        confirm = input("Are you sure you want to proceed with these settings? Press Enter to confirm, or type 'n' to re-enter: ")
        if confirm.lower() != "n":
            break
    return exam, diff, options

def main():
    init_app()
    while True:
        clear_console()
        print("========== Mock Nihongo ===========")
        print("1. Generate New Exam")
        print("2. Load Saved Exam")
        print("3. Delete Saved Exams")
        print("4. Update API Configuration")
        print("5. Delete API Configuration")
        print("6. Exit")
        choice = input("Select an option: ")
        if choice == "1":
            exam, diff, options = generation_settings()
            print("\n> Requesting from AI...")
            raw_data = ask_ai([exam, diff, options])
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
            del_questions()
        elif choice == "4":
            init_api()
        elif choice == "5":
            del_api()
        elif choice == "6":
            break

if __name__ == "__main__":
    main()