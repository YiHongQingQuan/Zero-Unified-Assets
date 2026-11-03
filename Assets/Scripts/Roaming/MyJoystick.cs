using UnityEngine;
using UnityEngine.EventSystems;

public class MyJoystick : MonoBehaviour, IDragHandler, IPointerUpHandler, IPointerDownHandler
{
    public Transform centerPoint; // 控制点
    public float maxLen = 100; // 最大拖动距离
    public Vector2 inputVector; // 输入的向量
    private Vector3 startPosition; // 原始位置

    public void OnDrag(PointerEventData eventData)
    {
        Vector2 dir = eventData.position - (Vector2)startPosition; // 计算移动方向
        if (dir.magnitude > maxLen)
        {
            inputVector = dir.normalized;
        }
        else
        {
            inputVector = dir / maxLen;
        }
        centerPoint.position = startPosition + (Vector3)inputVector * maxLen; // 移动角色
    }

    public void OnPointerDown(PointerEventData eventData)
    {
        startPosition = centerPoint.position;
        OnDrag(eventData);
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        inputVector = Vector2.zero;
        centerPoint.position = startPosition;
    }

}
