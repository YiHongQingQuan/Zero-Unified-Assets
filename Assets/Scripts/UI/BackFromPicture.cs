using UnityEngine;

/// <summary>
/// 关闭正在查看的图片画布。
/// 把按钮的 <c>onClick</c> 指到 <see cref="ClosePicture"/> 即可。
/// </summary>
public class BackFromPicture : MonoBehaviour
{
    [Tooltip("要关闭的画布")]
    public Transform canvas;

    /// <summary>关闭图片画布。</summary>
    public void ClosePicture()
    {
        if (canvas != null)
        {
            canvas.gameObject.SetActive(false);
        }
    }
}
