using System.Collections.Generic;
using UnityEngine;

public class SatellitePA : MonoBehaviour
{
    public static SatellitePA SatelliteInstance;
    public List<SatellitePP> SatellitePuzzleList = new List<SatellitePP>();
    public GameObject gameOverPanel;

    void Start()
    {
        SatelliteInstance = this;
        SatellitePuzzleList.Clear();
        SatellitePuzzleList.AddRange(GetComponentsInChildren<SatellitePP>());
    }

    public void Check()
    {
        foreach (SatellitePP puzzle in SatellitePuzzleList)
        {
            if (!puzzle.isComplete)
            {
                return;
            }
        }
        gameOverPanel.SetActive(true);
    }

    
}
