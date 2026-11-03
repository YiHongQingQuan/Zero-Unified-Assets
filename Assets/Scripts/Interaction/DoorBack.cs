using UnityEngine;

public class DoorBack : MonoBehaviour
{
    public Vector3 target1Pos = new Vector3(-15.42f, -160.34f, 107.591f);
    public Vector3 target2Pos = new Vector3(-11.05f, -160.34f, 107.591f);
    public float speed = 1f;
    public GameObject door1;
    private Transform transform1;
    public GameObject door2;
    private Transform transform2;

    private void Start()
    {
        transform1 = door1.transform;
        transform2 = door2.transform;
        enabled = false;
    }

    void OnTriggerEnter(Collider other) => enabled = true; // 触发后激活脚本

    void Update()
    {
        transform1.position = Vector3.MoveTowards(transform1.position, target1Pos, speed * Time.deltaTime);
        transform2.position = Vector3.MoveTowards(transform2.position, target2Pos, speed * Time.deltaTime);
        if (transform1.position == target1Pos) enabled = false; // 到达后停用
    }
}
