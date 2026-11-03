using UnityEngine;

public class ToPuzzle : MonoBehaviour
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
            if (UiPointer.IsClickOn("Button (Legacy)"))
            {
                joystick.SetActive(false);
                NowCamera.SetActive(false);
                NextCamera.SetActive(true);
                canva2.SetActive(true);
                canva.SetActive(false);
            }
        }

    }
}
