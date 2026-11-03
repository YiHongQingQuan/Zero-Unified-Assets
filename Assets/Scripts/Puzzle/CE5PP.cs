using UnityEngine;

public class CE5PP : MonoBehaviour
{
    public bool isComplete; // 完成拼图
    private bool isDragging = false; // 正在拖拽
    private Vector3 r; // 鼠标偏移
    public Camera m_Camera; // 主摄像机
    public Transform targetPosition;
    public float maxLen = 1f; // 最大吸附距离
    void Start()
    {
        //m_Camera = Camera.main;
    }

    private void OnMouseDown()
    {
        if (isComplete)
        {
            return;
        }
        isDragging = true;
        r = transform.position - GetMouseWorldPosition();
    }

    private void OnMouseUp()
    {
        if (isComplete)
        {
            return;
        }
        isDragging = false;
        CheckPosition();
    }

    private void Update()
    {
        if (isDragging)
        {
            transform.position = GetMouseWorldPosition() + r; // 拼图跟随鼠标
        }
    }

    private Vector3 GetMouseWorldPosition()
    {
        Vector3 mousePosition = Input.mousePosition;
        mousePosition.z = m_Camera.WorldToScreenPoint(transform.position).z;
        return m_Camera.ScreenToWorldPoint(mousePosition);
    }

    private void CheckPosition()
    {
        if (Vector3.Distance(transform.position, targetPosition.position) < maxLen)
        {
            transform.position = targetPosition.position;
            isComplete = true;
            CE5PA.CE5Instance.Check();
        }
    }
}
