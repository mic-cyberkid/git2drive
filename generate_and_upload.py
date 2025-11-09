import os
import matplotlib.pyplot as plt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ------------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------------
SERVICE_ACCOUNT_FILE = os.environ.get('SERVICE_ACCOUNT_PATH', 'service_account.json')  # Use env var for CI
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Folder ID where you want the file to land (optional, None = root)
PARENT_FOLDER_ID = os.environ.get('PARENT_FOLDER_ID', None)   # Set in workflow secrets

PLOT_FILE_PATH = 'simple_plot.png'   # The generated plot file
# ------------------------------------------------------------------

def main():
    # 2. Generate and save the plot
    x = [i for i in range(100)]
    y = [i * 0.1 * (i % 10) for i in x]  # Simple wavy data
    plt.figure(figsize=(8, 4))
    plt.plot(x, y, label='Simple Wave')
    plt.title('Generated Plot for Drive Upload')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.savefig(PLOT_FILE_PATH, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Plot saved: {PLOT_FILE_PATH}")

    # 3. Authenticate with the service account
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # 4. Build the Drive service
    service = build('drive', 'v3', credentials=credentials)

    # 5. Prepare metadata
    file_metadata = {
        'name': os.path.basename(PLOT_FILE_PATH),
    }
    if PARENT_FOLDER_ID:
        file_metadata['parents'] = [PARENT_FOLDER_ID]

    # 6. Media upload object
    media = MediaFileUpload(
        PLOT_FILE_PATH,
        resumable=True)   # resumable = works for large files too

    # 7. Create the file on Drive
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()

    print(f"Uploaded! File ID: {file.get('id')}")
    print(f"View link: {file.get('webViewLink')}")

if __name__ == '__main__':
    main()
