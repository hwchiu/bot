from __future__ import annotations

from enum import Enum

from lazyopenai import generate
from pydantic import BaseModel
from pydantic import Field
from telegram import Update
from telegram.ext import ContextTypes

from ..loaders.url import load_url
from ..utils import parse_url
from .utils import get_message_text


class DifficultyLevel(str, Enum):
    N1 = "N1"
    N2 = "N2"
    N3 = "N3"
    N4_N5 = "N4-N5"

    def get_emoji(self) -> str:
        return {
            DifficultyLevel.N1: "🔴",
            DifficultyLevel.N2: "🟡",
            DifficultyLevel.N3: "🟢",
            DifficultyLevel.N4_N5: "⚪",
        }[self]


class ExampleSentence(BaseModel):
    japanese: str = Field(..., description="日文範例句子")
    chinese: str = Field(..., description="對應的繁體中文翻譯")

    def __str__(self) -> str:
        return f"    ⋮ 日：{self.japanese}\n    ⋮ 中：{self.chinese}"


class VocabularyItem(BaseModel):
    word: str = Field(..., description="單字/語彙")
    reading: str = Field(..., description="假名讀音")
    difficulty: DifficultyLevel = Field(..., description="JLPT難度等級")
    original: str = Field(..., description="原文中出現的形式")
    explanation: str = Field(..., description="詳細解釋與用法說明")
    example_sentences: list[ExampleSentence] = Field(default_factory=list, description="相關例句列表")

    def __str__(self) -> str:
        examples = "\n".join(str(ex) for ex in self.example_sentences)
        emoji = self.difficulty.get_emoji()
        return (
            f"【詞彙】 {self.word}（{self.reading}） {emoji} {self.difficulty.value}\n"
            f"┣━━ 原文：{self.original}\n"
            f"┣━━ 解釋：{self.explanation}\n"
            f"┗━━ 例句\n{examples}"
        )


class GrammarItem(BaseModel):
    grammar_pattern: str = Field(..., description="文法句型")
    difficulty: DifficultyLevel = Field(..., description="JLPT難度等級")
    original: str = Field(..., description="原文中出現的形式")
    explanation: str = Field(..., description="文法的基本意思和功能說明")
    conjugation: str = Field(..., description="接續變化規則")
    usage: str = Field(..., description="使用場合與注意事項")
    comparison: str = Field(..., description="與相似文法的比較")
    example_sentences: list[ExampleSentence] = Field(default_factory=list, description="示例句子列表")

    def __str__(self) -> str:
        examples = "\n".join(str(ex) for ex in self.example_sentences)
        emoji = self.difficulty.get_emoji()
        return (
            f"【文法】 {self.grammar_pattern} {emoji} {self.difficulty.value}\n"
            f"┣━━ 原文：{self.original}\n"
            f"┣━━ 解釋：{self.explanation}\n"
            f"┣━━ 接續：{self.conjugation}\n"
            f"┣━━ 場合：{self.usage}\n"
            f"┣━━ 比較：{self.comparison}\n"
            f"┗━━ 例句\n{examples}"
        )


class JLPTResponse(BaseModel):
    vocabulary_section: list[VocabularyItem] = Field(default_factory=list, description="詞彙分析區段")
    grammar_section: list[GrammarItem] = Field(default_factory=list, description="文法分析區段")

    def __str__(self) -> str:
        vocab_section = "\n\n".join(str(v) for v in self.vocabulary_section)
        grammar_section = "\n\n".join(str(g) for g in self.grammar_section)

        return (
            "⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒ 📚 詞彙分析 ⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒\n\n"
            f"{vocab_section}\n\n"
            "⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒ 📓 文法分析 ⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒\n\n"
            f"{grammar_section}"
        )


SYSTEM_PROMPT_V2 = """
你是一位精通日文的老師，熟悉日本語能力試驗（JLPT）的考試範圍，並使用台灣用語的繁體中文進行教學。從給定的文章中，整理出最困難的詞彙、語法結構及文字的理解，並提供詳細解釋和相應的例句。

文章來源會包含日文中的各種詞彙和文法結構。你需要找出這些內容中最可能構成挑戰的部分，並從初級到高級的語言水平提供分析，以幫助學生透徹理解。這樣可以更有效地幫助準備JLPT的考生提升這些重點方面的能力。

# 步驟

1. **文章閱讀與重點整理**：
- 仔細閱讀所提供的日文文章。
- 挑出文章中屬於N2及N1級別，或者特別難以掌握的詞彙、語法結構及文字表現。

2. **詞彙與語法分析**：
- 將挑出的詞彙或短語進行解釋，包括其詞義、詞性、使用情境等。
- 提供其對應的中文解釋和注釋，以幫助理解其日文中使用的細微差異。

3. **例句補充**：
- 使用挑出單詞或語法創建例句，將該語彙或結構的典型應用展示出來。
- 每個例句需要既有日文又有繁體中文翻譯，幫助學生更深刻理解。
""".strip()


SYSTEM_PROMPT_V1 = """
你是一位精通日文的老師，熟悉日本語能力試驗（JLPT）的考試範圍，並使用台灣用語的繁體中文進行教學。從給定的文章中，整理出最困難的詞彙、語法結構及文字的理解，並提供詳細解釋和相應的例句。

文章來源會包含日文中的各種詞彙和文法結構。你需要找出這些內容中最可能構成挑戰的部分，並從初級到高級的語言水平提供分析，以幫助學生透徹理解。這樣可以更有效地幫助準備JLPT的考生提升這些重點方面的能力。

# 步驟

1. **文章閱讀與重點整理**：
   - 仔細閱讀所提供的日文文章。
   - 挑出文章中屬於N2及N1級別，或者特別難以掌握的詞彙、語法結構及文字表現。

2. **詞彙與語法分析**：
   - 將挑出的詞彙或短語進行解釋，包括其詞義、詞性、使用情境等。
   - 提供其對應的中文解釋和注釋，以幫助理解其日文中使用的細微差異。
   - 增加近義詞、反義詞、文化或語用背景、常見搭配詞，甚至詞頻或JLPT等級的補充資訊。

3. **例句補充**：
   - 使用挑出單詞或語法創建例句，將該語彙或結構的典型應用展示出來。
   - 每個例句需要既有日文又有繁體中文翻譯，幫助學生更深刻理解。
   - 在例句中加入語法標註，顯示詞彙或語法的實際應用。

4. **活用與變化分析**：
   - 若為動詞或形容詞，提供活用變化的完整表格（如五段、一段、サ變等）。
   - 說明該語法的句型變化（如否定形、過去形）。

5. **類似表達的比較**：
   - 與其他相似詞彙或語法進行比較，闡明差異。
   - 提供相似句型的使用場合與正式程度。

6. **使用場合與注意事項**：
   - 提供該詞彙或語法的口語與書面語差異。
   - 提醒學習者可能犯的錯誤或特別注意的用法。

7. **視覺化補充**：
   - 利用表格呈現動詞或形容詞的活用變化。
   - 在例句中突出關鍵詞或語法，讓學習者清晰辨認。

# 詞彙或語法重點 🎯

難易度標示：
🔴 N1 程度 - 最高難度
🟡 N2 程度 - 中高難度
🟢 N3 程度 - 中等難度
⚪ N4-N5 程度 - 基礎難度

每個詞彙或語法點將標註其難易度：
- 🔴 較為艱深的文言表現或商業用語
- 🟡 新聞常用語彙與進階語法
- 🟢 日常生活中較為正式的表達
- ⚪ 基礎語彙與常用語法

# 輸出格式 📝

詞彙和文法將以以下美觀的格式呈現：

⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒ 📚 詞彙分析 ⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒

【詞彙】 〔詞彙名稱〕[🔴/🟡/🟢/⚪]
┣━━ 原文：〔原文內容〕
┣━━ 詞性：〔詞性與語法特徵，如五段動詞〕
┣━━ 解釋：〔詳細說明〕
┣━━ 近義詞：〔近義詞列表〕
┣━━ 反義詞：〔反義詞列表〕
┣━━ 文化背景：〔文化或語用背景〕
┣━━ 常見搭配：〔搭配詞列表〕
┣━━ 活用：
    ⋮ 動詞活用表（若適用）
┗━━ 例句
    ⋮ 日：〔完整句子〕
    ⋮ 中：〔對應翻譯〕

⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒ 📓 文法分析 ⭒⭒⭒⭒⭒⭒⭒⭒⭒⭒

【文法】 〔語法名稱〕[🔴/🟡/🟢/⚪]
┣━━ 原文：〔原文內容〕
┣━━ 解釋：〔詳細說明〕
┣━━ 接續：〔接續規則〕
┣━━ 場合：〔使用場合與適用情境〕
┣━━ 比較：〔相似文法比較與差異〕
┣━━ 句型變化：〔句型的否定形、過去形等變化〕
┣━━ 注意事項：〔常見錯誤與提醒〕
┣━━ 實際應用：
    ⋮ 提供真實場景描述
┗━━ 例句
    ⋮ 日：〔完整句子〕
    ⋮ 中：〔對應翻譯〕
""".strip()


async def jlpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    text = get_message_text(update)
    if not text:
        return

    url = parse_url(text)

    if url:
        text += "\n" + await load_url(url)

    res = generate(text, SYSTEM_PROMPT_V1)
    await update.message.reply_text(str(res))
