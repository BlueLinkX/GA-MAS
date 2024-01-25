import os
import datetime
import re
import json
import time


def write_LLMlog(name, prompt, response, log_dir):
    prompt = str(prompt).replace("\\n", "\n").replace("{", "\n{")

    output_log = (
        f"{name}\n"
        f"Prompt:\n{prompt}\n\n"
        f"Result:\n{response}\n"
        "======================================================================================"
    )
    output_log.replace("  ", "")

    with open(os.path.join(log_dir, "api_log.txt"), "a",
              encoding="utf-8") as file:
        file.write(output_log + "\n")

    write_log(f"{name}:{response}", log_dir)
    return response


def write_log(text, log_dir, print_flag=False):
    if print_flag:
        print(text)
    with open(os.path.join(log_dir, "chat_history.txt"), "a",
              encoding="utf-8") as file:
        file.write(f"""{text}\n\n""")

    return


def load_violation_log(dir, max_entries=15):
    """Loads the last max_entries violation logs from a file."""
    violation_log = []
    try:
        with open(os.path.join(dir, 'vlog.json'), "r",
                  encoding='utf-8') as file:
            all_lines = file.readlines()
            violation_log = all_lines[
                -max_entries:]  # Read the last max_entries records
    except FileNotFoundError:
        print("No existing violation log found.")
        time.sleep(10)
        return []
    return [line.strip()
            for line in violation_log]  # Remove newline characters


def savelog(log, dir):
    """Saves a log or data to a file."""
    try:
        with open(dir, "w", encoding='utf-8') as file:
            if isinstance(log, list):
                for log_entry in log:
                    file.write(log_entry + '\n')
            elif isinstance(log, str):
                file.write(log)
    except Exception as e:
        print(e)
        print("Retrying in 10 seconds")
        time.sleep(10)
        return savelog(log, dir)


def save_policy(*agents, dir):
    """Saves the policies of agents to a JSON file."""
    agents_policies = [agent.character_context["Policy"] for agent in agents]
    policy_json = json.dumps(agents_policies, ensure_ascii=False, indent=4)
    savelog(policy_json, os.path.join(dir, 'policy.json'))
    return agents_policies


def save_advice(*advice, dir):
    """Saves the advice of agents to a JSON file."""
    agents_advice = [agent.character_context["Advice"] for agent in advice]
    advice_json = json.dumps(agents_advice, ensure_ascii=False, indent=4)
    savelog(advice_json, os.path.join(dir, 'advice.json'))
    return agents_advice


def save_vlog(vlog, dir):
    """Saves a vlog (video log) to a file."""
    savelog(vlog, os.path.join(dir, 'vlog.json'))


def rename_dir(olddir, newdir):
    try:
        os.rename(olddir, newdir)
    except Exception as e:
        print(e)
        print("10秒后重试")
        time.sleep(10)
        return rename_dir(olddir, newdir)


def extract_content(text, start_mark, end_mark):
    """
    从给定文本中提取开始关键字和结束关键字之间的内容。

    参数:
    text (str): 要从中提取内容的文本。
    start_mark (str): 内容开始的关键字。
    end_mark (str): 内容结束的关键字。

    返回:
    str: 提取出的文本内容。
    """
    if text and start_mark in text and end_mark in text:
        start_idx = text.find(start_mark) + len(start_mark)
        end_idx = text.find(end_mark, start_idx)
        extracted_text = text[start_idx:end_idx].strip()
        return extracted_text
    elif text and start_mark in text and end_mark not in text:
        start_idx = text.find(start_mark) + len(start_mark)
        extracted_text = text[start_idx:].strip()
        purple_print(
            f"Warning! No END MARK extracted! start_mark: {start_mark} end_mark: {end_mark}\n"
            f"Returning extracted_text: {extracted_text}")
        return extracted_text
    else:
        purple_print(
            f"Warning! No START MARK extracted! start_mark: {start_mark} end_mark: {end_mark}\n"
            f"Returning extracted_text: None")
        return ''


def handle_violation(violation_text, violation_log, agentA, agentB,
                     round_savepath, round_count):
    print("Dialogue interrupted by the supervisor, restarting the dialogue.")
    violation_log.append(violation_text)
    savelog(violation_log, "./log/guessNumber/vlog_number.txt")
    violation_log_str = "\n".join(violation_log)
    agentA.character_context[
        "Violation Log"] = f"Violation Log:\n{violation_log_str}"
    agentB.character_context[
        "Violation Log"] = f"Violation Log:\n{violation_log_str}"
    policies = save_policy(agentA, agentB, dir=round_savepath)
    A_policy, B_policy = policies
    print("End by Supervisor")
    new_round_savepath = f"{round_savepath}-{round_count}"
    os.rename(round_savepath, new_round_savepath)
    return A_policy, B_policy, violation_log_str


def extract_values(text):
    """
    Extract the values associated with 'WHEN', 'WHERE', and 'WHO' from the provided text.
    This function is designed to handle any type of separators, including alphanumeric,
    and is also case-insensitive, robust to different orderings and long gaps.

    Parameters:
    - text (str): The text to parse.

    Returns:
    - dict: A dictionary with keys 'WHEN', 'WHERE', 'WHO' and their corresponding boolean values.
             If a key occurs multiple times, the last occurrence is used.
    """
    # Convert text to lower case for case-insensitive matching
    text_lower = text.lower()

    # Regular expression patterns for each key, in lower case, accounting for any separators
    patterns = {
        'WHEN': r"when\s*.*?\s*(true|false)",
        'WHERE': r"where\s*.*?\s*(true|false)",
        'WHO': r"who\s*.*?\s*(true|false)"
    }

    # Initialize a result dictionary with default values
    result = {'WHEN': False, 'WHERE': False, 'WHO': False}

    # Iterate over each pattern and update the dictionary
    for key, pattern in patterns.items():
        # Find all matches for each pattern
        matches = re.findall(pattern, text_lower)
        if matches:
            # Use the last occurrence if a key appears multiple times
            result[key] = matches[-1] == 'true'

    return result


def find_sentence_with_word(text, word_list):
    """
    Find and return the sentence containing any of the words or their plural forms 
    from the word list in the provided text.

    Parameters:
    - text (str): The text to search through.
    - word_list (list): A list of words (and their plural forms) to search for.

    Returns:
    - list: A list of sentences containing any of the words or their plural forms from the word list.
    """
    # Split the text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Convert word_list to lower case for case-insensitive comparison
    word_list_lower = [word.lower() for word in word_list]

    # List to store sentences containing the words or their plural forms
    matching_sentences = []

    # Check each sentence for any of the words or their plural forms
    for sentence in sentences:
        for word in word_list_lower:
            # Check for both singular and plural forms of the word
            if re.search(r'\b' + re.escape(word) + r's?\b', sentence.lower()):
                matching_sentences.append(sentence)
                break  # Break to avoid adding the same sentence multiple times

    return matching_sentences


def calculate_accuracy(guessed_number, actual_number):
    if guessed_number != 0:
        return round(1 - abs(guessed_number - actual_number) / actual_number,
                     2)
    return 0


def try_rename_dir(olddir, newdir):
    try:
        os.rename(olddir, newdir)
    except Exception as e:
        print(e)
        print("10秒后重试")
        time.sleep(10)
        return try_rename_dir(olddir, newdir)


def extract_numbers(text):
    # 使用正则表达式匹配所有连续的数字
    numbers = re.findall(r'\d+', text)
    return [int(num) for num in numbers]


def reset_dialogue_history(context):
    context["Dialogue History"] = ""
    return context


def red_print(text):
    print(f"\033[1;31m{text}\033[0m")


def red_input(text):
    return input(f"\033[1;31m{text}\033[0m")


def green_print(text):
    print(f"\033[1;32m{text}\033[0m")


def yellow_print(text):
    print(f"\033[1;33m{text}\033[0m")


def blue_print(text):
    print(f"\033[1;34m{text}\033[0m")


def purple_print(text):
    print(f"\033[1;35m{text}\033[0m")


def light_blue_print(text):
    print(f"\033[1;36m{text}\033[0m")


def white_print(text):
    print(f"\033[1;37m{text}\033[0m")
