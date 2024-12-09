SUMMARY_PROMPT = """
請以台灣繁體中文摘取以下內容的核心重點。內容可能包括網頁、文章、論文、影片字幕或逐字稿。

# 步驟
1. 保留核心訊息，確保每條重點表達清晰且準確，避免加入任何虛構或未經證實的資訊。適度保留細節，避免過度簡潔。
2. 若發現相似或重複的資訊，請將其合併為一條重點，以保持內容連貫且流暢。
3. 使用符合台灣用語習慣的表達方式，排除不必要的細節，提高可讀性。
4. 總結完成後，添加至少三個與主題相關的英文 hashtag，以空格分隔（例如 #Sustainability #Innovation），便於標記和分類。
5. 確保最終輸出內容為台灣繁體中文。

輸入：
{text}
""".strip()  # noqa
