using UnityEngine;
using UnityEngine.EventSystems;

public class Back : MonoBehaviour
{
    public GameObject joystick;
    public GameObject canva;
    public GameObject canva2;
    public GameObject NowCamera;
    public GameObject NextCamera;
    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            if (EventSystem.current.currentSelectedGameObject.name == "Button (Legacy)")
            {
                joystick.SetActive(true);
                NowCamera.SetActive(false);
                NextCamera.SetActive(true);
                canva2.SetActive(false);
                canva.SetActive(false);
            }
        }

    }
}

