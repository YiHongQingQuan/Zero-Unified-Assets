using UnityEngine;
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
            if (UiPointer.IsClickOn("ESCButton"))
            {
                SceneManager.LoadScene("StartUI");
            }
            if (UiPointer.IsClickOn("AIButton"))
            {
                ai.SetActive(true);
                //ESCAIButton.SetActive(true);
                joystick.SetActive(false);
                ESCButton.SetActive(false);
                AIButton.SetActive(false);
                
            }
            if (UiPointer.IsClickOn("ESCAIButton"))
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
