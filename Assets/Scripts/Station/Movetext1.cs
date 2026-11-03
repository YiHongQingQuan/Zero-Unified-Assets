using UnityEngine;
using UnityEngine.EventSystems;

public class Movetext1 : MonoBehaviour
{
    private Animator animator;

    private void Start()
    {
        animator = GetComponent<Animator>();
    }

    public void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            var currentSelected = EventSystem.current?.currentSelectedGameObject;
            if (currentSelected != null && EventSystem.current.currentSelectedGameObject.name == "MoveButton")
            {
                animator.SetBool("IsPlay", true);
                Debug.Log("播放完成");
            }
            if (currentSelected != null && EventSystem.current.currentSelectedGameObject.name == "MoveBackButton")
            {
                animator.SetBool("IsPlay", false);
                Debug.Log("播放完成");
            }
        }
        
    }
}
