using UnityEngine;

public class MyJoystickBoxMove : MonoBehaviour
{
    public MyJoystick myJoystick;
    public Transform target;
    public Camera gameCamera;
    public float speed = 5;

    void FixedUpdate()
    {
        Vector2 joystickInput = myJoystick.inputVector;  // 获取摇杆输入
        Vector3 move = gameCamera.transform.forward * joystickInput.y + gameCamera.transform.right * joystickInput.x;
        move.y = 0;
        target.Translate(move * speed * Time.deltaTime, Space.World); // 移动
    }
}
