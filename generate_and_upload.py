import os
import sys
import json
import tempfile
import matplotlib.pyplot as plt
import base64
import numpy as np
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ------------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------------
CREDENTIALS_B64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
if not CREDENTIALS_B64:
    raise RuntimeError(
        'GOOGLE_CREDENTIALS_BASE64 environment variable is missing.\n'
        'Add it as a repository secret (base64-encoded service-account JSON).'
    )

USER_EMAIL = os.getenv('USER_EMAIL')  # Your personal email for impersonation
if not USER_EMAIL:
    raise RuntimeError(
        'USER_EMAIL environment variable is missing.\n'
        'Add your personal Google email (e.g., yourname@gmail.com) as a repo secret.'
    )

SCOPES = ['https://www.googleapis.com/auth/drive']  # Full Drive scope for impersonation

PARENT_FOLDER_ID = os.getenv('PARENT_FOLDER_ID')  # Your shared folder ID (optional)
if not PARENT_FOLDER_ID:
    print("Warning: No PARENT_FOLDER_ID – uploading to root of your Drive.")

PLOT_FILE_PATH = 'simple_plot.png'
# ------------------------------------------------------------------

def _create_credentials_from_base64() -> service_account.Credentials:
    raw_json = json.loads(base64.b64decode(CREDENTIALS_B64).decode('utf-8'))

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(raw_json, tmp)
    tmp.close()

    # Key: Impersonate the user – uploads use THEIR quota/ownership
    creds = service_account.Credentials.from_service_account_file(
        tmp.name, scopes=SCOPES, subject=USER_EMAIL
    )
    creds._temp_path = tmp.name
    return creds

def main():
    # ------------------------------------------------------------------
    # 2. Generate the plot
    # ------------------------------------------------------------------
    x = np.linspace(0, 10, 200)
    y = np.sin(x) * np.exp(-x/5)

    plt.figure(figsize=(8, 4))
    plt.plot(x, y, label='Damped sine')
    plt.title('Demo Plot – GitHub Actions → Google Drive')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PLOT_FILE_PATH, dpi=150)
    plt.close()
    print(f"Plot saved → {PLOT_FILE_PATH}")

    # ------------------------------------------------------------------
    # 3. Authenticate with impersonation
    # ------------------------------------------------------------------
    credentials = _create_credentials_from_base64()
    service = build('drive', 'v3', credentials=credentials)

    # ------------------------------------------------------------------
    # 4. Prepare Drive metadata
    # ------------------------------------------------------------------
    file_metadata = {'name': os.path.basename(PLOT_FILE_PATH)}
    if PARENT_FOLDER_ID:
        file_metadata['parents'] = [PARENT_FOLDER_ID]

    # ------------------------------------------------------------------
    # 5. Upload (as the impersonated user)
    # ------------------------------------------------------------------
    media = MediaFileUpload(PLOT_FILE_PATH, resumable=True)
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()

    print(f"Uploaded! File ID: {uploaded.get('id')}")
    print(f"View link: {uploaded.get('webViewLink')}")

    # ------------------------------------------------------------------
    # 6. Clean up the temporary credential file
    # ------------------------------------------------------------------
    if hasattr(credentials, '_temp_path'):
        try:
            os.unlink(credentials._temp_path)
        except Exception as e:
            print(f"Warning: could not delete temp credential file: {e}")

if __name__ == '__main__':
    main()
