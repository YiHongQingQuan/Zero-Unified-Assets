using System.Collections;
using UnityEngine;

/// <summary>
/// 空间站五舱段的拆解 / 复位动画，以及主相机与展厅相机之间的切换。
///
/// 原实现把 <c>while (position != target)</c> 直接写在 Update 里，会在一帧内死循环：
/// Time.deltaTime 为 0 时（暂停、首帧）条件永远成立，直接卡死编辑器。
/// 这里改成协程按时间插值，每帧只推进一步。
/// </summary>
public class KJZMove : MonoBehaviour
{
    [Header("舱段")]
    public GameObject tianhe;
    public GameObject tianzhou;
    public GameObject mengtian;
    public GameObject shenzhou;
    public GameObject wentian;

    [Header("拆解后的目标位置")]
    public Vector3 tianheTargetPos = new Vector3(-12.4f, -175f, 124.22f);
    public Vector3 tianzhouTargetPos = new Vector3(-12.4f, -177.1f, 124.22f);
    public Vector3 mengtianTargetPos = new Vector3(-9.74f, -173.9f, 124.21f);
    public Vector3 shenzhouTargetPos = new Vector3(-12.4f, -171.96f, 124.22f);
    public Vector3 wentianTargetPos = new Vector3(-15.24f, -173.9f, 124.2f);

    [Header("参数")]
    [Tooltip("舱段移动速度，单位：米/秒")]
    public float speed = 1f;

    [Header("按钮")]
    public GameObject moveButton;
    public GameObject moveBackButton;
    public GameObject introduceButton;

    [Header("相机")]
    public GameObject mainCamera;
    public GameObject showRoomCamera;

    private Transform tianheT;
    private Transform tianzhouT;
    private Transform mengtianT;
    private Transform shenzhouT;
    private Transform wentianT;

    private Vector3 tianheHome;
    private Vector3 tianzhouHome;
    private Vector3 mengtianHome;
    private Vector3 shenzhouHome;
    private Vector3 wentianHome;

    private Coroutine movingRoutine;

    private void Start()
    {
        if (tianhe == null || tianzhou == null || mengtian == null ||
            shenzhou == null || wentian == null)
        {
            Debug.LogError("[KJZMove] 舱段引用未在 Inspector 中赋值，脚本已停用。", this);
            enabled = false;
            return;
        }

        // 记录合拢时（Start 那一刻）的位置，复位时用
        tianheT = tianhe.transform;
        tianheHome = tianheT.position;

        tianzhouT = tianzhou.transform;
        tianzhouHome = tianzhouT.position;

        mengtianT = mengtian.transform;
        mengtianHome = mengtianT.position;

        shenzhouT = shenzhou.transform;
        shenzhouHome = shenzhouT.position;

        wentianT = wentian.transform;
        wentianHome = wentianT.position;
    }

    private void Update()
    {
        if (!Input.GetMouseButtonUp(0))
        {
            return;
        }

        if (UiPointer.IsClickOn("MoveButton"))
        {
            Disassemble();
        }
        else if (UiPointer.IsClickOn("MoveBackButton"))
        {
            Reassemble();
        }
        else if (UiPointer.IsClickOn("BackButton"))
        {
            BackToMainCamera();
        }
    }

    /// <summary>拆解：舱段散开，按钮切换为「复位」。</summary>
    public void Disassemble()
    {
        if (moveButton != null) moveButton.SetActive(false);
        if (introduceButton != null) introduceButton.SetActive(false);
        if (moveBackButton != null) moveBackButton.SetActive(true);

        MoveAll(tianheTargetPos, tianzhouTargetPos, mengtianTargetPos,
                shenzhouTargetPos, wentianTargetPos);
    }

    /// <summary>复位：舱段回到 Start 时记录的合拢位置。</summary>
    public void Reassemble()
    {
        if (moveButton != null) moveButton.SetActive(true);
        if (introduceButton != null) introduceButton.SetActive(true);
        if (moveBackButton != null) moveBackButton.SetActive(false);

        MoveAll(tianheHome, tianzhouHome, mengtianHome, shenzhouHome, wentianHome);
    }

    /// <summary>从展厅相机切回主相机。</summary>
    public void BackToMainCamera()
    {
        if (mainCamera != null) mainCamera.SetActive(true);
        if (showRoomCamera != null) showRoomCamera.SetActive(false);
    }

    private void MoveAll(Vector3 toTianhe, Vector3 toTianzhou, Vector3 toMengtian,
                         Vector3 toShenzhou, Vector3 toWentian)
    {
        if (movingRoutine != null)
        {
            StopCoroutine(movingRoutine);
        }

        movingRoutine = StartCoroutine(MoveAllRoutine(
            toTianhe, toTianzhou, toMengtian, toShenzhou, toWentian));
    }

    private IEnumerator MoveAllRoutine(Vector3 toTianhe, Vector3 toTianzhou, Vector3 toMengtian,
                                       Vector3 toShenzhou, Vector3 toWentian)
    {
        Vector3 fromTianhe = tianheT.position;
        Vector3 fromTianzhou = tianzhouT.position;
        Vector3 fromMengtian = mengtianT.position;
        Vector3 fromShenzhou = shenzhouT.position;
        Vector3 fromWentian = wentianT.position;

        // 按最远的那一段决定总时长，保证五个舱段同时到达
        float duration = Mathf.Max(
            TravelTime(fromTianhe, toTianhe),
            Mathf.Max(
                TravelTime(fromTianzhou, toTianzhou),
                Mathf.Max(
                    TravelTime(fromMengtian, toMengtian),
                    Mathf.Max(
                        TravelTime(fromShenzhou, toShenzhou),
                        TravelTime(fromWentian, toWentian)))));

        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / duration);

            tianheT.position = Vector3.Lerp(fromTianhe, toTianhe, t);
            tianzhouT.position = Vector3.Lerp(fromTianzhou, toTianzhou, t);
            mengtianT.position = Vector3.Lerp(fromMengtian, toMengtian, t);
            shenzhouT.position = Vector3.Lerp(fromShenzhou, toShenzhou, t);
            wentianT.position = Vector3.Lerp(fromWentian, toWentian, t);

            yield return null;
        }

        // 收尾时精确落位，避免插值残留的浮点误差
        tianheT.position = toTianhe;
        tianzhouT.position = toTianzhou;
        mengtianT.position = toMengtian;
        shenzhouT.position = toShenzhou;
        wentianT.position = toWentian;

        movingRoutine = null;
    }

    private float TravelTime(Vector3 from, Vector3 to)
    {
        return Vector3.Distance(from, to) / Mathf.Max(0.01f, speed);
    }
}
