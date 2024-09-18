import os.path
from openai import OpenAI
import socket
import urllib3.exceptions
import requests.exceptions
import time
import json
import argparse
import csv
import re

API_SECRET_KEY = "zk-9e873ff7d65d60a0f654bf4a40251498"
BASE_URL = "https://api.zhizengzeng.com/v1/"


# def simplify_to_traditional(simplified_text):
#     cc = OpenCC('s2twp')  # 简体中文转为繁体中文（台湾标准）
#     traditional_text = cc.convert(simplified_text)
#     return traditional_text


def extract_en(pairs_sentence):
    num = 0
    translation_dict = {}
    for i, src_word in enumerate(pairs_sentence.keys()):
        translation = []
        sentence = pairs_sentence[src_word]
        if "is '" in sentence or 'is "' in sentence:
            match = re.search(r"is\s+['\"]([^'\"]*)['\"]", sentence)
            # 检查匹配结果
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        elif 'remains ' in sentence and translation == [] and 'the same ' not in sentence:
            translation = src_word
        elif 'remain ' in sentence and translation == []:
            translation = src_word
        elif 'the same ' in sentence:
            translation = src_word
        elif ' (' in sentence and translation == []:
            match = re.search(r"\w+(?=\s*\()", sentence)
            if match:
                translation = match.group(0).rstrip(".").replace('"', '').replace("'", '')
        elif f'is already ' in sentence and f'{trg_lang}' in sentence:
            translation = src_word
        elif "as " in sentence and translation == []:
            match = re.search(r"as\s+['\"]([^'\"]*)['\"]", sentence)
            # 检查匹配结果
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        elif ' or ' in sentence and translation == []:
            match = re.search(r'"(.*?)"\s+or', sentence)
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        elif 'translates to ' in sentence and translation == []:
            match = re.search(r"translates to ['\"](.*?)['\"]", sentence)
            if src_word == '塚本':
                print(sentence, match)
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        if translation == []:
            if len(sentence.split(' ')) <= 5:
                translation = sentence.rstrip(".").replace('"', '').replace("'", '')
        if translation != []:
            translations = translation.split(', ')
            translation = translations[0]

            translation_dict.update({src_word: [translation]})
        else:
            print(src_word, "没有找到匹配的内容")
            # translation_dict.update({src_word: 'None'})
            num += 1
    print("*****invalid:", num)
    return translation_dict

def extract(content):
    json_objects = []
    json_objects_str = re.findall(r'\{[^{}]*\}', content)

    for json_str in json_objects_str:
        try:
            # 解析每个 JSON 字符串为字典
            json_object = json.loads(json_str)
            json_objects.append(json_object)
        except json.JSONDecodeError as e:
            print(f"无法解析 JSON 对象: {json_str} - 错误: {e}")


    translation_dict = {}
    num = 0
    for content in json_objects:
        translation = []
        src_word = ', '.join(content.keys())
        sentence = content[src_word]
        if "is '" in sentence or 'is "' in sentence:
            match = re.search(r"is\s+['\"]([^'\"]*)['\"]", sentence)
            # 检查匹配结果
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        elif 'remains ' in sentence and translation == [] and 'the same ' not in sentence:
            translation = src_word
        elif 'remain ' in sentence and translation == []:
            translation = src_word
        elif 'the same ' in sentence:
            translation = src_word
        elif ' (' in sentence and translation == []:
            match = re.search(r"\w+(?=\s*\()", sentence)
            if match:
                translation = match.group(0).rstrip(".").replace('"', '').replace("'", '')
        elif f'is already ' in sentence and f'{trg_lang}' in sentence:
            translation = src_word
        elif "as " in sentence and translation == []:
            match = re.search(r"as\s+['\"]([^'\"]*)['\"]", sentence)
            # 检查匹配结果
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        elif ' or ' in sentence and translation == []:
            match = re.search(r'"(.*?)"\s+or', sentence)
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        elif 'translates to ' in sentence and translation == []:
            match = re.search(r"translates to ['\"](.*?)['\"]", sentence)
            if src_word == '塚本':
                print(sentence, match)
            if match:
                translation = match.group(1).rstrip(".").replace('"', '').replace("'", '')
        if translation == []:
            if src_word == '痕迹':
                print(translation)
            if src_word == '痕迹':
                print(sentence)
            if len(sentence.split(' ')) <= 5:
                translation = sentence.rstrip(".").replace('"', '').replace("'", '')
            if src_word == '痕迹':
                print(translation)
        if translation != []:
            translations = translation.split(', ')
            translation = translations[0]
            if src_word == '痕迹':
                print(translation)
            translation_dict.update({src_word: [translation]})
        else:
            print(src_word, "没有找到匹配的内容")
            # translation_dict.update({src_word: 'None'})
            num += 1
    print("*****invalid:", num)

    return translation_dict

def wordsim_evaluate(src_lang, trg_lang, data_dict):
    src_gold_words = []
    trg_gold_words = []
    binary_lexicon = {}
    if args.src_lang in ['zh', 'en', 'ja'] and args.trg_lang in ['zh', 'en', 'ja']:
        file_lexicon = open(
            f'../bli_datasets/{args.src_lang}-{args.trg_lang}.5000-6500.txt',
            'r', encoding='utf-8')
        src_gold_words = []
        for line in file_lexicon.readlines():
            line = line.rstrip("\n")
            line = line.replace("\t", " ")
            line = line.replace("  ", " ")
            src_word, trg_word = line.split(' ')
            # trg_word = cc.convert(trg_word)
            if src_word not in binary_lexicon:
                binary_lexicon.update({src_word: [trg_word]})
            else:
                binary_lexicon[src_word].append(trg_word)
            src_gold_words.append(src_word)
            trg_gold_words.append(trg_word)
    else:
        if trg_lang == 'en':
            file_lexicon = open(
                f'../bli_datasets/{trg_lang}-{src_lang}/yacle.test.freq.2k.{trg_lang}-{src_lang}.tsv',
                'r', encoding='utf-8')
            for line in file_lexicon.readlines():
                line = line.rstrip("\n")
                line = line.replace("\t", " ")
                line = line.replace(" ", " ")
                print(line)
                src_word, trg_word = line.split(' ')
                if trg_word not in binary_lexicon:
                    binary_lexicon.update({trg_word: [src_word]})
                else:
                    binary_lexicon[trg_word].append(src_word)
                src_gold_words.append(trg_word)
                trg_gold_words.append(src_word)

            file_lexicon.close()
        else:
            file_lexicon = open(f'../bli_datasets/{src_lang}-{trg_lang}/yacle.test.freq.2k.{src_lang}-{trg_lang}.tsv', 'r', encoding='utf-8')
            for line in file_lexicon.readlines():
                line = line.rstrip("\n")
                line = line.replace("\t", " ")
                line = line.replace("  ", " ")
                src_word, trg_word = line.split(' ')
                if src_word not in binary_lexicon:
                    binary_lexicon.update({src_word: [trg_word]})
                else:
                    binary_lexicon[src_word].append(trg_word)
                src_gold_words.append(src_word)
                trg_gold_words.append(trg_word)

            file_lexicon.close()



    count = 0
    hit_count = 0

    for key, value in binary_lexicon.items():
        src_gold_word = key
        trg_gold_words = value
        if src_gold_word in data_dict.keys():
            hit_count = hit_count + 1
            candidate_words = list(set(data_dict[src_gold_word]))
            candidate_words = candidate_words + [candidate_word.lower() for candidate_word in candidate_words]
            candidate_words = list(set(candidate_words))
            # candidate_words = [cc.convert(c) for c in candidate_words]
            if candidate_words is not None:
                for candidate_word in candidate_words:
                    if candidate_word in trg_gold_words:
                        count = count + 1
                        break
                    else:
                        print("failed:", src_gold_word, candidate_word)
        else:
            print(src_gold_word)

    acc1 = count / len(binary_lexicon)
    print('Acc: {0:.4f}'.format(acc1))
    print(f"在双语词典中有{hit_count}个单词也在构建的词典中")
    print(f"双语词典和构建词典的{hit_count}个单词中，找到了{count}个")
    # acc2 = count / hit_count
    # print('Acc: {0:.4f}'.format(acc2))
    return acc1

# Function to augment text using GPT-3 with retry mechanism
def augment_text_with_gpt4_with_retry(content, max_retries=3):
    client = OpenAI(api_key=API_SECRET_KEY, base_url=BASE_URL)
    for _ in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    # {"role": "system", "content": "Marv is a factual chatbot that is also sarcastic."},
                    # {"role": "user", "content": "Do you know Guhanwen?"},
                    # {"role": "assistant", "content": "Guhanwen is a student in BFSU."},
                    {"role": "user", "content": content}
                ],
                temperature=0.1,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5,
                stop=None
            )
            if response.code != 0:
                print(f"Error code: {response.code}")
                print("Retrying...")
                time.sleep(30)  # Add a short delay before retrying
                continue
            else:
                answer = response.choices[0].message.content
            return answer
        except (
                socket.timeout, urllib3.exceptions.ReadTimeoutError, requests.exceptions.ReadTimeout,
                OpenAI.Timeout, OpenAI.ServiceUnavailableError,
                OpenAI.RateLimitError, OpenAI.APIError
        ):

            # Handle network error and retry
            print("Socket timeout, retrying...")
            time.sleep(30)  # Add a short delay before retrying
    # If max_retries is reached, return an error message
    return "Network error: Max retries reached"

parser = argparse.ArgumentParser(description='llama_translation')
parser.add_argument('--src_lang', default='zh', help='source language')
parser.add_argument('--trg_lang', default='fi', help='source language')
args = parser.parse_args()

lang_dic = {"en": "English", "de": "German", "fr": "French", "it":"Italian", "ru":"Russian", "tr":"Turkish", "hr":"Croatian", "fi":"Finnish", 'hu':'Hungarian', 'zh':'Chinese'}
src_lang = lang_dic[args.src_lang]
trg_lang = lang_dic[args.trg_lang]
if args.src_lang in ['zh','en','ja'] and args.trg_lang in ['zh','en','ja']:
    file_lexicon = open(
        f'../bli_datasets/{args.src_lang}-{args.trg_lang}.5000-6500.txt',
        'r', encoding='utf-8')
    src_gold_words = []
    for line in file_lexicon.readlines():
        line = line.rstrip("\n")
        line = line.replace("\t", " ")
        line = line.replace("  ", " ")
        src_word, trg_word = line.split(' ')
        src_gold_words.append(src_word)
else:
    if args.trg_lang == "en":
        file_lexicon = open(
            f'../bli_datasets/en-{args.src_lang}/yacle.test.freq.2k.en-{args.src_lang}.tsv',
            'r', encoding='utf-8')
        src_gold_words = []
        for line in file_lexicon.readlines():
            line = line.rstrip("\n")
            line = line.replace("\t", " ")
            line = line.replace("  ", " ")
            src_word, trg_word = line.split(' ')
            src_gold_words.append(trg_word)
    else:
        file_lexicon = open(f'../bli_datasets/{args.src_lang}-{args.trg_lang}/yacle.test.freq.2k.{args.src_lang}-{args.trg_lang}.tsv', 'r', encoding='utf-8')
        src_gold_words = []
        for line in file_lexicon.readlines():
            line = line.rstrip("\n")
            line = line.replace("\t"," ")
            line = line.replace("  ", " ")
            src_word, trg_word = line.split(' ')
            src_gold_words.append(src_word)

file_lexicon.close()

if os.path.exists(f"gpt_word_pairs_{args.src_lang}_en_zero.json"):
    print("****file already exists")
    with open(f"gpt_word_pairs_{args.src_lang}_en_zero.json", "r", encoding="utf-8") as f:
        pairs_s2t = json.load(f)
        data_dict = extract_en(pairs_s2t)
else:
    pairs_s2t = {}
    for src_word in src_gold_words:
        src_lang = lang_dic[args.src_lang]
        trg_lang = lang_dic[args.trg_lang]
        prompt = f" Translate the {src_lang} word '{src_word}' into English:"
        out = augment_text_with_gpt4_with_retry(prompt)
        pairs_s2t.update({src_word: out})
        word_pairs_s2t = json.dumps(pairs_s2t, indent=4)
        with open(f"gpt_word_pairs_{args.src_lang}_en_zero.json", "w", encoding="utf-8") as f:
            f.write(word_pairs_s2t)
        f.close()
        data_dict = extract_en(pairs_s2t)

if os.path.exists(f"gpt_en_aid_word_pairs_{args.src_lang}_{args.trg_lang}_zero.json"):
    print("****file already exists")

else:
    pairs_s2t = {}
    for src_word in src_gold_words:
        if src_word in data_dict.keys():
            eng = data_dict[src_word]
            for word in eng:
                prompt = f"Translate the {src_lang} word '{src_word}' into English: {word}.\nTranslate the English word '{word}' into {trg_lang}:"
                out = augment_text_with_gpt4_with_retry(prompt)
                pairs_s2t[src_word] = out
                word_pairs_s2t = json.dumps(pairs_s2t, indent=4)
                with open(f"gpt_en_aid_word_pairs_{args.src_lang}_{args.trg_lang}_zero.json", "a", encoding="utf-8") as f:
                    f.write(word_pairs_s2t)
                f.close()
                pairs_s2t = {}

with open(f"gpt_en_aid_word_pairs_{args.src_lang}_{args.trg_lang}_zero.json", "r", encoding="utf-8") as f:
    pairs_s2t = f.read()
translation_dict = extract(pairs_s2t)

# evaluate

acc = wordsim_evaluate(args.src_lang, args.trg_lang, translation_dict)


