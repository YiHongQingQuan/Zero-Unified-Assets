using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// 调用 DeepSeek 的对话接口，把回答通过回调交给调用方。
/// 密钥与默认的模型名 / 接口地址来自 Assets/StreamingAssets/api-config.json。
/// </summary>
public class DeepSeekAPI : MonoBehaviour
{
    [Tooltip("请求期间显示的加载提示")]
    public GameObject loadingImage;

    [Header("API 设置")]
    [Tooltip("留空则使用 api-config.json 中的 deepseekModel")]
    public string modelName = string.Empty;

    [Tooltip("留空则使用 api-config.json 中的 deepseekApiUrl")]
    public string apiUrl = string.Empty;

    [Header("对话设置")]
    [Tooltip("随机度，0 最稳定、2 最发散")]
    [Range(0f, 2f)] public float temperature = 0.5f;

    [Tooltip("单次回答的最大 token 数")]
    [Range(0, 3000)] public int maxTokens = 3000;

    [Serializable]
    public class AICharacter
    {
        public string name = "艾小航";

        [TextArea(0, 3)]
        public string aiNotice =
            "你是航天文化馆的讲解员，负责用非常简洁的语言讲解航天知识" +
            "(注意你只负责讲解，而不是告诉用户怎么参观或指导如何讲解，" +
            "且讲解内容禁止换行，这一点很重要：讲解内容不要换行)";
    }

    [SerializeField] public AICharacter aiCharacter;

    /// <summary>回答回调。请求失败时传入 <see cref="FallbackReply"/>。</summary>
    public delegate void DialogueCallback(string content);

    private const string FallbackReply = "抱歉，我暂时联系不上讲解服务，请稍后再试。";

    /// <summary>发起一次对话，回答通过 <paramref name="callback"/> 返回。</summary>
    public void SendToDeepSeek(string message, DialogueCallback callback)
    {
        StartCoroutine(PostRequest(message, callback));
    }

    private IEnumerator PostRequest(string message, DialogueCallback callback)
    {
        SetLoading(true);

        string reply;
        using (UnityWebRequest request = CreateWebRequest(BuildBody(message)))
        {
            yield return request.SendWebRequest();
            reply = ReadReply(request);
        }

        SetLoading(false);
        callback?.Invoke(string.IsNullOrEmpty(reply) ? FallbackReply : reply);
    }

    private string BuildBody(string message)
    {
        ApiConfigData config = ApiConfig.Current;

        var body = new ChatRequest
        {
            model = string.IsNullOrEmpty(modelName) ? config.deepseekModel : modelName,
            messages = new List<Message>
            {
                new Message { role = "system", content = aiCharacter.aiNotice },
                new Message { role = "user", content = message }
            },
            temperature = temperature,
            max_tokens = maxTokens
        };

        return JsonUtility.ToJson(body);
    }

    private UnityWebRequest CreateWebRequest(string json)
    {
        string url = string.IsNullOrEmpty(apiUrl) ? ApiConfig.Current.deepseekApiUrl : apiUrl;

        var request = new UnityWebRequest(url, "POST")
        {
            uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json)),
            downloadHandler = new DownloadHandlerBuffer()
        };

        request.SetRequestHeader("Content-Type", "application/json");
        request.SetRequestHeader("Authorization", "Bearer " + ApiConfig.Current.deepseekApiKey);
        request.SetRequestHeader("Accept", "application/json");
        return request;
    }

    /// <summary>从响应里取出回答文本；失败时记日志并返回 null。</summary>
    private static string ReadReply(UnityWebRequest request)
    {
        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("[DeepSeekAPI] 请求失败：" + request.error);
            return null;
        }

        DeepSeekResponse response = JsonUtility.FromJson<DeepSeekResponse>(request.downloadHandler.text);

        if (response == null || response.choices == null || response.choices.Length == 0)
        {
            Debug.LogError("[DeepSeekAPI] 返回内容为空：" + request.downloadHandler.text);
            return null;
        }

        return response.choices[0].message?.content;
    }

    private void SetLoading(bool visible)
    {
        if (loadingImage != null)
        {
            loadingImage.SetActive(visible);
        }
    }

    // ---- 请求 / 响应的数据结构，字段由 JsonUtility 反射填充 ----

    [Serializable]
    public class ChatRequest
    {
        public string model;
        public List<Message> messages;
        public float temperature;
        public int max_tokens;
    }

    [Serializable]
    public class Message
    {
        public string role;
        public string content;
    }

    [Serializable]
    private class Choice
    {
        public Message message;
    }

    [Serializable]
    private class DeepSeekResponse
    {
        public Choice[] choices;
    }
}
