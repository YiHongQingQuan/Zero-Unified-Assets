using UnityEngine;

public class MainCPP : MonoBehaviour
{
    public bool isComplete; // 记录是否完成拼图
    private bool isDragging = false; // 记录是否正在拖拽
    private Vector3 r; // 鼠标偏移
    public Camera camera; // 主摄像机
    public Transform targetPosition;
    public float maxLen = 1f; // 最大吸附距离
    void Start()
    {
        //camera = Camera.main;
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
            transform.position = GetMouseWorldPosition() + r; // 使拼图跟随鼠标
        }
    }

    private Vector3 GetMouseWorldPosition()
    {
        Vector3 mousePosition = Input.mousePosition;
        mousePosition.z = camera.WorldToScreenPoint(transform.position).z;
        return camera.ScreenToWorldPoint(mousePosition);
    }

    private void CheckPosition()
    {
        if (Vector3.Distance(transform.position, targetPosition.position) < maxLen)
        {
            transform.position = targetPosition.position;
            isComplete = true;
            MainCPA.MainCInstance.Check();
        }
    }
}
