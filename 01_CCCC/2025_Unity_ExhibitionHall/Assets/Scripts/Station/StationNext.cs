using UnityEngine;

/// <summary>
/// 空间站讲解翻页：切换到下一段讲解内容。
/// 把按钮的 <c>onClick</c> 指到 <see cref="ShowNext"/> 即可。
/// </summary>
public class StationNext : MonoBehaviour
{
    [Header("画布")]
    public GameObject NowCanva;
    public GameObject NextCanva;

    [Header("讲解对象")]
    public GameObject NowObject;
    public GameObject NextObject;

    /// <summary>显示下一段讲解。</summary>
    public void ShowNext()
    {
        NowObject.SetActive(false);
        NextObject.SetActive(true);

        NextCanva.SetActive(true);
        NowCanva.SetActive(false);
    }
}
