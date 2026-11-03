using System.Collections.Generic;
using System.Text;

/// <summary>
/// 按「显示宽度」给对话文本折行。
///
/// 全角字符（中文、全角标点）占 1 个单位，半角字符（英文、数字）占 0.5 个单位。
/// 按宽度而不是按字数折行，中英文混排时右侧边缘才能对齐。
/// </summary>
public static class DialogueLayout
{
    /// <summary>全角字符的宽度单位。</summary>
    public const float FullWidth = 1f;

    /// <summary>半角字符的宽度单位。</summary>
    public const float HalfWidth = 0.5f;

    /// <summary>每行都用相同宽度折行。</summary>
    public static List<string> Wrap(string text, float maxWidth)
    {
        return Wrap(text, maxWidth, maxWidth);
    }

    /// <summary>首行和后续行使用不同宽度的折行（首行需给行尾标签留位置时用）。</summary>
    public static List<string> Wrap(string text, float firstLineWidth, float restWidth)
    {
        var lines = new List<string>();
        if (string.IsNullOrEmpty(text))
        {
            lines.Add(string.Empty);
            return lines;
        }

        var current = new StringBuilder();
        float budget = firstLineWidth;
        float width = 0f;

        foreach (char c in text)
        {
            if (c == '\n')
            {
                lines.Add(current.ToString());
                current.Length = 0;
                width = 0f;
                budget = restWidth;
                continue;
            }

            float charWidth = CharWidth(c);
            if (width + charWidth > budget && current.Length > 0)
            {
                lines.Add(current.ToString());
                current.Length = 0;
                width = 0f;
                budget = restWidth;
            }

            current.Append(c);
            width += charWidth;
        }

        lines.Add(current.ToString());
        return lines;
    }

    /// <summary>单个字符占用的显示宽度。</summary>
    public static float CharWidth(char c)
    {
        return c < 128 ? HalfWidth : FullWidth;
    }

    /// <summary>整段文本的显示宽度（换行符不计）。</summary>
    public static float Measure(string text)
    {
        float width = 0f;
        if (text == null)
        {
            return width;
        }

        foreach (char c in text)
        {
            if (c != '\n')
            {
                width += CharWidth(c);
            }
        }

        return width;
    }
}
