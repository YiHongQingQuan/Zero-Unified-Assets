using System.Collections.Generic;
using UnityEngine;

public class PictureClickManager : MonoBehaviour
{
    
    public List<GameObject> canvas = new List<GameObject>();
    public List<Transform> transforms = new List<Transform>();
    public int listLen = 0;



    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        { // 检测左键点击
            Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            RaycastHit hit;

            if (Physics.Raycast(ray, out hit))
            {
                for (int i = 0; i < listLen; i++)
                {
                    if (hit.transform == transforms[i])
                    {
                        canvas[i].gameObject.SetActive(true);
                    }
                }
                
            }
        }
    }
}
