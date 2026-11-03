using UnityEngine;

/// <summary>
/// 双开自动门：触发器进入时滑开或合上。
///
/// 原来 <c>DoorMove</c>（类名 <c>TriggerMove</c>）与 <c>DoorBack</c> 两份脚本逐行相同，
/// 只有目标坐标不同 —— 一个负责打开、一个负责合上。这里合并成一个组件，
/// 由 <see cref="onEnter"/> 决定触发器进入时执行哪种动作。
/// </summary>
public class SlidingDoor : MonoBehaviour
{
    /// <summary>触发器进入后的动作。</summary>
    public enum TriggerAction
    {
        Open,
        Close
    }

    [Header("门板")]
    public Transform leftPanel;
    public Transform rightPanel;

    [Header("打开位置（世界坐标）")]
    public Vector3 leftOpenPosition;
    public Vector3 rightOpenPosition;

    [Header("运动")]
    [Tooltip("移动速度，单位：米/秒")]
    public float speed = 1f;

    [Tooltip("触发器进入时执行的动作")]
    public TriggerAction onEnter = TriggerAction.Open;

    [Tooltip("触发器离开时是否执行反向动作")]
    public bool toggleOnExit;

    private Vector3 leftClosedPosition;
    private Vector3 rightClosedPosition;
    private Vector3 leftTarget;
    private Vector3 rightTarget;
    private bool moving;

    private void Start()
    {
        if (leftPanel == null || rightPanel == null)
        {
            Debug.LogError("[SlidingDoor] 门板未在 Inspector 中赋值，脚本已停用。", this);
            enabled = false;
            return;
        }

        // 以场景初始位置作为「关闭」位置
        leftClosedPosition = leftPanel.position;
        rightClosedPosition = rightPanel.position;
        leftTarget = leftClosedPosition;
        rightTarget = rightClosedPosition;
    }

    private void OnTriggerEnter(Collider other)
    {
        if (onEnter == TriggerAction.Open)
        {
            Open();
        }
        else
        {
            Close();
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (!toggleOnExit)
        {
            return;
        }

        if (onEnter == TriggerAction.Open)
        {
            Close();
        }
        else
        {
            Open();
        }
    }

    /// <summary>滑开到设定的打开位置。</summary>
    public void Open()
    {
        MoveTo(leftOpenPosition, rightOpenPosition);
    }

    /// <summary>合上，回到 Start 时记录的位置。</summary>
    public void Close()
    {
        MoveTo(leftClosedPosition, rightClosedPosition);
    }

    private void MoveTo(Vector3 left, Vector3 right)
    {
        leftTarget = left;
        rightTarget = right;
        moving = true;
    }

    private void Update()
    {
        if (!moving)
        {
            return;
        }

        float step = speed * Time.deltaTime;

        leftPanel.position = Vector3.MoveTowards(leftPanel.position, leftTarget, step);
        rightPanel.position = Vector3.MoveTowards(rightPanel.position, rightTarget, step);

        if (leftPanel.position == leftTarget && rightPanel.position == rightTarget)
        {
            moving = false;
        }
    }
}
