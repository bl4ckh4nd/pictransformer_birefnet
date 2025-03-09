from typing import Dict, Type, Optional
from .base import BackgroundRemovalModel
from .rmbg import RMBG2Model
from .ben2 import BEN2Model
from .birefnet import BiRefNetModel
import torch
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    """Registry for managing background removal models"""
    def __init__(self):
        self._models: Dict[str, Type[BackgroundRemovalModel]] = {}
        self._instances: Dict[str, BackgroundRemovalModel] = {}
        self.register_defaults()

    def register_defaults(self):
        """Register default model implementations"""
        self.register_model("rmbg2", RMBG2Model)
        self.register_model("ben2", BEN2Model)
        self.register_model("birefnet", BiRefNetModel)

    def register_model(self, name: str, model_class: Type[BackgroundRemovalModel]):
        """Register a new model class"""
        self._models[name] = model_class
        logger.info(f"Registered model {name}")

    def get_model(self, name: str, load: bool = True) -> Optional[BackgroundRemovalModel]:
        """Get or create a model instance"""
        if name not in self._models:
            logger.error(f"Model {name} not found in registry")
            return None

        if name not in self._instances:
            try:
                model = self._models[name]()
                if load:
                    model.load_model()
                self._instances[name] = model
                logger.info(f"Created new instance of {name}")
            except Exception as e:
                logger.error(f"Failed to create model {name}: {str(e)}")
                return None

        return self._instances[name]

    def unload_model(self, name: str):
        """Unload a model to free memory"""
        if name in self._instances:
            model = self._instances[name]
            if hasattr(model, 'model'):
                model.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            del self._instances[name]
            logger.info(f"Unloaded model {name}")

    def get_available_models(self) -> Dict[str, dict]:
        """Get metadata for all registered models"""
        return {
            name: {
                "loaded": name in self._instances,
                "metadata": self.get_model(name, load=False).metadata if name in self._instances else None
            }
            for name in self._models.keys()
        }

# Global registry instance
registry = ModelRegistry()