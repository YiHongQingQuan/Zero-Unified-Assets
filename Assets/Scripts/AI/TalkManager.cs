using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.UI;

public class TalkManager : MonoBehaviour
{
    public DeepSeekAPI deepseekAPI;
    public InputField inputField;
    public Text dialogueText;
    public Text inputText;
    private string characterName;
    public float typingSpeed = 0.03f;

    private void Start()
    {
        characterName = deepseekAPI.aiCharacter.name;
        inputField.onSubmit.AddListener((text) =>
        {
            if (string.IsNullOrEmpty(text))
            {
                Debug.Log("输入内容不能为空");
                return;
            }
            dialogueText.text += "\n————————————————————————————————————\n\n";
            float num = 0f;
            int line = 0;
            dialogueText.text += "                   ";
            if (text.Length < 28)
            {
                int rem = 28 - text.Length;
                for (float i = 0; i < rem; i += 0.3f)
                {
                    dialogueText.text += " ";
                }
                dialogueText.text += text + ":星航者";
                inputField.text = "";
                goto go;
            }
            foreach (char i in text)
            {
                if (i == ':' || i == '"' || i == '.' || i == '-')
                {
                    num += 0.3f;
                }
                else if (i - '0' <= 9)
                {
                    num += 0.4f;
                }
                else if(i != '\n')
                {
                    num++;
                }
                if (num >= 28)
                {
                    Debug.Log("正在尝试换行");
                    if (line == 0)
                    {
                        dialogueText.text += ":星航者";
                    }
                    dialogueText.text += "\n";
                    dialogueText.text += "                   ";
                    Debug.Log("换行成功");
                    num = 0f;
                }
                dialogueText.text += i.ToString();
            }
            dialogueText.text += "\n";
            inputField.text = "";
            
            go: deepseekAPI.SendToDeepSeek(text, HandleAIResponse);
        });
    }

    private void HandleAIResponse(string content)
    {
        StopAllCoroutines();
        string s = content;
        StartCoroutine(ShowText("艾小航:" + s));
    }

    private IEnumerator ShowText(string text)
    {
        StringBuilder sb = new StringBuilder(dialogueText.text); // 当前文本内容
        sb.AppendLine();
        float num = 0f;
        foreach (char i in text)
        {
            if (i == ':' || i == '"' || i == '.' || i == '-')
            {
                num += 0.3f;
            }
            else if (i - '0' <= 9)
            {
                num += 0.4f;
            }
            else if (i != '\n')
            {
                num++;
            }
            if (num >= 28)
            {
                Debug.Log("正在尝试换行");
                sb.AppendLine();
                sb.Append("          ");
                Debug.Log("换行成功");
                num = 0f;
            }
            Debug.Log(num);
            Debug.Log(i);
            if (i != '\n')
            {
                sb.Append(i.ToString());
                dialogueText.text = sb.ToString();
            }
            
            yield return new WaitForSeconds(typingSpeed);
        }
        num = 0;
    }
}
