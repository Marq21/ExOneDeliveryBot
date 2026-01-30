from src.utils.generate_codes import generate_barcode_image_bytesio, generate_qr_code_image_bytesio

def test_generate_barcode():
    result = generate_barcode_image_bytesio("12345*6789")
    assert result is not None
    assert len(result.getvalue()) > 0

def test_generate_qr_code():
    result = generate_qr_code_image_bytesio("12345_6789")
    assert result is not None
    assert len(result.getvalue()) > 0