using UnityEngine;

/// <summary>
/// 用 Animator 的 bool 参数驱动讲解文字的进出动画。
/// 两个按钮分别绑到 <see cref="PlayIn"/> 与 <see cref="PlayOut"/>。
/// </summary>
public class Movetext1 : MonoBehaviour
{
    [Tooltip("控制讲解文字的 Animator，留空则取本物体上的")]
    public Animator targetAnimator;

    [Tooltip("Animator 里控制进出的 bool 参数名")]
    public string boolParameter = "IsPlay";

    private void Awake()
    {
        if (targetAnimator == null)
        {
            targetAnimator = GetComponent<Animator>();
        }
    }

    /// <summary>让讲解文字进场。</summary>
    public void PlayIn()
    {
        if (targetAnimator != null)
        {
            targetAnimator.SetBool(boolParameter, true);
        }
    }

    /// <summary>让讲解文字退场。</summary>
    public void PlayOut()
    {
        if (targetAnimator != null)
        {
            targetAnimator.SetBool(boolParameter, false);
        }
    }
}
