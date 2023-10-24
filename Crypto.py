import base64
import hashlib

import qrcode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


def smallSign(data, key):
    result = {"data": data, "small_signature": ""}

    hashFunction = hashlib.sha1()
    hashFunction.update(data.encode())
    hashFunction.update(key.encode())
    signature = base64.b64encode(hashFunction.digest()).decode()

    result["small_signature"] = signature
    return result


def smallVerify(data, key):
    oldSignature = data["small_signature"]
    data = data["data"]

    hashFunction = hashlib.sha1()
    hashFunction.update(data.encode())
    hashFunction.update(key.encode())
    signature = base64.b64encode(hashFunction.digest()).decode()

    return signature == oldSignature


def json_to_qrcode(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_M,
    )
    qr.add_data(data)
    return qr.make_image(fill_color="black", back_color="white")


def sign(private_key, private_key_pass, data):
    result = {"data": data, "b64_signature": ""}

    private_key = serialization.load_pem_private_key(
        private_key.encode(), password=private_key_pass.encode()
    )

    signature = private_key.sign(  # type: ignore
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA1()), salt_length=padding.PSS.DIGEST_LENGTH
        ),  # type: ignore
        hashes.SHA1(),  # type: ignore
    )

    result["b64_signature"] = base64.b64encode(signature).decode()
    return result


def verify(signed_data, public_key):
    data = signed_data["data"]
    b64_signature = signed_data["b64_signature"]

    try:
        public_key = serialization.load_pem_public_key(public_key.encode())
        signature = base64.b64decode(b64_signature)

        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return True
    except Exception as e:
        return False


def generate_new_keypair(password):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    encrypted_pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode()),
    )

    pem_public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return pem_public_key.decode(), encrypted_pem_private_key.decode()
