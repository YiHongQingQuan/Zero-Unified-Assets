using System.Collections.Generic;
using UnityEngine;

public class CE5PA : MonoBehaviour
{
    public static CE5PA CE5Instance;
    public List<CE5PP> CE5PuzzleList = new List<CE5PP>();
    public GameObject gameOverPanel;

    void Start()
    {
        CE5Instance = this;
        CE5PuzzleList.Clear();
        CE5PuzzleList.AddRange(GetComponentsInChildren<CE5PP>());
    }

    public void Check()
    {
        foreach (CE5PP puzzle in CE5PuzzleList)
        {
            if (!puzzle.isComplete)
            {
                return;
            }
        }
        gameOverPanel.SetActive(true);
    }

    
}
