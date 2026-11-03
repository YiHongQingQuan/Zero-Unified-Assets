using UnityEngine;
using UnityEngine.EventSystems;
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
            if (EventSystem.current.currentSelectedGameObject.name == "Button (Legacy)")
            {
                if (!isPlay && EventSystem.current.currentSelectedGameObject == button)
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
