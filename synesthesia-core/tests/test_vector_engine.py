import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.synesthesia.vector import VectorEngine

class TestVectorEngine:
    @pytest.fixture
    def vector_engine(self):
        with patch('python.synesthesia.vector.QdrantClient') as mock_qdrant, \
             patch('python.synesthesia.vector.ClapModel') as mock_model, \
             patch('python.synesthesia.vector.ClapProcessor') as mock_processor:
            
            engine = VectorEngine()
            engine.qdrant = mock_qdrant.return_value
            engine.model = mock_model.from_pretrained.return_value
            engine.processor = mock_processor.from_pretrained.return_value
            return engine

    def test_get_vector_found(self, vector_engine):
        # Mock Qdrant retrieve response
        mock_point = MagicMock()
        mock_point.vector = [0.1] * 512
        vector_engine.qdrant.retrieve.return_value = [mock_point]
        
        vector = vector_engine.get_vector("test_id")
        
        assert vector is not None
        assert len(vector) == 512
        assert vector[0] == pytest.approx(0.1)

    def test_get_vector_not_found(self, vector_engine):
        vector_engine.qdrant.retrieve.return_value = []
        
        vector = vector_engine.get_vector("missing_id")
        
        assert vector is None

    def test_get_concept_vector(self, vector_engine):
        # Mock model output
        mock_output = MagicMock()
        # Return a tensor that can be detached and converted to numpy
        mock_tensor = MagicMock()
        mock_tensor.cpu.return_value.numpy.return_value.flatten.return_value.astype.return_value = np.zeros(512, dtype=np.float32)
        vector_engine.model.get_text_features.return_value = mock_tensor
        
        vector = vector_engine.get_concept_vector("Drums")
        
        assert len(vector) == 512
