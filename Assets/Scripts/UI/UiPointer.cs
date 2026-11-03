using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

/// <summary>
/// 把「鼠标点击」翻译成「被点到的那个按钮」。
///
/// 做法：用 EventSystem 从鼠标位置发一条 UI 射线，命中的若是 Text / Image 子节点，
/// 就向上回溯到真正接收点击的控件（Selectable），因此不依赖层级结构和命名习惯。
/// 结果按帧缓存，同一帧内多次查询只算一次。
///
/// 用法：<c>if (UiPointer.IsClickOn("MoveButton")) { ... }</c>
/// </summary>
public static class UiPointer
{
    private static readonly List<RaycastResult> RaycastResults = new List<RaycastResult>();

    private static GameObject cachedObject;
    private static int cachedFrame = -1;

    /// <summary>当前鼠标位置下最上层的可点击控件；点到空白处返回 null。</summary>
    public static GameObject ClickedButton()
    {
        if (cachedFrame == Time.frameCount)
        {
            return cachedObject;
        }

        cachedFrame = Time.frameCount;
        cachedObject = Pick();
        return cachedObject;
    }

    /// <summary>判断本次点击是否落在名为 <paramref name="objectName"/> 的控件上。</summary>
    public static bool IsClickOn(string objectName)
    {
        GameObject target = ClickedButton();
        return target != null && target.name == objectName;
    }

    /// <summary>手动清空缓存（同一帧内 UI 结构变化时使用，一般不需要调用）。</summary>
    public static void InvalidateCache()
    {
        cachedFrame = -1;
        cachedObject = null;
    }

    private static GameObject Pick()
    {
        EventSystem eventSystem = EventSystem.current;
        if (eventSystem == null)
        {
            return null;
        }

        PointerEventData pointer = new PointerEventData(eventSystem);
        pointer.position = Input.mousePosition;

        RaycastResults.Clear();
        eventSystem.RaycastAll(pointer, RaycastResults);

        if (RaycastResults.Count == 0)
        {
            return null;
        }

        // 命中的通常是最上层的 Image / Text，向上回溯到真正接收点击的控件
        for (int i = 0; i < RaycastResults.Count; i++)
        {
            Transform node = RaycastResults[i].gameObject.transform;
            while (node != null)
            {
                if (node.GetComponent<Selectable>() != null)
                {
                    return node.gameObject;
                }
                node = node.parent;
            }
        }

        // 没找到 Selectable 时退化为最上层命中对象，兼容 EventTrigger 之类的写法
        return RaycastResults[0].gameObject;
    }
}
