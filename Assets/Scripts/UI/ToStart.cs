using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// 返回启动页。把按钮的 <c>onClick</c> 指到 <see cref="BackToStartUI"/> 即可。
/// </summary>
public class ToStart : MonoBehaviour
{
    /// <summary>加载启动场景。</summary>
    public void BackToStartUI()
    {
        SceneManager.LoadScene("StartUI");
    }
}
