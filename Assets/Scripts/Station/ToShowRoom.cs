using UnityEngine;
using UnityEngine.EventSystems;

public class ToShowRoom : MonoBehaviour
{
    [Header("画布")]
    public GameObject leadCanvas;
    public GameObject showRoomCanvas;
    public GameObject functionCanvas;
    public GameObject joystick;

    [Header("摄像机")]
    public GameObject mainCamera;
    public GameObject showRoomCamera;

    // Update is called once per frame
    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (EventSystem.current.currentSelectedGameObject.name == "ToShowButton")
            {
                showRoomCanvas.SetActive(true);
                functionCanvas.SetActive(false);
                joystick.SetActive(false);
                showRoomCamera.SetActive(true);
                mainCamera.SetActive(false);
                leadCanvas.SetActive(false);
            }
        }
    }
}
