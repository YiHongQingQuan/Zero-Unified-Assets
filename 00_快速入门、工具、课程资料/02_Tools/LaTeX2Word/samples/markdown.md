# 牛顿法与拟牛顿法

## 一、基本原理

设目标函数 f(x) 二阶可导，在当前点 xₖ 处做二阶泰勒展开：

$$
f(x_k+d) \approx f(x_k) + \nabla f(x_k)^{\mathsf{T}} d + \frac{1}{2} d^{\mathsf{T}} \nabla^2 f(x_k)\, d
$$

令导数为零，得到牛顿方向 d = −[∇²f(xₖ)]⁻¹∇f(xₖ)。

迭代格式为

$$\begin{aligned} x_{k+1} &= x_k + \alpha_k d_k \\ &= x_k - \alpha_k H_k^{-1} g_k \end{aligned}$$

其中 αₖ 由线搜索确定，Hₖ 为海森矩阵或其近似。

## 二、优缺点对比

| 方法 | 收敛速度 | 每步代价 | 适用场景 |
| --- | --- | --- | --- |
| 梯度下降 | 线性 | O(n) | 大规模、低精度 |
| 牛顿法 | 二次 | O(n³) | 中小规模、高精度 |
| BFGS | 超线性 | O(n²) | 通用 |

主要缺点：

- 需要存储和求逆 n×n 矩阵，内存开销为 O(n²)
- 海森矩阵可能非正定，需要修正（如加阻尼项 μI）

## 三、代码片段（不参与公式识别）

```python
for k in range(max_iter):
    g = grad(f, x)
    H = hess(f, x)
    d = -solve(H, g)
    x = x + alpha * d
```

## 四、收敛性说明

在 f 强凸且海森矩阵李氏连续（Lipschitz 常数 L）时，牛顿法满足

$$\|x_{k+1}-x^*\| \le \frac{L}{2m}\|x_k-x^*\|^2$$

即二次收敛，其中 m 为强凸参数。
