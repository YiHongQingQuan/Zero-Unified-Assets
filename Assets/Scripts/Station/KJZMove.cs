using System;
using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;

public class KJZMove : MonoBehaviour
{
    [Header("天和舱")]
    public GameObject tianhe;
    private Transform tianheTransform;
    public Vector3 tianheStartPos;
    public Vector3 tianheTargetPos = new Vector3(-12.4f, -175f, 124.22f);

    [Header("天舟飞船")]
    public GameObject tianzhou;
    private Transform tianzhouTransform;
    public Vector3 tianzhouStartPos;
    public Vector3 tianzhouTargetPos = new Vector3(-12.4f, -177.1f, 124.22f);

    [Header("梦天舱")]
    public GameObject mengtian;
    private Transform mengtianTransform;
    public Vector3 mengtianStartPos;
    public Vector3 mengtianTargetPos = new Vector3(-9.74f, -173.9f, 124.21f);

    [Header("神舟飞船")]
    public GameObject shenzhou;
    private Transform shenzhouTransform;
    public Vector3 shenzhouStartPos;
    public Vector3 shenzhouTargetPos = new Vector3(-12.4f, -171.96f, 124.22f);

    [Header("问天舱")]
    public GameObject wentian;
    private Transform wentianTransform;
    public Vector3 wentianStartPos;
    public Vector3 wentianTargetPos = new Vector3(-15.24f, -173.9f, 124.2f);

    [Header("其它参数")]
    public float speed = 1f;

    [Header("按钮")]
    public GameObject moveButton;
    public GameObject moveBackButton;
    public GameObject introduceButton;

    [Header("画布")]
    public GameObject joystick;
    public GameObject functionCanvas;
    public GameObject showRoomCanvas;

    [Header("摄像机")]
    public GameObject mainCamera;
    public GameObject showRoomCamera;

    private void Start()
    {
        tianheTransform = tianhe.transform;
        tianheStartPos = tianhe.transform.position;

        tianzhouTransform = tianzhou.transform;
        tianzhouStartPos = tianzhou.transform.position;

        mengtianTransform = mengtian.transform;
        mengtianStartPos = mengtian.transform.position;

        shenzhouTransform = shenzhou.transform;
        shenzhouStartPos = shenzhou.transform.position;

        wentianTransform = wentian.transform;
        wentianStartPos = wentian.transform.position;
        //enabled = false;
    }

    private void OnMouseUpAsButton()
    {
        //enabled = true;
    }

    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (EventSystem.current.currentSelectedGameObject.name == "MoveButton")
            {
                Debug.Log("测试1");
                moveButton.SetActive(false);
                introduceButton.SetActive(false);
                moveBackButton.SetActive(true);

                //StartCoroutine(MoveTo(tianheTransform, tianheTargetPos, 2f, () => { }));

                while (tianheTransform.position != tianheTargetPos)
                {
                    tianheTransform.position = Vector3.MoveTowards(tianheTransform.position, tianheTargetPos, speed * Time.deltaTime);
                }

                //tianheTransform.position = Vector3.MoveTowards(tianheTransform.position, tianheTargetPos, speed * Time.deltaTime);
                tianzhouTransform.position = Vector3.MoveTowards(tianzhouTransform.position, tianzhouTargetPos, speed * Time.deltaTime);
                mengtianTransform.position = Vector3.MoveTowards(mengtianTransform.position, mengtianTargetPos, speed * Time.deltaTime);
                shenzhouTransform.position = Vector3.MoveTowards(shenzhouTransform.position, shenzhouTargetPos, speed * Time.deltaTime);
                wentianTransform.position = Vector3.MoveTowards(wentianTransform.position, wentianTargetPos, speed * Time.deltaTime);
            }
            if (EventSystem.current.currentSelectedGameObject.name == "MoveBackButton")
            {
                Debug.Log("测试2");
                moveButton.SetActive(true);
                introduceButton.SetActive(true);
                moveBackButton.SetActive(false);
                tianheTransform.position = Vector3.MoveTowards(tianheTargetPos, tianheTransform.position, speed * Time.deltaTime);
                tianzhouTransform.position = Vector3.MoveTowards(tianzhouTargetPos, tianzhouTransform.position, speed * Time.deltaTime);
                mengtianTransform.position = Vector3.MoveTowards(mengtianTargetPos, mengtianTransform.position, speed * Time.deltaTime);
                shenzhouTransform.position = Vector3.MoveTowards(shenzhouTargetPos, shenzhouTransform.position, speed * Time.deltaTime);
                wentianTransform.position = Vector3.MoveTowards(wentianTargetPos, wentianTransform.position, speed * Time.deltaTime);
            }
            if (EventSystem.current.currentSelectedGameObject.name == "BackButton")
            {
                mainCamera.SetActive(true);
                showRoomCamera.SetActive(false);
            }
        }
    }

    public IEnumerator MoveTo (Transform transform, Vector3 end, float seconds, Action finish)
    {
        float time = 0;
        Vector3 start = transform.position;
        var wait = new WaitForEndOfFrame();
        while (time < seconds)
        {
            transform.position = Vector3.Lerp(start, end, (time / seconds));
            time += Time.deltaTime;
            yield return wait;
        }
        transform.position = end;
        finish?.Invoke();
    }
}
