import argparse
import os
import sys
from ultralytics import YOLO


def evaluate_model(
    model_path=r"runs\detect\pothole_detection-4\weights\best.pt",
    data_yaml="data.yaml",
    imgsz=640,
    batch=8,
    split="val",
    device="cpu"
):
    """
    Evaluates a trained YOLO model against a validation or test dataset.
    Prints precision, recall, mAP50, and mAP50-95.
    """
    if not os.path.exists(model_path):
        print(f"ERROR: Model weights not found at '{model_path}'.")
        return None

    if not os.path.exists(data_yaml):
        print(f"ERROR: Dataset configuration not found at '{data_yaml}'.")
        return None

    print("=" * 60)
    print("           SafeRouteAI Model Evaluation")
    print("=" * 60)
    print(f"Model:   {model_path}")
    print(f"Dataset: {data_yaml}")
    print(f"Split:   {split}")
    print(f"Device:  {device}")
    print("=" * 60)

    try:
        model = YOLO(model_path)
        metrics = model.val(
            data=data_yaml,
            split=split,
            imgsz=imgsz,
            batch=batch,
            device=device,
            verbose=True
        )

        print("\n" + "=" * 60)
        print("                 Evaluation Summary")
        print("=" * 60)
        
        # Extract metrics
        precision = metrics.box.mp
        recall = metrics.box.mr
        map50 = metrics.box.map50
        map50_95 = metrics.box.map

        print(f"Mean Precision:    {precision:.4f} ({precision:.1%})")
        print(f"Mean Recall:       {recall:.4f} ({recall:.1%})")
        print(f"mAP@0.50:          {map50:.4f} ({map50:.1%})")
        print(f"mAP@0.50:0.95:     {map50_95:.4f} ({map50_95:.1%})")
        
        if hasattr(metrics, 'speed') and metrics.speed:
            inf_time = metrics.speed.get('inference', 0.0)
            print(f"Inference Latency: {inf_time:.2f} ms / frame")

        print("=" * 60)
        print(f"Detailed plots saved to: {metrics.save_dir}")
        print("=" * 60)
        return metrics

    except Exception as e:
        print(f"Evaluation error: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SafeRouteAI YOLO Model")
    parser.add_argument(
        "--model",
        type=str,
        default=r"runs\detect\pothole_detection-4\weights\best.pt",
        help="Path to trained YOLO weights file (.pt)"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data.yaml",
        help="Path to dataset YAML file"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="val",
        choices=["val", "test", "train"],
        help="Dataset split to evaluate on"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to run evaluation on (e.g., cpu, 0)"
    )

    args = parser.parse_args()
    evaluate_model(
        model_path=args.model,
        data_yaml=args.data,
        split=args.split,
        device=args.device
    )
