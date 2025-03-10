import os
import sys
import warnings
import importlib.util
from types import ModuleType
import torch

def create_module_from_file(file_path: str, module_name: str) -> ModuleType:
    """Create a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module {module_name} from {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def setup_rmbg_imports(model_dir: str) -> None:
    """Set up proper imports for RMBG-2.0 model files."""
    # Find the model files directory
    snapshot_dir = None
    for root, dirs, files in os.walk(model_dir):
        if 'BiRefNet_config.py' in files and 'birefnet.py' in files:
            snapshot_dir = root
            break
    
    if not snapshot_dir:
        raise FileNotFoundError("Could not find RMBG-2.0 model files")

    # Create modules from the files
    config_path = os.path.join(snapshot_dir, 'BiRefNet_config.py')
    model_path = os.path.join(snapshot_dir, 'birefnet.py')

    # First load the config as it's a dependency
    config_module = create_module_from_file(config_path, 'BiRefNet_config')
    
    # Patch the birefnet.py imports
    with open(model_path, 'r') as f:
        content = f.read()
    
    # Replace relative imports with absolute ones
    content = content.replace('from .BiRefNet_config', 'from BiRefNet_config')
    
    # Write modified content to a new file
    patched_model_path = os.path.join(os.path.dirname(model_path), 'patched_birefnet.py')
    with open(patched_model_path, 'w') as f:
        f.write(content)
    
    # Load the patched model
    create_module_from_file(patched_model_path, 'birefnet')

def suppress_warnings():
    """Suppress known deprecation warnings."""
    warnings.filterwarnings('ignore', category=FutureWarning, 
                          module='timm.layers')
    warnings.filterwarnings('ignore', category=FutureWarning, 
                          module='timm.models.registry')
    warnings.filterwarnings('ignore', category=FutureWarning, 
                          module='torch.utils._pytree')
    # Use new pytree registration method if available
    if hasattr(torch.utils._pytree, 'register_pytree_node'):
        register_fn = torch.utils._pytree.register_pytree_node
    else:
        register_fn = torch.utils._pytree._register_pytree_node
    
    # Re-register any existing pytree nodes with the correct method
    if hasattr(torch.utils._pytree, '_pytree_node_registry'):
        for cls, handlers in torch.utils._pytree._pytree_node_registry.items():
            register_fn(cls, *handlers)

def apply_fixes(model_dir: str):
    """Apply all import fixes."""
    suppress_warnings()
    setup_rmbg_imports(model_dir)