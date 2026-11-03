using UnityEngine;
using UnityEngine.Video;

/// <summary>
/// 播放 / 暂停视频。把按钮的 <c>onClick</c> 指到 <see cref="TogglePlayback"/> 即可。
/// </summary>
public class PlayVideo : MonoBehaviour
{
    [Tooltip("要控制的视频播放器")]
    public VideoPlayer vPlayer;

    /// <summary>在播放与暂停之间切换。</summary>
    public void TogglePlayback()
    {
        if (vPlayer == null)
        {
            return;
        }

        if (vPlayer.isPlaying)
        {
            vPlayer.Pause();
        }
        else
        {
            vPlayer.Play();
        }
    }
}
