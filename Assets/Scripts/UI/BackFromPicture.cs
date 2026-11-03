using UnityEngine;

public class BackFromPicture : MonoBehaviour
{
    public Transform canvas;
    public GameObject button;

    
    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (UiPointer.IsClickOn("Button (Legacy)"))
            {
                canvas.gameObject.SetActive(false);
            }
        }
    }
}
