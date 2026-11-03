using UnityEngine;
using UnityEngine.Video;

public class PlayVideo : MonoBehaviour
{
    public VideoPlayer vPlayer;
    private bool isPlay = false;
    public GameObject button;

    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (UiPointer.IsClickOn("Button (Legacy)"))
            {
                if (!isPlay && UiPointer.ClickedButton() == button)
                {
                    isPlay = true;
                    vPlayer.Play();
                }
                else if (isPlay)
                {
                    isPlay = false;
                    vPlayer.Pause();
                }
            }
        }
    }
}
