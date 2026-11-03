using UnityEngine;

public class VideoTrigger : MonoBehaviour
{
    public GameObject gamObject;

    private void OnTriggerEnter(Collider other)
    {
        Debug.Log("test");
        gamObject.SetActive(true);
    }

    private void OnTriggerExit(Collider other)
    {
        gamObject.SetActive(false);
    }
}
