using UnityEngine;

/// <summary>
/// 从空间站进入展厅：切换相机与画布。
/// 把按钮的 <c>onClick</c> 指到 <see cref="EnterShowRoom"/> 即可。
/// </summary>
public class ToShowRoom : MonoBehaviour
{
    [Header("画布")]
    public GameObject leadCanvas;
    public GameObject showRoomCanvas;
    public GameObject functionCanvas;
    public GameObject joystick;

    [Header("摄像机")]
    public GameObject mainCamera;
    public GameObject showRoomCamera;

    /// <summary>切换到展厅相机与展厅画布。</summary>
    public void EnterShowRoom()
    {
        showRoomCanvas.SetActive(true);
        functionCanvas.SetActive(false);
        joystick.SetActive(false);
        showRoomCamera.SetActive(true);
        mainCamera.SetActive(false);
        leadCanvas.SetActive(false);
    }
}
