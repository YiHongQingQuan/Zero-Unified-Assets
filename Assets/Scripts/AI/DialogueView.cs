using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 对话区的排版与输出，负责三件事：
/// 分隔线、折行后带缩进的正文、以及 AI 回复的逐字显示。
///
/// 折行规则在 <see cref="DialogueLayout"/> 里，这里只负责拼装和播放。
/// </summary>
public class DialogueView : MonoBehaviour
{
    [Tooltip("对话文本控件")]
    public Text output;

    [Tooltip("每个字的显示间隔（秒），在 Awake 时读取一次")]
    public float typingSpeed = 0.03f;

    [Tooltip("每行最大显示宽度，一个全角字符算 1")]
    public float lineWidth = 28f;

    [Tooltip("折行后的左缩进空格数")]
    public int indentSpaces = 19;

    private const string Divider = "————————————————————————————————————";

    private WaitForSeconds typingDelay;
    private Coroutine typingRoutine;

    private void Awake()
    {
        typingDelay = new WaitForSeconds(typingSpeed);
    }

    /// <summary>追加一条玩家发言：内容在前，说话人标签贴在首行行尾。</summary>
    public void AppendPlayerLine(string content, string speaker = "星航者")
    {
        if (output == null)
        {
            return;
        }

        output.text += "\n" + Divider + "\n\n" + BuildPlayerBlock(content, speaker);
    }

    /// <summary>以打字机效果追加一条 AI 回复。</summary>
    public void PlayReply(string speaker, string content)
    {
        if (output == null)
        {
            return;
        }

        StopTyping();
        typingRoutine = StartCoroutine(TypeReply(speaker, content));
    }

    /// <summary>中断正在播放的打字机效果。</summary>
    public void StopTyping()
    {
        if (typingRoutine != null)
        {
            StopCoroutine(typingRoutine);
            typingRoutine = null;
        }
    }

    /// <summary>玩家发言的整块文本：首行给说话人标签留位置，其余行缩进。</summary>
    private string BuildPlayerBlock(string content, string speaker)
    {
        string indent = new string(' ', indentSpaces);
        string tag = ":" + speaker;

        // 首行要让出标签的宽度，否则标签会顶出边界
        float firstLineWidth = Mathf.Max(
            lineWidth - DialogueLayout.Measure(tag), DialogueLayout.FullWidth);

        List<string> lines = DialogueLayout.Wrap(content, firstLineWidth, lineWidth);

        var builder = new StringBuilder();
        builder.Append(indent).Append(lines[0]).Append(tag);

        for (int i = 1; i < lines.Count; i++)
        {
            builder.Append('\n').Append(indent).Append(lines[i]);
        }

        builder.Append('\n');
        return builder.ToString();
    }

    private IEnumerator TypeReply(string speaker, string content)
    {
        string indent = new string(' ', indentSpaces);
        List<string> lines = DialogueLayout.Wrap(content, lineWidth);

        var builder = new StringBuilder(output.text);
        builder.Append('\n').Append(speaker).Append(':');

        for (int i = 0; i < lines.Count; i++)
        {
            if (i > 0)
            {
                builder.Append('\n').Append(indent);
            }

            foreach (char c in lines[i])
            {
                builder.Append(c);
                output.text = builder.ToString();
                yield return typingDelay;
            }
        }

        typingRoutine = null;
    }
}
