using UnityEngine;
using UnityEngine.EventSystems;

public class BackFromPicture : MonoBehaviour
{
    public Transform canvas;
    public GameObject button;

    
    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (EventSystem.current.currentSelectedGameObject.name == "Button (Legacy)")
            {
                canvas.gameObject.SetActive(false);
            }
        }
    }
}
