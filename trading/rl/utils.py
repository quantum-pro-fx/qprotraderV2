# trading/rl/utils.py
import torch
import logging

logger = logging.getLogger(__name__)

def check_for_nans(tensor: torch.Tensor, context: str = "") -> bool:
    """Check for NaN values in tensors and log detailed warnings."""
    if torch.isnan(tensor).any():
        nan_count = torch.isnan(tensor).sum().item()
        tensor_size = tensor.numel()
        logger.warning(
            f"NaN detected in {context} - "
            f"{nan_count}/{tensor_size} ({nan_count/tensor_size:.1%}) NaN values "
            f"in tensor of shape {tuple(tensor.shape)}"
        )
        return True
    return False