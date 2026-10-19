import os
import base64
import io
import json
import zipfile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_key_pair(passphrase: str) -> tuple[bytes, bytes]:
    # Generate a new RSA private key.
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=3072
    )

    # Export the private key in an encrypted format.
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            passphrase.encode("utf-8")
        )
    )

    # Derive and export the matching public key.
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_key_pem, private_key_pem
def encrypt_file_aes(file_data: bytes) -> tuple[bytes, bytes, bytes]:
    # Generate a fresh 256-bit AES key.
    aes_key = AESGCM.generate_key(bit_length=256)

    # Generate a fresh 12-byte nonce.
    nonce = os.urandom(12)

    # Encrypt and authenticate the file contents.
    aes = AESGCM(aes_key)
    ciphertext = aes.encrypt(nonce, file_data, None)

    return aes_key, nonce, ciphertext


def decrypt_file_aes(
    aes_key: bytes,
    nonce: bytes,
    ciphertext: bytes
) -> bytes:
    # Decrypt the contents and verify their authenticity.
    aes = AESGCM(aes_key)

    return aes.decrypt(nonce, ciphertext, None)






def create_secure_package(
    file_data: bytes,
    filename: str,
    public_key_pem: bytes
) -> bytes:

    # Load the recipient's public key.
    public_key = serialization.load_pem_public_key(
        public_key_pem
    )

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("The uploaded key must be an RSA public key.")

    # Generate a fresh AES-256 key and 12-byte nonce.
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)

    # Authenticate the filename along with the file contents.
    associated_data = filename.encode("utf-8")

    # Encrypt the actual file using AES-256-GCM.
    ciphertext = AESGCM(aes_key).encrypt(
        nonce,
        file_data,
        associated_data
    )

    # Protect the AES key using RSA-OAEP and SHA-256.
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Record the information required for decryption.
    manifest = {
        "version": 1,
        "original_filename": filename,
        "cipher": "AES-256-GCM",
        "key_wrapping": "RSA-OAEP-SHA256",
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "encrypted_aes_key": base64.b64encode(
            encrypted_aes_key
        ).decode("ascii")
    }

    # Bundle the metadata and ciphertext into one package.
    package_buffer = io.BytesIO()

    with zipfile.ZipFile(
        package_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED
    ) as package:
        package.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2)
        )
        package.writestr(
            "ciphertext.bin",
            ciphertext
        )

    return package_buffer.getvalue()













def decrypt_secure_package(
    package_data: bytes,
    private_key_pem: bytes,
    passphrase: str
) -> tuple[str, bytes]:

    # Load the recipient's encrypted private key.
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=passphrase.encode("utf-8")
    )

    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError("The key must be an RSA private key.")

    # Read the downloaded secure package.
    with zipfile.ZipFile(io.BytesIO(package_data), "r") as package:

        required_files = {"manifest.json", "ciphertext.bin"}

        if set(package.namelist()) != required_files:
            raise ValueError("Invalid secure package structure.")

        manifest = json.loads(
            package.read("manifest.json").decode("utf-8")
        )

        ciphertext = package.read("ciphertext.bin")

    # Check the algorithms expected in this package.
    if (
        manifest.get("version") != 1
        or manifest.get("cipher") != "AES-256-GCM"
        or manifest.get("key_wrapping") != "RSA-OAEP-SHA256"
    ):
        raise ValueError("Unsupported package format.")

    # Recover the AES key using the RSA private key.
    encrypted_aes_key = base64.b64decode(
        manifest["encrypted_aes_key"],
        validate=True
    )

    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    if len(aes_key) != 32:
        raise ValueError("Invalid AES key length.")

    nonce = base64.b64decode(
        manifest["nonce"],
        validate=True
    )

    if len(nonce) != 12:
        raise ValueError("Invalid AES-GCM nonce.")

    # Recover the original filename.
    filename = manifest["original_filename"]
    filename = os.path.basename(filename.replace("\\", "/"))

    if not filename or filename in {".", ".."}:
        raise ValueError("Invalid original filename.")

    # Decrypt and authenticate the file.
    # The filename must match the one authenticated by the sender.
    original_data = AESGCM(aes_key).decrypt(
        nonce,
        ciphertext,
        filename.encode("utf-8")
    )

    return filename, original_data










def tamper_package_ciphertext(package_data: bytes) -> bytes:
    # Open the package without modifying the original.
    with zipfile.ZipFile(io.BytesIO(package_data), "r") as package:
        manifest = package.read("manifest.json")
        ciphertext = bytearray(package.read("ciphertext.bin"))

    if not ciphertext:
        raise ValueError("The ciphertext is empty.")

    # Flip one bit in the encrypted data.
    ciphertext[0] ^= 1

    # Build a modified package in memory.
    output = io.BytesIO()

    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED
    ) as package:
        package.writestr("manifest.json", manifest)
        package.writestr("ciphertext.bin", bytes(ciphertext))

    return output.getvalue()