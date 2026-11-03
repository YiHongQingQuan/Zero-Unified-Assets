using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;

public class FunctionCanvas : MonoBehaviour
{
    public GameObject ai;
    public GameObject ESCButton;
    public GameObject AIButton;
    public GameObject ESCAIButton;
    public GameObject joystick;


    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (EventSystem.current.currentSelectedGameObject.name == "ESCButton")
            {
                SceneManager.LoadScene("StartUI");
            }
            if (EventSystem.current.currentSelectedGameObject.name == "AIButton")
            {
                ai.SetActive(true);
                //ESCAIButton.SetActive(true);
                joystick.SetActive(false);
                ESCButton.SetActive(false);
                AIButton.SetActive(false);
                
            }
            if (EventSystem.current.currentSelectedGameObject.name == "ESCAIButton")
            {
                ai.SetActive(false);
                joystick.SetActive(true);
                ESCButton.SetActive(true);
                AIButton.SetActive(true);
                //ESCAIButton.SetActive(false);
            }
        }
    }
}
