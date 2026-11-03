using UnityEngine;

public class Movetext1 : MonoBehaviour
{
    private Animator animator;

    private void Start()
    {
        animator = GetComponent<Animator>();
    }

    public void Update()
    {
        if (!Input.GetMouseButtonDown(0)) return;

        if (UiPointer.IsClickOn("MoveButton"))
        {
            animator.SetBool("IsPlay", true);
        }
        if (UiPointer.IsClickOn("MoveBackButton"))
        {
            animator.SetBool("IsPlay", false);
        }
    }
}
