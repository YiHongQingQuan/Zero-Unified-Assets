using UnityEngine;

/// <summary>
/// 空间站内的按钮总控：讲解翻页、拆解演示、返回漫游。
/// 四个按钮分别绑到四个公开方法。
/// </summary>
public class StationStart : MonoBehaviour
{
    [Header("舱段讲解")]
    public GameObject NowCanva;
    public GameObject NextCanva;
    public GameObject NowObject;
    public GameObject NextObject;

    [Header("拆解动画")]
    public GameObject moveButton;
    public GameObject moveBackButton;
    public GameObject introduceButton;

    [Header("返回")]
    public GameObject joystick;
    public GameObject fuctionCanva;
    public GameObject showCamera;
    public GameObject mainCamera;

    /// <summary>显示下一段舱段讲解。</summary>
    public void OpenIntroduction()
    {
        NowObject.SetActive(false);
        NextObject.SetActive(true);

        NextCanva.SetActive(true);
        NowCanva.SetActive(false);
    }

    /// <summary>进入拆解演示：按钮切换为「复位」，讲解入口暂时收起。</summary>
    public void StartDisassembly()
    {
        moveBackButton.SetActive(true);
        SetActive(introduceButton, false);
        moveButton.SetActive(false);
    }

    /// <summary>结束拆解演示：恢复「拆解」与讲解入口。</summary>
    public void RestoreModules()
    {
        moveBackButton.SetActive(false);
        SetActive(introduceButton, true);
        moveButton.SetActive(true);
    }

    /// <summary>返回漫游。</summary>
    public void BackToRoaming()
    {
        fuctionCanva.SetActive(true);
        showCamera.SetActive(false);
        mainCamera.SetActive(true);
        joystick.SetActive(true);
        NowCanva.SetActive(false);
    }

    private static void SetActive(GameObject target, bool active)
    {
        if (target != null)
        {
            target.SetActive(active);
        }
    }
}
