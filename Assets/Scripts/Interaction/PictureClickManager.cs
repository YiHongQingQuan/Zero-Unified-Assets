using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 点击展品模型，打开对应的图片画布。
///
/// <see cref="transforms"/> 与 <see cref="canvas"/> 按下标一一对应：
/// 射线命中的展品在第几项，就显示第几块画布。
/// </summary>
public class PictureClickManager : MonoBehaviour
{
    [Tooltip("发射射线的相机，留空则使用 Camera.main")]
    public Camera rayCamera;

    [Tooltip("点击后要显示的画布，与 transforms 按下标对应")]
    public List<GameObject> canvas = new List<GameObject>();

    [Tooltip("可点击的展品，与 canvas 按下标对应")]
    public List<Transform> transforms = new List<Transform>();

    private void Update()
    {
        if (!Input.GetMouseButtonDown(0))
        {
            return;
        }

        Camera cam = rayCamera != null ? rayCamera : Camera.main;
        if (cam == null)
        {
            return;
        }

        RaycastHit hit;
        if (!Physics.Raycast(cam.ScreenPointToRay(Input.mousePosition), out hit))
        {
            return;
        }

        // 只遍历两张表都存在的部分，避免下标越界
        int count = Mathf.Min(canvas.Count, transforms.Count);

        for (int i = 0; i < count; i++)
        {
            if (transforms[i] == null || canvas[i] == null)
            {
                continue;
            }

            if (hit.transform == transforms[i])
            {
                canvas[i].SetActive(true);
                return;
            }
        }
    }
}
