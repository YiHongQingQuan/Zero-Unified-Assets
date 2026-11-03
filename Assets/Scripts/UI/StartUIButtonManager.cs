using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class StartUIButtonManager : MonoBehaviour
{
    public List<Button> buttons = new List<Button>();
    void Start()
    {
        AddClickEvents();
    }


    void AddClickEvents()
    {
        int x = 0;
        foreach (Button item in buttons)
        {
            int y = x;
            item.onClick.AddListener(() => ClickEvent(y));
            x++;
        }
    }


    void ClickEvent(int a)
    {
        //通过判断点击按钮的名字调用相应的方法
        switch (buttons[a].name)
        {
            case "VPButton":
                SceneManager.LoadScene("航天");
                break;

            case "ARButton":
                SceneManager.LoadScene("AR");
                break;

            case "ExitButton":
                Application.Quit();
                break;

            default:
                break;
        }
    }
}
