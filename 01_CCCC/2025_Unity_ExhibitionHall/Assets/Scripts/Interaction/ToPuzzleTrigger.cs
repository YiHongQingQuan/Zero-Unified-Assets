using UnityEngine;

public class ToPuzzleTrigger : MonoBehaviour
{
    public GameObject mgameObject;

    private void OnTriggerEnter(Collider other)
    {
        mgameObject.SetActive(true);
    }

    private void OnTriggerExit(Collider other)
    {
        mgameObject.SetActive(false);
    }
}
