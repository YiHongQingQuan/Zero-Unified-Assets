using UnityEngine;

/// <summary>
/// 退出拼图界面，恢复漫游状态。
/// 把按钮的 <c>onClick</c> 指到 <see cref="BackToRoaming"/> 即可。
/// </summary>
public class Back : MonoBehaviour
{
    [Header("界面")]
    public GameObject joystick;
    public GameObject canva;
    public GameObject canva2;

    [Header("相机")]
    public GameObject NowCamera;
    public GameObject NextCamera;

    /// <summary>回到漫游：显示摇杆与漫游相机，收起拼图界面。</summary>
    public void BackToRoaming()
    {
        joystick.SetActive(true);
        NowCamera.SetActive(false);
        NextCamera.SetActive(true);
        canva2.SetActive(false);
        canva.SetActive(false);
    }
}
