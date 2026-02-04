from unittest.mock import mock_open, patch
import numpy as np
from src.utils.image_utils import extract_code_from_image

def test_extract_code_from_image():
    """Тест на извлечение кода из изображения."""
    # Мокаем содержимое файла
    mock_file_data = b"fake image data"
    
    with patch("builtins.open", mock_open(read_data=mock_file_data)):
        # --- ИСПРАВЛЕНО: Мокаем cv2.imdecode ---
        with patch("cv2.imdecode") as mock_imdecode:
            # Создаём фейковое OpenCV-изображение (numpy array)
            fake_image = np.array([[[1, 2, 3]]], dtype=np.uint8)
            mock_imdecode.return_value = fake_image
            
            # Мокаем pyzbar.decode
            with patch("pyzbar.pyzbar.decode") as mock_decode:
                # Создаём фейковый объект, который вернёт pyzbar
                fake_obj = type('FakeDecoded', (), {'type': 'CODE128', 'data': b'12345*6789'})()
                mock_decode.return_value = [fake_obj]
                
                code = extract_code_from_image(mock_file_data)
                assert code == "12345*6789"