class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.standard_inputs = ["a", "ai", "an", "ang", "ao", "ba", "bai", "ban", "bang", "bao", "bei", "ben", "beng", "bi", "bian",
                       "biang", "biao", "bie", "bin", "bing", "bo", "bu", "ca", "cai", "can", "cang", "cao", "ce", "cen",
                       "ceng", "cha", "chai", "chan", "chang", "chao", "che", "chen", "cheng", "chi", "chong", "chou",
                       "chu", "chua", "chuai", "chuan", "chuang", "chui", "chun", "chuo", "ci", "cong", "cou", "cu",
                       "cuan", "cui", "cun", "cuo", "da", "dai", "dan", "dang", "dao", "de", "dei", "den", "deng", "di",
                       "dian", "diao", "die", "ding", "diu", "dong", "dou", "du", "duan", "dui", "dun", "duo", "e", "ei",
                       "en", "eng", "er", "fa", "fan", "fang", "fei", "fen", "feng", "fiao", "fo", "fou", "fu", "ga",
                       "gai", "gan", "gang", "gao", "ge", "gei", "gen", "geng", "gong", "gou", "gu", "gua", "guai", "guan",
                       "guang", "gui", "gun", "guo", "ha", "hai", "han", "hang", "hao", "he", "hei", "hen", "heng", "hong",
                       "hou", "hu", "hua", "huai", "huan", "huang", "hui", "hun", "huo", "ji", "jia", "jian", "jiang",
                       "jiao", "jie", "jin", "jing", "jiong", "jiu", "ju", "juan", "jue", "jun", "ka", "kai", "kan",
                       "kang", "kao", "ke", "kei", "ken", "keng", "kong", "kou", "ku", "kua", "kuai", "kuan", "kuang",
                       "kui", "kun", "kuo", "la", "lai", "lan", "lang", "lao", "le", "lei", "leng", "li", "lia", "lian",
                       "liang", "liao", "lie", "lin", "ling", "liu", "lo", "long", "lou", "lu", "luan", "lun", "luo", "lü",
                       "lüe", "ma", "mai", "man", "mang", "mao", "me", "mei", "men", "meng", "mi", "mian", "miao", "mie",
                       "min", "ming", "miu", "mo", "mou", "mu", "na", "nai", "nan", "nang", "nao", "ne", "nei", "nen",
                       "neng", "ni", "nian", "niang", "niao", "nie", "nin", "ning", "niu", "nong", "nou", "nu", "nuan",
                       "nuo", "nü", "nüe", "o", "ong", "ou", "pa", "pai", "pan", "pang", "pao", "pei", "pen", "peng", "pi",
                       "pian", "piao", "pie", "pin", "ping", "po", "pou", "pu", "qi", "qia", "qian", "qiang", "qiao",
                       "qie", "qin", "qing", "qiong", "qiu", "qu", "quan", "que", "qun", "ran", "rang", "rao", "re", "ren",
                       "reng", "ri", "rong", "rou", "ru", "ruan", "rui", "run", "ruo", "sa", "sai", "san", "sang", "sao",
                       "se", "sen", "seng", "sha", "shai", "shan", "shang", "shao", "she", "shei", "shen", "sheng", "shi",
                       "shou", "shu", "shua", "shuai", "shuan", "shuang", "shui", "shun", "shuo", "si", "song", "sou",
                       "su", "suan", "sui", "sun", "suo", "ta", "tai", "tan", "tang", "tao", "te", "tei", "teng", "ti",
                       "tian", "tiao", "tie", "ting", "tong", "tou", "tu", "tuan", "tui", "tun", "tuo", "wa", "wai", "wan",
                       "wang", "wei", "wen", "weng", "wo", "wu", "xi", "xia", "xian", "xiang", "xiao", "xie", "xin",
                       "xing", "xiong", "xiu", "xu", "xuan", "xue", "xun", "ya", "yai", "yan", "yang", "yao", "ye", "yi",
                       "yin", "ying", "yo", "yong", "you", "yu", "yuan", "yue", "yun", "za", "zai", "zan", "zang", "zao",
                       "ze", "zei", "zen", "zeng", "zha", "zhai", "zhan", "zhang", "zhao", "zhe", "zhei", "zhen", "zheng",
                       "zhi", "zhong", "zhou", "zhu", "zhua", "zhuai", "zhuan", "zhuang", "zhui", "zhun", "zhuo", "zi",
                       "zong", "zou", "zu", "zuan", "zui", "zun", "zuo"]
        for word in self.standard_inputs:
            self.insert(word)

    # 插入节点
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    # 查询首字母起全字匹配
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        if node.is_end_of_word:
            print("找到了")
        else:
            print("没找到")
        return node.is_end_of_word

if __name__ == '__main__':
    # # 创建字典树并插入所有标准输入字符串
    # trie = Trie()
    # while True:
    #     # 用户输入的字符串
    #     user_input = input("请输入一个字符串: ")
    #
    #     # 在字典树中搜索用户输入的字符串
    #     if trie.search(user_input):
    #         print("字符串在列表中找到了。")
    #     else:
    #         print("字符串不在列表中。")
    # 创建一个包含所有标准输入字符串的列表
    standard_inputs = ["apple", "banana", "cherry", "date", "fig", "grape", "kiwi", "lemon", "mango", "orange", "pear",
                       "plum"]

    # 创建一个字典（或集合）用于存储标准输入字符串
    input_set = set(standard_inputs)

    # 用户输入的字符串
    user_input = input("请输入一个字符串: ")

    # 检查用户输入是否在标准输入字符串列表中
    if user_input in input_set:
        print("字符串在列表中找到了。")
    else:
        print("字符串不在列表中。")
