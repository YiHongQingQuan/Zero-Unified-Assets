using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 一组拼图的完成判定：组内所有 <see cref="PuzzlePiece"/> 都归位后，显示通关面板。
///
/// 拼图块通过 <see cref="PuzzlePiece.group"/> 直接引用所属组，不依赖全局单例，
/// 同一场景里可以并存多组互不干扰的拼图。
/// </summary>
public class PuzzleGroup : MonoBehaviour
{
    [Header("通关")]
    [Tooltip("全部归位后要显示的面板")]
    public GameObject completePanel;

    [Tooltip("勾选后会在 Start 时自动收集子节点里的所有拼图块")]
    public bool autoCollectPieces = true;

    private readonly List<PuzzlePiece> pieces = new List<PuzzlePiece>();

    private void Start()
    {
        if (autoCollectPieces)
        {
            CollectPieces();
        }
    }

    /// <summary>重新收集子节点下的所有拼图块（含未激活的）。</summary>
    public void CollectPieces()
    {
        pieces.Clear();
        pieces.AddRange(GetComponentsInChildren<PuzzlePiece>(true));
    }

    /// <summary>由 <see cref="PuzzlePiece"/> 在归位后调用。</summary>
    public void NotifyPieceCompleted(PuzzlePiece piece)
    {
        if (pieces.Count == 0)
        {
            CollectPieces();
        }

        for (int i = 0; i < pieces.Count; i++)
        {
            if (!pieces[i].IsComplete)
            {
                return;
            }
        }

        ShowCompletePanel();
    }

    private void ShowCompletePanel()
    {
        if (completePanel != null)
        {
            completePanel.SetActive(true);
        }
    }
}
