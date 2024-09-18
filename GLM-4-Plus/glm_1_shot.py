from zhipuai import ZhipuAI
import torch
import argparse
import os
import re
import json
import csv
def extract(pairs_sentence):
    num = 0
    translation_dict = {}
    for i, src_word in enumerate(pairs_sentence.keys()):
        translation = []
        sentence = pairs_sentence[src_word]
        if sentence != None:
            sentence = sentence.split('\n')[0]
            if '*' in sentence:
                match = re.search(r'as\s+\*\*([^*]*)\*\*', sentence)
                # 检查匹配结果
                if match:
                    translation = match.group(1).rstrip(".").rstrip(",")
                    translation_dict.update({src_word: translation})
            elif ' as "' in sentence and translation == []:
                match = re.search(r'as\s+"([^"]*)"', sentence)
                # 检查匹配结果
                if match:
                    translation = match.group(1).rstrip(".").rstrip(",")
                    translation_dict.update({src_word: translation})
            elif 'as' in sentence and translation == [] and " (" in sentence:
                match = re.search(r'as (.*?) \(', sentence)
                # sentence = sentence.split('.')[0] # 检索中文
                # match = re.search(r'as ([\u4e00-\u9fff]+) \(', sentence)  # 检索中文
                # sentence = sentence.split('.')[0] # 检索日文
                # match = re.search(r'as ([\u3040 -\u30FF\u4E00 -\u9FAF\uFF66 -\uFF9F]+) \(', sentence)  # 检索日文
                # 检查匹配结果
                if match:
                    translation = match.group(1).rstrip(".").rstrip(",")
                    translation_dict.update({src_word: translation})
            elif ' as ' in sentence and translation == []:
                match = re.search(r'as (.*?)', sentence)
                # sentence = sentence.split('.')[0]
                # match = re.search(r'as ([\u4e00-\u9fff]+)', sentence) #检索中文
                # match = re.search(r'as ([\u3040 -\u30FF\u4E00 -\u9FAF\uFF66 -\uFF9F]+)', sentence) #检索日语
                # 检查匹配结果
                if match:
                    translation = match.group(1).rstrip(".").rstrip(",")
                    translation_dict.update({src_word: translation})
            elif 'is also "' in sentence and translation == []:
                match = re.search(r'is also\s+"([^"]*)"', sentence)
                # 检查匹配结果
                if match:
                    translation = match.group(1).rstrip(".").rstrip(",")
                    translation_dict.update({src_word: translation})
            elif ' (' in sentence and translation == []:
                match = re.search(r"\w+(?=\s*\()", sentence)
                if match:
                    translation = match.group(0).rstrip(".").rstrip(",").replace('"', '').replace("'", '')
            if translation == []:
                if len(sentence.split(' ')) <= 5:
                    translation = sentence.rstrip(".").replace('"', '').replace("'", '').replace('.', '')
            if translation != []:
                translations = translation.split(', ')
                translation = translations[0].rstrip(".").replace('[', '').replace(']', '').replace("'", '')
                if ' or ' in translation:
                    match = re.search(r'(\S+)\s+or', sentence)
                    translation = match.group(1)
                translation_dict.update({src_word: [translation]})
            else:
                print(src_word, "没有找到匹配的内容")
                # translation_dict.update({src_word: 'None'})
                num += 1
        else:
            print("***invalid sentence***")
    print("*****invalid:", num)
    return translation_dict
def wordsim_evaluate(src_lang, trg_lang, data_dict):
    src_gold_words = []
    trg_gold_words = []
    binary_lexicon = {}
    if args.src_lang in ['zh', 'en', 'ja'] and args.trg_lang in ['zh', 'en', 'ja']:
        file_lexicon = open(
            f'/data/hl/BLI/acl2024-bli/hl/clwe/dictionaries/{args.src_lang}-{args.trg_lang}.5000-6500.txt',
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
                f'/data/hl/xling-eval-master/bli_datasets/{trg_lang}-{src_lang}/yacle.test.freq.2k.{trg_lang}-{src_lang}.tsv',
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
            file_lexicon = open(f'/data/hl/xling-eval-master/bli_datasets/{src_lang}-{trg_lang}/yacle.test.freq.2k.{src_lang}-{trg_lang}.tsv', 'r', encoding='utf-8')
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
                    # candidate_word = candidate_word.lower()
                    if candidate_word in trg_gold_words:
                        # print(src_gold_word,candidate_word)
                        count = count + 1
                        # print("hit:", src_gold_word, candidate_word)
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

def augment_text_with_glm_with_retry(content, max_retries=3):
    client = ZhipuAI(api_key="7b2c348aa000c771ca41fad2a5ed5174.tkYimBPYb9ITp59V")  # 填写您自己的APIKey
    for _ in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="glm-4-plus",  # 填写需要调用的模型编码
                messages=[
                    {"role": "user", "content": content}
                ],
                max_tokens = 30,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            # 捕获所有异常并进行处理
            error_message = str(e)  # 获取错误信息
            if '1301' in error_message:
                print("系统检测到输入内容可能包含不安全或敏感内容，请修改后重试。")
            else:
                print(f"遇到错误: {e}")
            # 返回一个默认值或者None，确保程序继续运行
            return None

parser = argparse.ArgumentParser(description='llama_translation')
parser.add_argument('--src_lang', default='de', help='source language')
parser.add_argument('--trg_lang', default='fr', help='source language')
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


# 找到和语言的大模型1-shot
with open(f"../near_words_32/{args.src_lang}.json", 'r') as f:
    nn_words = json.load(f)


if os.path.exists(f"llm_glm_word_pairs_{args.src_lang}_{args.trg_lang}_1.json"):
    print("*******file already exist")
    with open(f"llm_glm_word_pairs_{args.src_lang}_{args.trg_lang}_1.json", "r", encoding="utf-8") as f:
        pairs_s2t = json.load(f)
else:
    pairs_s2t = {}
    for word in src_gold_words:
        if word.lower() in nn_words.keys():
            nearest_word = nn_words[word.lower()][0]
            prompt = f"""The {src_lang} word {nearest_word} can be translated to {trg_lang} as"""
            out = augment_text_with_glm_with_retry(prompt)
            pairs_s2t[nearest_word] = out
            word_pairs_s2t = json.dumps(pairs_s2t, indent=4)
            with open(f"llm_glm_word_pairs_{args.src_lang}_{args.trg_lang}_1.json", "w", encoding="utf-8") as f:
                f.write(word_pairs_s2t)
            f.close()

data_dict = extract(pairs_s2t)



if os.path.exists(f"llm_glm_word_pairs_{args.src_lang}_{args.trg_lang}_1_shot.json"):
    print("*******file already exist")
    with open(f"llm_glm_word_pairs_{args.src_lang}_{args.trg_lang}_1_shot.json", "r", encoding="utf-8") as f:
        pairs_s2t = json.load(f)
else:
    pairs_s2t = {}
    print("***********", len(src_gold_words))
    for src_word in src_gold_words:
        if src_word.lower() in nn_words.keys():
            nearest_word = nn_words[src_word.lower()][0]
            if (nearest_word in data_dict.keys()) or (nearest_word.lower() in data_dict.keys()):
                trans = data_dict[nearest_word]
                prompt = f"""The {src_lang} word {nearest_word} can be translated to {trg_lang} as '{trans}'.\nThe {src_lang} word {src_word} can be translated to {trg_lang} as"""
                out = augment_text_with_glm_with_retry(prompt)
                pairs_s2t[src_word] = out
            else:
                prompt = f"""The {src_lang} word {src_word} can be translated to {trg_lang} as"""
                out = augment_text_with_glm_with_retry(prompt)
                pairs_s2t[src_word] = out
        else:
            prompt = f"""The {src_lang} word {src_word} can be translated to {trg_lang} as"""
            out = augment_text_with_glm_with_retry(prompt)
            pairs_s2t[src_word] = out

        word_pairs_s2t = json.dumps(pairs_s2t, indent=4)
        with open(f"llm_glm_word_pairs_{args.src_lang}_{args.trg_lang}_1_shot.json", "w", encoding="utf-8") as f:
            f.write(word_pairs_s2t)
        f.close()

translation_dict = extract(pairs_s2t)
# evaluate
acc = wordsim_evaluate(args.src_lang, args.trg_lang, translation_dict)


