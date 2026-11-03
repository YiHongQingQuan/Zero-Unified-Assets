using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 文字输入版对话：回车提交后先显示自己说的话，再把问题发给 AI 并逐字显示回答。
/// </summary>
public class TalkManager : MonoBehaviour
{
    [Header("引用")]
    public DeepSeekAPI deepSeek;
    public DialogueView dialogueView;
    public InputField inputField;

    private void OnEnable()
    {
        if (inputField != null)
        {
            inputField.onSubmit.AddListener(OnSubmit);
        }
    }

    private void OnDisable()
    {
        if (inputField != null)
        {
            inputField.onSubmit.RemoveListener(OnSubmit);
        }
    }

    private void OnSubmit(string content)
    {
        inputField.text = string.Empty;

        if (string.IsNullOrWhiteSpace(content))
        {
            Debug.Log("[TalkManager] 输入内容为空，已忽略。");
            return;
        }

        dialogueView.AppendPlayerLine(content);
        deepSeek.SendToDeepSeek(content, OnReply);
    }

    private void OnReply(string content)
    {
        dialogueView.PlayReply(deepSeek.aiCharacter.name, content);
    }
}
