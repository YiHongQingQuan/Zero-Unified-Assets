using System.Collections.Generic;
using UnityEngine;

public class MainCPA : MonoBehaviour
{
    public static MainCPA MainCInstance;
    public List<MainCPP> MainCPuzzleList = new List<MainCPP>();
    public GameObject gameOverPanel;

    void Start()
    {
        MainCInstance = this;
        MainCPuzzleList.Clear();
        MainCPuzzleList.AddRange(GetComponentsInChildren<MainCPP>());
    }

    public void Check()
    {
        Debug.Log("1");
        foreach (MainCPP puzzle in MainCPuzzleList)
        {
            if (!puzzle.isComplete)
            {
                return;
            }
        }
        Debug.Log("当当~~！");
        gameOverPanel.SetActive(true);
    }

    
}
