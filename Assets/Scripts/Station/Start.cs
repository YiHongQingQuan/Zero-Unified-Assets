using UnityEngine;

public class Start : MonoBehaviour
{
    [Header("舱段讲解")]
    public GameObject NowCanva;
    public GameObject NextCanva;
    public GameObject NowObject;
    public GameObject NextObject;

    [Header("拆解动画")]
    public GameObject moveButton;
    public GameObject moveBackButton;
    public GameObject introduceButton;

    [Header("返回")]
    public GameObject joystick;
    public GameObject fuctionCanva;
    public GameObject showCamera;
    public GameObject mainCamera;


    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            if (UiPointer.IsClickOn("IntroduceButton"))
            {
                NowObject.SetActive(false);
                NextObject.SetActive(true);

                NextCanva.SetActive(true);
                NowCanva.SetActive(false);
            }

            if (UiPointer.IsClickOn("MoveButton"))
            {
                moveBackButton.SetActive(true);
                if (introduceButton != null)
                {
                    introduceButton.SetActive(false);
                }
                moveButton.SetActive(false);
            }
            if (UiPointer.IsClickOn("MoveBackButton"))
            {
                moveBackButton.SetActive(false);
                if (introduceButton != null)
                {
                    introduceButton.SetActive(true);
                }
                moveButton.SetActive(true);
            }
            if (UiPointer.IsClickOn("BackButton"))
            {
                fuctionCanva.SetActive(true);
                showCamera.SetActive(false);
                mainCamera.SetActive(true);
                joystick.SetActive(true);
                NowCanva.SetActive(false);
            }
        }
        
    }
}
