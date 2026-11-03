using UnityEngine;
using UnityEngine.EventSystems;

public class Next : MonoBehaviour
{
    public GameObject NowCanva;
    public GameObject NextCanva;
    public GameObject NowObject;
    public GameObject NextObject;
    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            if (EventSystem.current.currentSelectedGameObject.name == "Next")
            {
                NowObject.SetActive(false);
                NextObject.SetActive(true);

                NextCanva.SetActive(true);
                NowCanva.SetActive(false);
            }
        }
        
    }
}
