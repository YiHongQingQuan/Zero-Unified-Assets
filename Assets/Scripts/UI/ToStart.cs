using UnityEngine;
using UnityEngine.SceneManagement;

public class ToStart : MonoBehaviour
{
    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (UiPointer.IsClickOn("ESCButton"))
            {
                SceneManager.LoadScene("StartUI");
            }
        }
    }
}
