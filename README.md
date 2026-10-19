# CipherShare — Secure File Sharing Using AES and RSA

CipherShare is an academic **Cryptography and Network Security** project that demonstrates secure file sharing through hybrid encryption. It uses **AES-256-GCM** to encrypt file contents and **RSA-OAEP with SHA-256** to protect the AES key for the intended recipient.

The application is built with Python and Streamlit and provides a guided interface for key generation, file encryption, recipient-side decryption, and basic security testing.

> **Project status:** Educational prototype. It demonstrates core cryptographic concepts, but it has not been independently audited and is not intended for production use or highly sensitive files.

## Features

- **RSA key generation:** Create a public/private RSA key pair. The private key is exported in a passphrase-protected PEM file.
- **AES-256-GCM file encryption:** Encrypt file contents with authenticated encryption.
- **Hybrid encryption:** Encrypt the file with a randomly generated AES key, then protect that AES key with the recipient's RSA public key.
- **Portable encrypted package:** Bundle the encrypted file contents and metadata into a `.securepkg` package.
- **Recipient-side recovery:** Use the matching RSA private key and passphrase to recover the AES key and decrypt the original file.
- **Tamper detection:** AES-GCM authentication should reject modified encrypted data.
- **Interactive interface:** Streamlit pages guide users through the main workflow and explain the cryptographic steps.

## How it works

1. **Generate keys.** The recipient creates an RSA key pair and shares the public key with the sender. The private key should remain secret.
2. **Encrypt the file.** The sender selects the recipient's public key and a file. The application generates a fresh AES-256 key and a fresh 12-byte nonce, then encrypts the file using AES-GCM.
3. **Protect the AES key.** The application encrypts the AES key using the recipient's RSA public key with RSA-OAEP and SHA-256.
4. **Create the package.** The encrypted AES key, nonce, metadata, and ciphertext are bundled into a `.securepkg` file.
5. **Decrypt the package.** The recipient uploads the package and the matching encrypted private-key PEM file, then enters the private-key passphrase. RSA recovers the AES key and AES-GCM authenticates and decrypts the file.
6. **Test security behaviour.** The project includes tests/demonstrations for wrong-key rejection and ciphertext tampering.

### Cryptographic components

| Component | Purpose |
|---|---|
| AES-256-GCM | Encrypts the file and authenticates its ciphertext and associated data. |
| RSA-OAEP + SHA-256 | Protects the AES key for the intended recipient. |
| RSA public/private key pair | Public key is used to wrap the AES key; the matching private key unwraps it. |
| SHA-256 file hash (where used) | Helps compare original and recovered file contents during a demonstration. |

## Requirements

- Python 3.10 or newer is recommended.
- `streamlit`
- `cryptography`
- Visual Studio Code or another Python editor (optional)

The dependencies are listed in `requirements.txt`.

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/ciphershare-secure-file-sharing.git
cd ciphershare-secure-file-sharing
```

Replace `YOUR-USERNAME` with your GitHub username and adjust the repository URL if you chose a different name.

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell activation is blocked or you prefer not to activate the environment, you can call its Python executable directly, as shown below.

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the application

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal (typically `http://localhost:8501`).

If your main application file has a different name, update the command accordingly. Keep `app.py` and `crypto_utils.py` in the same project directory unless your imports are updated.

## Project structure

A typical project layout is:

```text
ciphershare-secure-file-sharing/
├── app.py              # Streamlit user interface and workflow
├── crypto_utils.py     # RSA/AES cryptographic functions
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
├── .gitignore          # Excludes environments and sensitive artifacts
└── tests/              # Optional automated tests
```

Your local folder may also contain a virtual environment and test files. Do not commit private keys, passphrases, or generated encrypted packages.

## Testing checklist

Use only non-sensitive sample files while testing.

| Test | Expected result |
|---|---|
| Encrypt and decrypt with the matching key pair | Original file contents are recovered. |
| Attempt decryption using a different RSA private key | Decryption fails. |
| Change bytes in the ciphertext | AES-GCM authentication fails. |
| Enter the wrong private-key passphrase | The private key cannot be loaded. |
| Upload a malformed package or unsupported file | The application should reject it without exposing sensitive information. |

For a recovery check, compare the original and recovered files byte-for-byte or compare their SHA-256 hashes. A successful basic demo is not, by itself, proof that an entire deployed system is secure.

## Security notes and limitations

- Share **only the recipient's public key**. Never share the private key or its passphrase.
- The sender must verify that the public key genuinely belongs to the intended recipient. If an attacker substitutes their own public key, they may be able to decrypt files sent to that key.
- Protect private keys at rest and keep backups secure. A passphrase-protected PEM file does not make a weak passphrase safe.
- Use a fresh random AES key for each encryption operation and never reuse a GCM nonce with the same AES key.
- Do not commit `.pem`, `.securepkg`, real user files, passphrases, or virtual-environment folders to a public repository.
- The local Streamlit prototype does not, by itself, provide multi-user authentication, verified identity, audited key management, secure remote deployment, rate limiting, or production-grade access controls.
- The application and its dependencies have not been independently security-audited. Do not use it to protect critical or highly sensitive information.

## Suggested `.gitignore`

```gitignore
.venv/
.venv2/
__pycache__/
*.py[cod]
*.pem
*.securepkg
.env
.streamlit/secrets.toml
Final Demo test/
```

Review the repository before pushing. `.gitignore` does not remove sensitive files that were already committed. If a private key or secret was committed, remove it from the repository history as appropriate and rotate it.

## Academic context

**Subject:** Cryptography and Network Security  
**Project:** Secure File Sharing Using AES and RSA  
**Interface:** Python + Streamlit  
**Purpose:** Demonstrate hybrid encryption, recipient-based decryption, and authenticated tamper detection in an educational prototype.

## Future improvements

- Authenticate recipient public keys using fingerprints or a trusted key-distribution mechanism.
- Add automated tests and safer handling of invalid/oversized uploads.
- Improve key lifecycle management and make the application avoid retaining sensitive material longer than necessary.
- Add authenticated users and carefully designed secure transport before considering a remote multi-user deployment.
- Add accessibility checks, responsive layout testing, and clearer error handling.

## License

No license is specified yet. Add a `LICENSE` file before inviting others to reuse or redistribute this project.
