# Patch for PyTorch deprecation warning

def apply_torch_patch():
    """
    Apply patch to fix the PyTorch deprecation warning:
    'torch.utils._pytree._register_pytree_node is deprecated. Please use torch.utils._pytree.register_pytree_node instead.'
    
    This function monkey patches the deprecated function to use the new recommended function.
    """
    try:
        import torch.utils._pytree as _torch_pytree
        
        # Store the original function
        original_register = getattr(_torch_pytree, '_register_pytree_node', None)
        new_register = getattr(_torch_pytree, 'register_pytree_node', None)
        
        # Only patch if both functions exist and they're different
        if original_register is not None and new_register is not None and original_register is not new_register:
            # Replace the deprecated function with the new one
            setattr(_torch_pytree, '_register_pytree_node', new_register)
            return True
        return False
    except (ImportError, AttributeError):
        # If torch is not installed or the functions don't exist, do nothing
        return False