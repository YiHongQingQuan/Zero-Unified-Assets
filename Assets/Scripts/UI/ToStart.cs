using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;

public class ToStart : MonoBehaviour
{
    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (EventSystem.current.currentSelectedGameObject.name == "ESCButton")
            {
                SceneManager.LoadScene("StartUI");
            }
        }
    }
}
