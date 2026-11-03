using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// 功能面板：返回启动页、以及 AI 面板的开合。
/// 三个按钮分别绑到 <see cref="BackToStartUI"/>、<see cref="OpenAiPanel"/>、<see cref="CloseAiPanel"/>。
/// </summary>
public class FunctionCanvas : MonoBehaviour
{
    [Header("AI 面板")]
    public GameObject ai;

    [Header("其它界面元素")]
    public GameObject ESCButton;
    public GameObject AIButton;
    public GameObject ESCAIButton;
    public GameObject joystick;

    /// <summary>返回启动页。</summary>
    public void BackToStartUI()
    {
        SceneManager.LoadScene("StartUI");
    }

    /// <summary>打开 AI 面板，暂时收起摇杆与功能按钮。</summary>
    public void OpenAiPanel()
    {
        ai.SetActive(true);
        joystick.SetActive(false);
        ESCButton.SetActive(false);
        AIButton.SetActive(false);
    }

    /// <summary>收起 AI 面板，恢复摇杆与功能按钮。</summary>
    public void CloseAiPanel()
    {
        ai.SetActive(false);
        joystick.SetActive(true);
        ESCButton.SetActive(true);
        AIButton.SetActive(true);
    }
}
