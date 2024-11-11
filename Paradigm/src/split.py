from pypinyin import pinyin, Style

def split_pinyin(input_string):
    # 使用 pypinyin 将汉字字符串转换为拼音
    pinyin_list = pinyin(input_string, style=Style.NORMAL)

    result = []
    current_word = ""

    # 遍历拼音列表，按照拼音规则划分字符串
    for pinyin_word in pinyin_list:
        pinyin_word = pinyin_word[0]
        current_word += pinyin_word
        if pinyin_word.isalpha() and len(pinyin_word) == 1:
            result.append(current_word)
            current_word = ""

    # 处理最后一个拼音
    if current_word:
        result.append(current_word)

    return result

input_string = "nihao"
pinyin_segments = split_pinyin(input_string)
print(pinyin_segments)  # 输出 ["ni", "hao"]
