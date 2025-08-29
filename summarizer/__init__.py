# Import and apply the PyTorch patch to fix deprecation warning
from .torch_patch import apply_torch_patch

# Apply the patch when the module is imported
apply_torch_patch()