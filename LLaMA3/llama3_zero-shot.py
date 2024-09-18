import torch
from modelscope import Model, AutoTokenizer, AutoModelForCausalLM
import argparse
# 模型下载
from modelscope import snapshot_download
import os
import re
import json
import itertools


def clean_translation(text):
    # 去掉双引号和单引号

    if ' ('in text:
        text = text.lstrip(" ")
        text = text.split(' ')[0]
    if ') ' in text:
        text = text.split(' ')[1]
        # text = text.split(' ')
        # text = str(text[0])+" "+ str(text[1])
    return text.strip().replace('"', '').replace("'", '').rstrip(',').rstrip('.').replace("„", '').replace("“", '').replace("\\", '').replace("”", '').replace("»", '').replace("«", '').replace(";", '')
def extract_before_period(sentence):
    # 使用正则表达式提取句号前面的部分
    match = re.search(r'(.*?)(?=\.)', sentence)
    if match:
        return match.group(1).strip()
    return ''
def extract(pairs_sentence):
    translation_dict = {}
    num = 0
    for i, src_word in enumerate(pairs_sentence.keys()):
        sentence = pairs_sentence[src_word]
        sentence = sentence.replace('follows:\n', '')
        sentence = sentence.replace('follows', '')
        sentence = sentence.replace('as:\n', 'as ')

        sentences = sentence.split('\n')  # 仅分割一次
        matches = []
        for sentence in sentences:
            sentence = sentence.replace('.', '')
            if ":" in sentence:
                parts = sentence.split(':')
                sentence = parts[0].rstrip(":") + parts[1]
            if "." in sentence:
                sentence = extract_before_period(sentence)

            pattern_as = r'(?<=\bis\s)(.*?)(?=\sor\b|$)'
            pattern_or = r'(?<=\sor\s)(.*?)(?=\.$|$)'
            # 提取 "as" 后面的内容
            matches_as = re.findall(pattern_as, sentence)
            # 提取 "or" 后面的内容
            matches_or = re.findall(pattern_or, sentence)
            # 合并结果为一个列表
            if 'or' and " " not in sentence:
                a = [sentence]
                matches.append(matches_as + matches_or + a)
            else:
                matches.append(matches_as + matches_or)
            # matches.append(matches_as + matches_or)
        matches = list(itertools.chain(*matches))
        if matches == [''] or matches == []:
            print(src_word, "No translations found.")
            num += 1
        else:
            # 提取翻译部分并处理引号
            translations = []
            for t in matches:
                if " " in t and "," not in t:
                    translations.append(clean_translation(t).split(' '))
                elif "to " in t:
                    t = clean_translation(t).split(', ')
                    translations.append([item.replace("to ", '') for item in t])
                else:
                    translations.append(clean_translation(t).split(', '))
            # translations = [clean_translation(t).split(', ') for t in matches]
            # 扁平化列表并去除空白字符
            translations = [item.strip() for sublist in translations for item in sublist if item.strip()]
            translation_dict.update({src_word: translations})
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

# model_dir = snapshot_download('AI-ModelScope/bloom-7b1', cache_dir='/data/hl/Multi-LLM/LLMs/llama3-8b/LLama3-8b')
model_dir = '/data/hl/Multi-LLM/LLMs/llama3-8b/LLama3-8b'
model = AutoModelForCausalLM.from_pretrained(model_dir, device_map='auto', torch_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(model_dir)

parser = argparse.ArgumentParser(description='llama_translation')
parser.add_argument('--src_lang', default='de', help='source language')
parser.add_argument('--trg_lang', default='fi', help='target language')
parser.add_argument('--out_file', default='', help='source language')
args = parser.parse_args()

lang_dic = {"en": "English", "de": "German", "fr": "French", "it":"Italian", "ru":"Russian", "tr":"Turkish", "hr":"Croatian", "fi":"Finnish", "hu":"Hungarian", 'zh':'Chinese','ja':'Japanese'}
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
print(len(src_gold_words))
if os.path.exists(f'llama3_word_pairs_{args.src_lang}_{args.trg_lang}_zero.json'):
    print("****file already exists")
    with open(f"llama3_word_pairs_{args.src_lang}_{args.trg_lang}_zero.json", "r", encoding="utf-8") as f:
        pairs_s2t = json.load(f)
else:
    pairs_s2t = {}
    for src_word in src_gold_words:
        src_lang = lang_dic[args.src_lang]
        trg_lang = lang_dic[args.trg_lang]
        prompt = f"""The {src_lang} word {src_word} in {trg_lang} is:"""
        device = model.device
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        logits = model.generate(inputs.input_ids, attention_mask=inputs.attention_mask, num_beams=4, max_new_tokens=10,  pad_token_id=tokenizer.eos_token_id, early_stopping=True)
        out = tokenizer.decode(logits[0].tolist(), skip_special_tokens=True)
        pairs_s2t.update({src_word: out})
        word_pairs_s2t = json.dumps(pairs_s2t, indent=4)
        with open(f"llama3_word_pairs_{args.src_lang}_{args.trg_lang}_zero.json", "w", encoding="utf-8") as f:
            f.write(word_pairs_s2t)
        f.close()

## extract
translation_dict = extract(pairs_s2t)

# evaluate

acc = wordsim_evaluate(args.src_lang, args.trg_lang, translation_dict)
