using System;
using System.Collections;
using UnityEngine;

/// <summary>
/// 空间站舱段的拆解 / 复位动画，以及主相机与展厅相机之间的切换。
///
/// 舱段用一个数组描述：每个元素记录「哪一段」和「拆解后停在哪」，
/// 合拢位置在 Start 时自动记录，因此加舱段只要在 Inspector 里加一条即可。
/// </summary>
public class KJZMove : MonoBehaviour
{
    [Serializable]
    public class Module
    {
        [Tooltip("舱段名称，仅用于在 Inspector 中辨认")]
        public string label;

        [Tooltip("舱段对象")]
        public Transform target;

        [Tooltip("拆解后停留的位置")]
        public Vector3 disassembledPosition;

        [NonSerialized] public Vector3 homePosition;
    }

    [Header("舱段")]
    public Module[] modules = new Module[0];

    [Header("参数")]
    [Tooltip("移动速度，单位：米/秒")]
    public float speed = 1f;

    [Header("按钮")]
    public GameObject moveButton;
    public GameObject moveBackButton;
    public GameObject introduceButton;

    [Header("相机")]
    public GameObject mainCamera;
    public GameObject showRoomCamera;

    private Coroutine movingRoutine;

    private void Start()
    {
        if (modules == null || modules.Length == 0)
        {
            Debug.LogError("[KJZMove] 未配置任何舱段，脚本已停用。", this);
            enabled = false;
            return;
        }

        foreach (Module module in modules)
        {
            if (module.target == null)
            {
                Debug.LogError("[KJZMove] 有舱段未指定对象，脚本已停用。", this);
                enabled = false;
                return;
            }

            module.homePosition = module.target.position;
        }
    }

    /// <summary>拆解：舱段散开，按钮切换为「复位」。</summary>
    public void Disassemble()
    {
        if (moveButton != null) moveButton.SetActive(false);
        if (introduceButton != null) introduceButton.SetActive(false);
        if (moveBackButton != null) moveBackButton.SetActive(true);

        MoveAll(toDisassembled: true);
    }

    /// <summary>复位：舱段回到 Start 时记录的合拢位置。</summary>
    public void Reassemble()
    {
        if (moveButton != null) moveButton.SetActive(true);
        if (introduceButton != null) introduceButton.SetActive(true);
        if (moveBackButton != null) moveBackButton.SetActive(false);

        MoveAll(toDisassembled: false);
    }

    /// <summary>从展厅相机切回主相机。</summary>
    public void BackToMainCamera()
    {
        if (mainCamera != null) mainCamera.SetActive(true);
        if (showRoomCamera != null) showRoomCamera.SetActive(false);
    }

    private void MoveAll(bool toDisassembled)
    {
        if (movingRoutine != null)
        {
            StopCoroutine(movingRoutine);
        }

        movingRoutine = StartCoroutine(MoveAllRoutine(toDisassembled));
    }

    private IEnumerator MoveAllRoutine(bool toDisassembled)
    {
        int count = modules.Length;
        var from = new Vector3[count];
        var to = new Vector3[count];
        float duration = 0f;

        for (int i = 0; i < count; i++)
        {
            from[i] = modules[i].target.position;
            to[i] = toDisassembled ? modules[i].disassembledPosition : modules[i].homePosition;

            // 按最远的那一段决定总时长，保证所有舱段同时到达
            duration = Mathf.Max(duration, Vector3.Distance(from[i], to[i]) / Mathf.Max(0.01f, speed));
        }

        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / duration);

            for (int i = 0; i < count; i++)
            {
                modules[i].target.position = Vector3.Lerp(from[i], to[i], t);
            }

            yield return null;
        }

        // 收尾时精确落位，避免插值残留的浮点误差
        for (int i = 0; i < count; i++)
        {
            modules[i].target.position = to[i];
        }

        movingRoutine = null;
    }
}
