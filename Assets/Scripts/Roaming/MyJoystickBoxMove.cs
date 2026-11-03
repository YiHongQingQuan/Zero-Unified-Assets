using UnityEngine;

/// <summary>
/// 按摇杆输入沿相机朝向水平移动目标对象。
/// </summary>
public class MyJoystickBoxMove : MonoBehaviour
{
    [Tooltip("输入来源")]
    public MyJoystick myJoystick;

    [Tooltip("要移动的对象")]
    public Transform target;

    [Tooltip("移动方向的参考相机")]
    public Camera gameCamera;

    [Tooltip("移动速度，单位：米/秒")]
    public float speed = 5f;

    private void FixedUpdate()
    {
        if (myJoystick == null || target == null || gameCamera == null)
        {
            return;
        }

        Vector2 input = myJoystick.InputVector;
        if (input.sqrMagnitude <= 0f)
        {
            return;
        }

        Vector3 direction = gameCamera.transform.forward * input.y + gameCamera.transform.right * input.x;
        direction.y = 0f;

        // 物理帧要用 fixedDeltaTime，用 deltaTime 会让速度随帧率漂移
        target.Translate(direction.normalized * input.magnitude * speed * Time.fixedDeltaTime, Space.World);
    }
}
