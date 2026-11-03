using UnityEngine;

/// <summary>
/// 单块拼图：按住鼠标拖拽，松手时离目标点足够近就吸附归位，并通知所属的 <see cref="PuzzleGroup"/>。
///
/// 原来的 <c>CE5PP</c> / <c>MainCPP</c> / <c>SatellitePP</c> 三份脚本逐行相同，
/// 唯一区别是归位后通知哪个静态单例。现在合并成一个组件：
/// 所属拼图组由 Inspector 的 <see cref="group"/> 字段指定，留空则自动向父节点查找。
/// </summary>
public class PuzzlePiece : MonoBehaviour
{
    [Header("吸附")]
    [Tooltip("归位后的目标点")]
    public Transform targetPosition;

    [Tooltip("松手时与目标点的最大距离，小于该值即吸附")]
    public float snapDistance = 1f;

    [Header("拾取")]
    [Tooltip("屏幕坐标转世界坐标用的相机，留空则使用 Camera.main")]
    public Camera pickupCamera;

    [Header("所属拼图组")]
    [Tooltip("留空时自动向父节点查找 PuzzleGroup")]
    public PuzzleGroup group;

    [SerializeField]
    [Tooltip("是否已归位（只在运行时由脚本修改）")]
    private bool isComplete;

    /// <summary>该块是否已归位。</summary>
    public bool IsComplete
    {
        get { return isComplete; }
    }

    private bool isDragging;
    private Vector3 grabOffset;

    private Camera ActiveCamera
    {
        get { return pickupCamera != null ? pickupCamera : Camera.main; }
    }

    private void Awake()
    {
        if (group == null)
        {
            group = GetComponentInParent<PuzzleGroup>();
        }
    }

    private void OnMouseDown()
    {
        if (isComplete || ActiveCamera == null)
        {
            return;
        }

        isDragging = true;
        grabOffset = transform.position - MouseWorldPosition();
    }

    private void OnMouseUp()
    {
        if (isComplete)
        {
            return;
        }

        isDragging = false;
        TrySnap();
    }

    private void Update()
    {
        if (isDragging)
        {
            transform.position = MouseWorldPosition() + grabOffset;
        }
    }

    private Vector3 MouseWorldPosition()
    {
        Camera cam = ActiveCamera;
        Vector3 screenPoint = Input.mousePosition;
        screenPoint.z = cam.WorldToScreenPoint(transform.position).z;
        return cam.ScreenToWorldPoint(screenPoint);
    }

    private void TrySnap()
    {
        if (targetPosition == null)
        {
            Debug.LogWarning("[PuzzlePiece] 未设置 targetPosition，无法判定是否归位。", this);
            return;
        }

        if (Vector3.Distance(transform.position, targetPosition.position) > snapDistance)
        {
            return;
        }

        transform.position = targetPosition.position;
        isComplete = true;

        if (group != null)
        {
            group.NotifyPieceCompleted(this);
        }
    }
}
