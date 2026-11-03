using System;
using System.IO;
using System.Text;
using UnityEngine;

/// <summary>
/// 密钥配置的数据结构，与 Assets/StreamingAssets/api-config.json 一一对应。
/// </summary>
[Serializable]
public class ApiConfigData
{
    [Tooltip("DeepSeek 开放平台的 API Key，形如 sk-xxxxxxxx")]
    public string deepseekApiKey;

    [Tooltip("对话模型名称")]
    public string deepseekModel = "deepseek-chat";

    [Tooltip("对话接口地址")]
    public string deepseekApiUrl = "https://api.deepseek.com/chat/completions";

    [Tooltip("百度智能云应用的 API Key（授权时作为 client_id）")]
    public string baiduApiKey;

    [Tooltip("百度智能云应用的 Secret Key（授权时作为 client_secret）")]
    public string baiduSecretKey;
}

/// <summary>
/// 统一读取 Assets/StreamingAssets/api-config.json 中的密钥。
///
/// 设计目的：密钥不再以 public 字段的形式挂在 MonoBehaviour 上。
/// 因为 Unity 会把 public 字段的值序列化进 .unity / .prefab / .asset 文件，
/// 一旦把这些文件提交到 GitHub，密钥就永久留在了 git 历史里。
///
/// 使用方式：
///   1. 把 Assets/StreamingAssets/api-config.example.json 复制为 api-config.json；
///   2. 填入自己的密钥（该文件已被 .gitignore 排除，不会被提交）；
///   3. 代码中通过 ApiConfig.Current.deepseekApiKey 读取。
/// </summary>
public static class ApiConfig
{
    /// <summary>配置文件名称（放在 StreamingAssets 下）。</summary>
    public const string FileName = "api-config.json";

    /// <summary>示例文件名，随仓库提交，供使用者参考。</summary>
    public const string ExampleFileName = "api-config.example.json";

    private static ApiConfigData current;
    private static bool loaded;

    /// <summary>当前配置。首次访问时从磁盘读取，之后走缓存。</summary>
    public static ApiConfigData Current
    {
        get
        {
            if (!loaded || current == null)
            {
                current = Load();
                loaded = true;
            }
            return current;
        }
    }

    /// <summary>配置文件的完整路径。</summary>
    public static string ConfigPath
    {
        get { return Path.Combine(Application.streamingAssetsPath, FileName); }
    }

    /// <summary>
    /// 从 StreamingAssets 读取配置。文件缺失或格式错误时返回空配置并打日志，
    /// 不会抛异常，方便在没配密钥时先跑通场景。
    /// </summary>
    public static ApiConfigData Load()
    {
        string path = ConfigPath;

        if (!File.Exists(path))
        {
            Debug.LogWarning(
                "[ApiConfig] 未找到配置文件：" + path + "\n" +
                "请把 " + ExampleFileName + " 复制为 " + FileName + " 并填入自己的密钥。");
            return new ApiConfigData();
        }

        try
        {
            string json = File.ReadAllText(path, Encoding.UTF8);
            ApiConfigData data = JsonUtility.FromJson<ApiConfigData>(json);

            if (data == null)
            {
                Debug.LogError("[ApiConfig] 配置解析结果为空，请检查 JSON 格式：" + path);
                return new ApiConfigData();
            }

            if (string.IsNullOrEmpty(data.deepseekApiKey))
            {
                Debug.LogWarning("[ApiConfig] deepseekApiKey 为空，AI 对话将无法使用。");
            }

            return data;
        }
        catch (Exception e)
        {
            Debug.LogError("[ApiConfig] 读取配置失败：" + e.Message);
            return new ApiConfigData();
        }
    }

    /// <summary>丢弃缓存，下次访问 Current 时重新读盘（改完配置后可在运行时调用）。</summary>
    public static void Reload()
    {
        loaded = false;
        current = null;
    }
}
