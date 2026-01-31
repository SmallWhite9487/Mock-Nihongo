import os
import sys
from openai import OpenAI

def resource_path(path):
    '''
    Get absolute path to resource, works for dev and for PyInstaller
    '''
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.getcwd(), path)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def init_app():
    '''
    Initialize application, check for API key and load it
    '''
    os.makedirs(resource_path("data"), exist_ok=True)
    api_file = resource_path(os.path.join("data", "api.txt"))
    if not os.path.exists(api_file):
        init_api()
        return
    with open(api_file, "r") as f:
        lines = [line.strip() for line in f.readlines()]
    if len(lines) < 3:
        init_api()
        return
    values = [line.split(": ")[1].replace('"', '') for line in lines if ": " in line]
    if any(v == "" for v in values):
        init_api()
    else:
        load_api()

def init_api():
    '''
    Prompt user for API key and save it
    '''
    open(resource_path(os.path.join("data", "api.txt")), "w")
    print("API keys not found. Please enter your AI API key, base URL and the Model.")
    while True:
        api = input("Please enter your API key: (eg: nvapi-xxxxxxxxxxxxxx)\n").strip()
        url = input("\nPlease enter the Base URL: (eg: https://integrate.api.nvidia.com/v1)\n").strip()
        mod = input("\nPlease enter the AI Model: (eg: deepseek-ai/deepseek-v3.2)\n").strip()
        reply = input("\nAre you sure these details are correct? If yes, just press the Enter key to confirm\n")
        if not reply:
            save_api(api, url, mod)
            break

def load_api():
    '''
    Load API key from api.txt
    '''
    global API_KEYS
    with open(resource_path(os.path.join("data", "api.txt")), "r") as f:
        contact = f.readlines()
        API_KEYS = []
        for line in contact:
            API_KEYS.append(line.strip().split(": ")[1].replace('"', ''))

def save_api(api,url,mod):
    '''
    Save API key to api.txt
    '''
    with open(resource_path(os.path.join("data", "api.txt")), "w") as f:
        form = f'API: "{api}"\nBase URL: "{url}"\nModel: "{mod}"'
        f.write(form)

def ask_ai(details):
    '''
    Ask AI a question and stream the response
    '''
    CLIENT = OpenAI(api_key="",
                    base_url="")
    
    exam, difficulty = details
    question = f"請編寫一套包含完整的日語考試-{exam}的模擬題，難度相當於{exam}的{difficulty}級/分，內容涵蓋該考試的全部內容以及所有題目，例如JPT有200題就生成200道。請提供每個問題的問題、選項、以及正確答案，請按照以下格式返回內容：'<問題>/<問題内容>/<選項A>/<選項B>/<選項C>/<選項D>/<正確答案>/<備註(如有必要)>', '<問題>/<問題内容>/<選項A>/<選項B>/<選項C>/<選項D>/<正確答案>/<備註(如有必要)>'，例如：'<下の___線の言葉の正しい表現、または同じ意味のはたらきをしている言葉を (A)から(D)の中で一つ選びなさい。>/<私の母は、画家です。>/<がけ>/<がか>/<かくけ>/<かくいえ>/<B>/', ......，並且每個問題之間請用, 分隔開來。請確保問題的多樣性、覆蓋範圍以及不重複，以便全面評估考生的日語能力。"
    question = "你好"

    print(question, exam, difficulty, details, API_KEYS)

    completion = CLIENT.chat.completions.create(
        model="",
        messages=[{"role":"user","content":question}],
        temperature=1,
        top_p=0.95,
        max_tokens=8192,
        extra_body={"chat_template_kwargs": {"thinking":True}},
        stream=True
    )

    for chunk in completion:
        if not getattr(chunk, "choices", None):
            continue
        reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
        if reasoning:
            print(reasoning, end="", flush=True)
        if chunk.choices and chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)


################################################################################################################################################
################################################################################################################################################

def main(first_run=False):
    def options_1():
        clear_console()
        while True:
            while True:
                exam = input("Please enter the exam type (JLPT, JPT): ").upper()
                if exam in ["JLPT", "JPT"]:
                    break
            while True:
                if exam == "JLPT":
                    difficulty = input("Please enter the JLPT level (N5, N4, N3, N2, N1): ").upper()
                    result = difficulty in ["N5", "N4", "N3", "N2", "N1"]
                else:
                    difficulty = input("Please enter the JPT level (Maximum: 990): ")
                    if difficulty.isdigit():
                        difficulty = int(difficulty)
                        result = 0 < difficulty <= 990
                    else:
                        result = False
                if result:
                    break
            confirm = input("\nAre you sure these options are correct? If yes, just press the Enter key to confirm.")
            if not confirm:
                return [exam, difficulty]
            
    clear_console()
    print("Welcome to the Mock Nihongo!\n")

    if first_run:
        print("Loaded data successfully.")
        print("==========Info of AI===========")
        print(f"Your AI API key: {API_KEYS[0]}")
        print(f"Your Base URL: {API_KEYS[1]}")
        print(f"Your AI Model: {API_KEYS[2]}")
        print("==========Info of AI===========\n")
    
    print("==========Options===========")
    options = ["Generate Mock Questions", "Exit"]
    for i in range(len(options)):
        print(f"{i+1}. {options[i]}")
    print("==========Options===========")
    user_input = input("Please enter your options: ")
    
    if user_input == "1":
        ask_ai(options_1())
        
if __name__ == "__main__":
    init_app()
    main(True)