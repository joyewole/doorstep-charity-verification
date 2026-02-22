import io
import qrcode

def make_qr_png(data: str) -> bytes:
    """
    Returns PNG bytes for a QR code containing `data`.
    """
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
