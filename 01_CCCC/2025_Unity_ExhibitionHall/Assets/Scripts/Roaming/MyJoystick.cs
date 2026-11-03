using UnityEngine;
using UnityEngine.EventSystems;

/// <summary>
/// 虚拟摇杆：拖动时把指针位置换算成底盘内的归一化方向。
///
/// 用 RectTransformUtility 把屏幕坐标转进底盘的局部坐标再算方向，
/// 所以摇杆放在任意分辨率、任意位置的 Canvas 下都能得到正确的结果。
/// </summary>
public class MyJoystick : MonoBehaviour, IDragHandler, IPointerUpHandler, IPointerDownHandler
{
    [Tooltip("摇杆底盘，用来确定活动范围")]
    public RectTransform background;

    [Tooltip("摇杆头，跟随拖动移动")]
    public RectTransform handle;

    [Tooltip("摇杆头可移动的最大半径（像素）")]
    public float radius = 100f;

    /// <summary>归一化后的输入方向，长度 0~1。</summary>
    public Vector2 InputVector { get; private set; }

    public void OnPointerDown(PointerEventData eventData)
    {
        OnDrag(eventData);
    }

    public void OnDrag(PointerEventData eventData)
    {
        if (background == null)
        {
            return;
        }

        Vector2 localPoint;
        bool hit = RectTransformUtility.ScreenPointToLocalPointInRectangle(
            background, eventData.position, eventData.pressEventCamera, out localPoint);

        if (!hit)
        {
            return;
        }

        InputVector = Vector2.ClampMagnitude(localPoint / Mathf.Max(radius, 1f), 1f);

        if (handle != null)
        {
            handle.anchoredPosition = InputVector * radius;
        }
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        InputVector = Vector2.zero;

        if (handle != null)
        {
            handle.anchoredPosition = Vector2.zero;
        }
    }
}
