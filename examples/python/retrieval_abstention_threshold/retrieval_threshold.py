# Author: Sandeep Belgavi. Synthetic score-threshold accounting.
def report(rows, threshold):
    accepted = [r for r in rows if r["score"] >= threshold]
    supported = sum(r["supported"] for r in accepted)
    return {
        "cases": len(rows),
        "accepted": len(accepted),
        "false_accepts": len(accepted) - supported,
        "precision": supported / len(accepted) if accepted else None,
        "coverage": len(accepted) / len(rows) if rows else None,
    }
