using UnityEngine;
using UnityEngine.UI;

public class AnimationController : MonoBehaviour
{
    public Animator targetAnimator;
    public Button triggerButton;
    public string animationName;


    void Start()
    {
        triggerButton.onClick.AddListener(PlayAnimation);
    }

    void PlayAnimation()
    {
        targetAnimator.Play(animationName); // 填写动画片段名称
    }
}
