using UnityEngine;

/// <summary>
/// 从漫游进入拼图界面：切换相机与画布。
/// 把按钮的 <c>onClick</c> 指到 <see cref="EnterPuzzle"/> 即可。
/// </summary>
public class ToPuzzle : MonoBehaviour
{
    [Header("界面")]
    public GameObject joystick;
    public GameObject canva;
    public GameObject canva2;

    [Header("相机")]
    public GameObject NowCamera;
    public GameObject NextCamera;

    /// <summary>切换到拼图相机与拼图画布。</summary>
    public void EnterPuzzle()
    {
        joystick.SetActive(false);
        NowCamera.SetActive(false);
        NextCamera.SetActive(true);
        canva2.SetActive(true);
        canva.SetActive(false);
    }
}
