import nltk
from nltk.corpus import brown, cess_esp, europarl_raw
from nltk.tokenize import word_tokenize
from collections import Counter
from janome.tokenizer import Tokenizer
from konlpy.tag import Okt
import pickle
from ctypes import *
import os
import pykakasi


def tokenize_japanese(sentences):
    tokenizer = Tokenizer()
    return [tokenizer.tokenize(sentence, wakati=True) for sentence in sentences]


def tokenize_korean(sentences):
    tokenizer = Okt()
    return [tokenizer.morphs(sentence) for sentence in sentences]

def save_word_freqs(word_freqs, filename):
    with open(filename, 'wb') as f:
        pickle.dump(word_freqs, f)

def load_word_freqs(filename):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None

def load_europarl_sentences(language):
    language_to_corpus = {
        'french': europarl_raw.french.sents,
        'german': europarl_raw.german.sents,
        'danish': europarl_raw.danish.sents,
        'dutch': europarl_raw.dutch.sents,
        'english': europarl_raw.english.sents,
        'finnish': europarl_raw.finnish.sents,
        'greek': europarl_raw.greek.sents,
        'italian': europarl_raw.italian.sents,
        'portuguese': europarl_raw.portuguese.sents,
        'spanish': europarl_raw.spanish.sents,
        'swedish': europarl_raw.swedish.sents
    }
    corpus_function = language_to_corpus.get(language, lambda: [])
    return corpus_function()

def load_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        sentences = file.readlines()
    return [sentence.strip() for sentence in sentences]

def romaji_to_hiragana(romaji):
    kakasi = pykakasi.kakasi()
    kakasi.setMode('H', 'a')  # Set to convert from Hiragana to Romaji
    converter = kakasi.getConverter()
    return converter.do(romaji)

def kana_to_romaji(text):
    kakasi = pykakasi.kakasi()
    kakasi.setMode('H', 'a')  # H: Hiragana, a: Romaji
    kakasi.setMode('K', 'a')  # K: Katakana, a: Romaji
    converter = kakasi.getConverter()
    return converter.do(text)

class CN_Class:
    def __init__(self, max_spell_len=100, max_out_len=50):
        # 加载 DLL
        self.lib = CDLL('./MyQtClass.dll')
        # 定义返回类型和参数类型
        self.lib.MyQtClass_new.restype = c_void_p
        self.lib.MyQtClass_delete.argtypes = [c_void_p]
        self.lib.MyQtClass_init.argtypes = [c_void_p, c_int, c_int]
        self.lib.MyQtClass_init.restype = c_bool
        self.lib.MyQtClass_deinit.argtypes = [c_void_p]
        self.lib.MyQtClass_search.argtypes = [c_void_p, c_char_p]
        self.lib.MyQtClass_search.restype = c_uint
        self.lib.MyQtClass_get_candidate.argtypes = [c_void_p, c_uint]
        self.lib.MyQtClass_get_candidate.restype = POINTER(c_char_p)
        self.lib.MyQtClass_free_results.argtypes = [c_void_p, POINTER(c_char_p), c_uint]
        self.obj = self.lib.MyQtClass_new()
        if not self.lib.MyQtClass_init(self.obj, max_spell_len, max_out_len):
            raise Exception("初始化失败！")

    def search(self, spell):
        try:
            result_count = self.lib.MyQtClass_search(self.obj, spell.encode('utf-8'))
            if result_count == 0:
                return []
            results = self.lib.MyQtClass_get_candidate(self.obj, result_count)
            candidate_list = [results[i].decode('utf-8') for i in range(result_count)]
            self.lib.MyQtClass_free_results(self.obj, results, result_count)
            return candidate_list
        except Exception as e:
            print(f"错误异常反馈: {e}")
            return []

    def deinit(self):
        self.lib.MyQtClass_deinit(self.obj)

    def __del__(self):
        try:
            self.deinit()
            self.lib.MyQtClass_delete(self.obj)
        except Exception as e:
            print(f"清空内存失败: {e}")

class MultiLangAutoComplete:
    def __init__(self, load_filename=None):
        # 加载欧洲语言
        self.languages = [
            'french', 'german', 'danish', 'dutch', 'english',
            'finnish', 'greek', 'italian', 'portuguese', 'spanish', 'swedish'
        ]
        self.words = {lang: Counter() for lang in self.languages}

        # 加载中文
        self.cn = CN_Class()

        # 加载日语
        self.words.update({'japanese': Counter()})
        japanese_sentences = load_sentences('japan.txt')
        self.tokenized_japanese = tokenize_japanese(japanese_sentences)
        # self.words.update({'korean': Counter()})
        # korean_sentences = load_sentences('path_to_korean.txt')
        # tokenized_korean = tokenize_korean(korean_sentences)

        if load_filename:
            loaded_words = load_word_freqs(load_filename)
            if loaded_words:
                self.words = loaded_words
            else:
                self.initialize_corpora()
        else:
            self.initialize_corpora()

    def initialize_corpora(self):
        self.train_corpus('english', brown.sents())
        self.train_corpus('spanish', cess_esp.sents())
        self.train_corpus('japanese', self.tokenized_japanese)
        # 欧洲数据集
        for language in self.languages:
            sentences = load_europarl_sentences(language)
            self.train_corpus(language, sentences)

    def train_corpus(self, language, sentences):
        for sentence in sentences:
            words = [word.lower() for word in sentence if isinstance(word, str)]
            self.words[language].update(words)

    def suggest(self, language, prefix, n_suggestions=5):
        suggestions = {word: freq for word, freq in self.words[language].items() if word.startswith(prefix)}
        sorted_suggestions = sorted(suggestions, key=suggestions.get, reverse=True)
        return sorted_suggestions[:n_suggestions]

    def save(self, filename):
        save_word_freqs(self.words, filename)

if __name__ == '__main__':
    # 加载已有的字词库或创建新的
    auto_complete = MultiLangAutoComplete('autocomplete_data.pkl')

    # 添加一些新的文本到英语字词库
    text = "Hello GPT, hello GPT, zhangyutao is a great programmer. Zyjacya in love, I Zyjacya in love with a girl"
    words = word_tokenize(text.lower())
    auto_complete.train_corpus('english', [words])

    # 使用联想输入功能
    # print(auto_complete.suggest('korean', '안'))  # Korean suggestions
    # 示例
    # hiragana_text = "こんにちは"
    # romaji_result = kana_to_romaji(hiragana_text)
    # print("平假名:", hiragana_text)
    # print("罗马音:", romaji_result)
    # romaji_text = "kon"
    # hiragana_result = romaji_to_hiragana(romaji_text)
    # print("罗马字:", romaji_text)
    # print("平假名:", hiragana_result)
    # print('japan:' + str(auto_complete.suggest('japanese', hiragana_result)))  # Japanese suggestions

    # 加载中文
    try:
        candidates = auto_complete.cn.search("nihao")
        print("中文:", candidates)
    except Exception as e:
        print(f"错误异常反馈: {e}")

    for index in auto_complete.languages:
        print(str(index) + ":" + str(auto_complete.suggest(index, 'gp')))  # Japanese suggestions

    # 保存字词库的状态
    auto_complete.save('autocomplete_data.pkl')

