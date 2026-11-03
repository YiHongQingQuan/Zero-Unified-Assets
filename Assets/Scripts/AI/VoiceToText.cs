using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using UnityEngine.UI;
using System.Text;
using System;

public class VoiceToText : MonoBehaviour
{
    private AudioClip audioClip;

    [Header("API 设置")]
    public DeepSeekAPI deepseekAPI;
    // 百度语音的 api / secret 不再作为 public 字段保存，
    // 统一从 Assets/StreamingAssets/api-config.json 读取，避免随场景文件泄露。

    [Header("对话设置")]
    public Text dialogueText;
    public float typingSpeed = 0.05f;

    [Header("图像")]
    public GameObject voiceImage;
    public GameObject waitImage;

    private void Update()
    {
        if (Input.GetMouseButtonDown(0) && UiPointer.IsClickOn("VoiceButton"))
        {
            Debug.Log("录音按钮被按下");
            voiceImage.SetActive(true);
            StartCoroutine(RecordAndRecognize());
        }
    }

    IEnumerator RecordAndRecognize()
    {
        // 录音
        Debug.Log("开始录音");
        audioClip = Microphone.Start(null, false, 5, 16000);
        while (Microphone.GetPosition(null) < 16000 * 5) // 检测已采集到的样本数
        {
            yield return null;
        }
        Microphone.End(null); // 停止录音
        yield return new WaitForSeconds(5);
        
        voiceImage.SetActive(false);
        waitImage.SetActive(true);

        // 将音频数据转为PCM格式
        byte[] pcmInfomation = ToPCM(audioClip);

        // 获取token
        string token = "";
        ApiConfigData config = ApiConfig.Current; // 密钥来自 StreamingAssets/api-config.json
        WWWForm tokenForm = new WWWForm(); // 创建请求体
        tokenForm.AddField("grant_type", "client_credentials"); // 授权类型
        tokenForm.AddField("client_id", config.baiduApiKey);
        tokenForm.AddField("client_secret", config.baiduSecretKey); // 

        using (UnityWebRequest tokenRequest = UnityWebRequest.Post(
            "https://aip.baidubce.com/oauth/2.0/token", tokenForm))
        {
            yield return tokenRequest.SendWebRequest();  // 发起网络请求
            if (tokenRequest.result == UnityWebRequest.Result.Success)
            {
                //将返回的JSON字符串反序列化为TokenResponse 类
                TokenResponse response = JsonUtility.FromJson<TokenResponse>(tokenRequest.downloadHandler.text);
                token = response.access_token; // 获取access_token
            }
        }

        // 构建请求体
        string cuid = "设备唯一标识";
        string base64Data = Convert.ToBase64String(pcmInfomation); // 转为 Base64 字符串

        RequestBody requestBody = new RequestBody
        {
            format = "pcm",
            rate = 16000,
            channel = 1,
            cuid = cuid,
            token = token,
            speech = base64Data,
            len = pcmInfomation.Length
        };

        string jsonInfomation = JsonUtility.ToJson(requestBody); // 将请求体序列化为JSON字符串
        byte[] utfInfomation = Encoding.UTF8.GetBytes(jsonInfomation); // 将JSON字符串转换为UTF-8字节数组

        // 发送请求
        using (UnityWebRequest request = new UnityWebRequest(
            "https://vop.baidu.com/server_api", "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(utfInfomation); // 配置上传处理器
            request.downloadHandler = new DownloadHandlerBuffer(); // 配置下载处理器
            request.SetRequestHeader("Content-Type", "application/json"); // 设置请求头

            yield return request.SendWebRequest(); // 发送请求

            if (request.result == UnityWebRequest.Result.Success)
            {
                string result = "";
                if (request.result == UnityWebRequest.Result.Success)
                {
                    string responseInformation = request.downloadHandler.text; // 获取响应数据
                    RecognitionResponse response = JsonUtility.FromJson<RecognitionResponse>(responseInformation);// 反序列化JSON
                    result = response.result[0]; // 提取语音识别结果
                }

                //Debug.Log("识别结果：" + result);
                waitImage.SetActive(false);
                dialogueText.text += "\n————————————————————————————————————\n\n";
                float num = 0f;
                int line = 0;
                dialogueText.text += "                   ";
                if (result.Length < 28)
                {
                    int rem = 28 - result.Length;
                    for (float i = 0; i < rem; i += 0.3f)
                    {
                        dialogueText.text += " ";
                    }
                    dialogueText.text += result + ":星航者";
                    goto go;
                }
                foreach (char i in result)
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

            go: deepseekAPI.SendToDeepSeek(result, HandleAIResponse);
            }
        }
    }

    // PCM转换
    byte[] ToPCM(AudioClip clip)
    {
        float[] arr = new float[clip.samples * clip.channels]; // 声道数量
        clip.GetData(arr, 0); // 填充音频数据，记录每个样本的振幅

        byte[] pcmInfomation = new byte[arr.Length * 2]; // PCM数据的字节数组
        for (int i = 0; i < arr.Length; i++)
        {
            short tmp = (short)(arr[i] * short.MaxValue); // 将浮点值映射到short的整型范围
            pcmInfomation[i * 2] = (byte)(tmp & 0xFF); // 提取低位字节
            pcmInfomation[i * 2 + 1] = (byte)(tmp >> 8); // 提取高位字节
        }
        return pcmInfomation;
    }

    // 请求体结构
    [System.Serializable]
    private class RequestBody
    {
        public string format; //音频格式
        public int rate; //采样率
        public int channel; //声道
        public string cuid; //设备标识
        public string token; //access_token
        public string speech; //音频数据
        public int len; //音频数据长度
    }

    [System.Serializable]
    private class TokenResponse
    {
        public string access_token;
    }

    [System.Serializable]
    private class RecognitionResponse
    {
        public string corpus_no;
        public string err_msg;
        public int err_no;
        public string[] result;
        public string sn;
    }

    private void HandleAIResponse(string content)
    {
        StopAllCoroutines();
        string s = content;
        StartCoroutine(ShowText("艾小航:" + s));
    }

    private IEnumerator ShowText(string text)
    {
        StringBuilder sb = new StringBuilder(dialogueText.text); // 使用当前的文本内容
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
