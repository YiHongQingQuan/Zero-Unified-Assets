using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// 语音提问：录音 → 百度语音识别转文字 → 交给 DeepSeek 回答。
/// 识别与回答都通过 <see cref="DialogueView"/> 显示到对话框。
/// </summary>
public class VoiceToText : MonoBehaviour
{
    [Header("引用")]
    public DeepSeekAPI deepSeek;
    public DialogueView dialogueView;

    [Header("录音")]
    [Tooltip("单次录音时长（秒）")]
    public int recordSeconds = 5;

    [Tooltip("采样率，百度短语音识别要求 16000")]
    public int sampleRate = 16000;

    [Header("提示图")]
    [Tooltip("录音时显示")]
    public GameObject recordingHint;

    [Tooltip("识别等待时显示")]
    public GameObject waitingHint;

    private const string TokenUrl = "https://aip.baidubce.com/oauth/2.0/token";
    private const string RecognitionUrl = "https://vop.baidu.com/server_api";

    private AudioClip clip;
    private bool busy;

    private void Update()
    {
        if (busy || !Input.GetMouseButtonDown(0) || !UiPointer.IsClickOn("VoiceButton"))
        {
            return;
        }

        StartCoroutine(AskByVoice());
    }

    /// <summary>一次完整的「录音 → 识别 → 提问」流程。</summary>
    private IEnumerator AskByVoice()
    {
        busy = true;
        ShowHints(recording: true, waiting: false);

        yield return Record();
        ShowHints(recording: false, waiting: true);

        string question = null;
        yield return Recognize(ConvertToPcm16(clip), result => question = result);

        ShowHints(recording: false, waiting: false);
        busy = false;

        if (string.IsNullOrEmpty(question))
        {
            Debug.LogWarning("[VoiceToText] 没有识别到内容，本次提问已取消。");
            yield break;
        }

        dialogueView.AppendPlayerLine(question);
        deepSeek.SendToDeepSeek(question,
            reply => dialogueView.PlayReply(deepSeek.aiCharacter.name, reply));
    }

    /// <summary>录满设定时长，或超时后停止。</summary>
    private IEnumerator Record()
    {
        Microphone.End(null);
        clip = Microphone.Start(null, false, recordSeconds, sampleRate);

        int expectedSamples = sampleRate * recordSeconds;
        float deadline = Time.realtimeSinceStartup + recordSeconds + 2f;

        while (Microphone.GetPosition(null) < expectedSamples && Time.realtimeSinceStartup < deadline)
        {
            yield return null;
        }

        Microphone.End(null);
    }

    /// <summary>把音频发到百度语音识别，回调返回识别文本；失败时回调 null。</summary>
    private IEnumerator Recognize(byte[] pcm, Action<string> onResult)
    {
        string token = null;
        yield return RequestToken(value => token = value);

        if (string.IsNullOrEmpty(token))
        {
            onResult(null);
            yield break;
        }

        var body = new RecognitionRequest
        {
            format = "pcm",
            rate = sampleRate,
            channel = 1,
            cuid = DeviceId(),
            token = token,
            speech = Convert.ToBase64String(pcm),
            len = pcm.Length
        };

        using (var request = new UnityWebRequest(RecognitionUrl, "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(body)));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("[VoiceToText] 识别请求失败：" + request.error);
                onResult(null);
                yield break;
            }

            RecognitionResponse response = JsonUtility.FromJson<RecognitionResponse>(request.downloadHandler.text);

            if (response == null || response.result == null || response.result.Length == 0)
            {
                Debug.LogWarning("[VoiceToText] 识别失败：" + (response == null ? "响应为空" : response.err_msg));
                onResult(null);
                yield break;
            }

            onResult(response.result[0]);
        }
    }

    /// <summary>用 API Key / Secret Key 换取 access_token。</summary>
    private IEnumerator RequestToken(Action<string> onToken)
    {
        var form = new WWWForm();
        form.AddField("grant_type", "client_credentials");
        form.AddField("client_id", ApiConfig.Current.baiduApiKey);
        form.AddField("client_secret", ApiConfig.Current.baiduSecretKey);

        using (UnityWebRequest request = UnityWebRequest.Post(TokenUrl, form))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("[VoiceToText] 获取 access_token 失败：" + request.error);
                onToken(null);
                yield break;
            }

            TokenResponse response = JsonUtility.FromJson<TokenResponse>(request.downloadHandler.text);
            onToken(response == null ? null : response.access_token);
        }
    }

    /// <summary>把 AudioClip 的浮点采样转成 16 位小端 PCM。</summary>
    private static byte[] ConvertToPcm16(AudioClip source)
    {
        int sampleCount = source.samples * source.channels;
        var samples = new float[sampleCount];
        source.GetData(samples, 0);

        var pcm = new byte[sampleCount * 2];
        for (int i = 0; i < sampleCount; i++)
        {
            short value = (short)(samples[i] * short.MaxValue);
            pcm[i * 2] = (byte)(value & 0xFF);
            pcm[i * 2 + 1] = (byte)(value >> 8);
        }

        return pcm;
    }

    private void ShowHints(bool recording, bool waiting)
    {
        if (recordingHint != null)
        {
            recordingHint.SetActive(recording);
        }

        if (waitingHint != null)
        {
            waitingHint.SetActive(waiting);
        }
    }

    private static string DeviceId()
    {
        string id = SystemInfo.deviceUniqueIdentifier;
        return string.IsNullOrEmpty(id) ? "unity-device" : id;
    }

    // ---- 请求 / 响应的数据结构，字段由 JsonUtility 反射填充 ----

    [Serializable]
    private class RecognitionRequest
    {
        public string format;
        public int rate;
        public int channel;
        public string cuid;
        public string token;
        public string speech;
        public int len;
    }

    [Serializable]
    private class TokenResponse
    {
        public string access_token;
    }

    [Serializable]
    private class RecognitionResponse
    {
        public string err_msg;
        public int err_no;
        public string[] result;
    }
}
