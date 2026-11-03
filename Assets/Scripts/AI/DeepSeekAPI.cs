using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public class DeepSeekAPI : MonoBehaviour
{
    public GameObject loadingImage;

    [Header("API 设置")]
    // 密钥统一从 Assets/StreamingAssets/api-config.json 读取，不再作为 public 字段。
    // public 字段的值会被 Unity 序列化进 .unity / .prefab，一旦提交仓库密钥就泄露了。
    [Tooltip("留空则使用 api-config.json 中的 deepseekModel")]
    public string modelName = "";

    [Tooltip("留空则使用 api-config.json 中的 deepseekApiUrl")]
    public string apiUrl = "";

    [Header("对话设置")]
    [Range(0, 2)] public float temperature = 0.5f; // 随机度
    [Range(0, 3000)] public int maxTokens = 3000;

    [System.Serializable]
    public class AICharacter
    {
        public string name = "艾小航";
        [TextArea(0, 3)]
        public string aiNotice = "你是航天文化馆的讲解员，负责用非常简洁的语言讲解航天知识(注意你只负责讲解，而不是告诉用户怎么参观或指导如何讲解，且讲解内容禁止换行，这一点很重要：讲解内容不要换行)";
    }
    [SerializeField] public AICharacter aiCharacter;
    public delegate void DialogueCallback(string content);

    public void SendToDeepSeek(string message, DialogueCallback callback)
    {
        loadingImage.SetActive(true);
        StartCoroutine(PostRequest(message, callback));
    }

    IEnumerator PostRequest(string message, DialogueCallback callback)
    {
        List<Message> messages = new List<Message>()
        {
            new Message { role = "system", content = aiCharacter.aiNotice },
            new Message { role = "user", content = message }
        };

        ApiConfigData config = ApiConfig.Current; // 密钥与默认模型/地址来自 StreamingAssets/api-config.json
        ChatRequest requestBody = new ChatRequest
        {
            model = string.IsNullOrEmpty(modelName) ? config.deepseekModel : modelName, // 模型名称
            messages = messages, // 对话信息列表
            temperature = temperature, // 随机度
            max_tokens = maxTokens, // 最大token数
        };
        string jsonInformation = JsonUtility.ToJson(requestBody); // 把requestBody转换成json
        UnityWebRequest request = CreateWebRequest(jsonInformation, config);
        yield return request.SendWebRequest();

        Debug.Log(request.downloadHandler.text);
        DeepSeekResponse response = JsonUtility.FromJson<DeepSeekResponse>(request.downloadHandler.text);
        callback?.Invoke(response.choices[0].message.content);
        loadingImage.SetActive(false);
        request.Dispose();
    }


    private UnityWebRequest CreateWebRequest(string jsonInformation, ApiConfigData config)
    {
        string url = string.IsNullOrEmpty(apiUrl) ? config.deepseekApiUrl : apiUrl;
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonInformation);
        UnityWebRequest request = new UnityWebRequest(url, "POST");
        request.uploadHandler = new UploadHandlerRaw(bodyRaw); // 设置上传处理器
        request.downloadHandler = new DownloadHandlerBuffer(); // 设置下载处理器
        request.SetRequestHeader("Content-type", "application/json"); // 设置请求头
        request.SetRequestHeader("Authorization", "Bearer " + config.deepseekApiKey); // 设置认证头，密钥来自 api-config.json
        request.SetRequestHeader("Accept", "application/json"); // 设置接受类型
        return request;
    }

    [System.Serializable]
    public class ChatRequest
    {
        public string model;
        public List<Message> messages;
        public float temperature;
        public int max_tokens;
    }

    [System.Serializable]
    public class Message
    {
        public string role;
        public string content;
        public float temperature;
        public int max_tokens;
    }

    [System.Serializable]
    private class Choice
    {
        public Message message; // 生成的内容
    }

    [System.Serializable]
    private class DeepSeekResponse
    {
        public Choice[] choices; // 生成的选择列表
    }
}
