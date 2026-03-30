import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleChatDAO:
    """
    Data Access Object (DAO) for reading Google Chat messages and threads.
    Handles authentication and read-only Chat API operations.
    """

    def __init__(self, client_secret_path: str, token_path: str = "chat_token.json"):
        """
        Initializes the GoogleChatDAO.

        Args:
            client_secret_path (str): Path to the client_secret.json file.
            token_path (str): Path to store/load the user's OAuth token.
        """
        if not os.path.exists(client_secret_path):
            raise FileNotFoundError(f"Client secret file not found: {client_secret_path}")

        self.client_secret_path = client_secret_path
        self.token_path = token_path
        self.service = None

        # Scopes for read-only access:
        # chat.messages.readonly: To read message content.
        # chat.spaces.readonly: To list and view chat spaces (including DMs).
        self.SCOPES = [
            'https://www.googleapis.com/auth/chat.messages.readonly',
            'https://www.googleapis.com/auth/chat.spaces.readonly'
        ]

    def connect(self):
        """
        Authenticates with the Google Chat API and builds the service object.
        Handles token refreshing and local storage.

        Returns:
            googleapiclient.discovery.Resource: The authenticated Chat API service object, or None on failure.
        """
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        try:
            self.service = build('chat', 'v1', credentials=creds)
            print("Google Chat API service connected successfully with read-only scopes.")
            return self.service
        except HttpError as error:
            print(f"An API error occurred during connection: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during connection: {e}")
            return None

    def get_direct_message_space_with_user(self, user_email: str) -> str | None:
        """
        Attempts to find a direct message space with a specific user based on their email.
        The authenticated user must be a member of this DM space.

        Args:
            user_email (str): The email address of the specific human user.

        Returns:
            str: The resource name of the DM space (e.g., 'spaces/AAAAAAAAAAA') if found,
                 None otherwise.
        """
        if not self.service:
            print("Chat service not connected. Please call .connect() first.")
            return None

        try:
            response = self.service.spaces().list(filter='spaceType="DIRECT_MESSAGE"').execute()
            spaces = response.get('spaces', [])

            for space in spaces:
                try:
                    members_response = self.service.spaces().members().list(parent=space['name']).execute()
                    members = members_response.get('members', [])

                    for member in members:
                        if member['state'] == 'JOINED' and member['member'].get('type') == 'HUMAN':
                            if member['member'].get('email') == user_email:
                                return space['name']
                except HttpError as inner_error:
                    print(f"Warning: Could not list members for space {space.get('name', 'N/A')}: {inner_error}")
                    continue

            print(f"Could not find a direct message space with {user_email}.")
            return None

        except HttpError as error:
            print(f"Error listing DM spaces: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while searching for DM space: {e}")
            return None

    def list_messages_in_space(self, space_name: str, page_size: int = 10, page_token: str | None = None) -> tuple[
        list, str | None]:
        """
        Lists messages in a given Google Chat space.

        Args:
            space_name (str): The resource name of the space (e.g., 'spaces/AAAAAAAAAAA').
            page_size (int): The maximum number of messages to return.
            page_token (str): A page token, received from a previous list messages call.

        Returns:
            tuple[list, str | None]: A tuple containing a list of message resources and
                                      the next page token (or None if no more pages).
        """
        if not self.service:
            print("Chat service not connected. Please call .connect() first.")
            return [], None

        try:
            response = self.service.spaces().messages().list(
                parent=space_name,
                pageSize=page_size,
                pageToken=page_token
            ).execute()

            messages = response.get('messages', [])
            next_page_token = response.get('nextPageToken')

            return messages, next_page_token
        except HttpError as error:
            print(f"Error listing messages in {space_name}: {error}")
            return [], None
        except Exception as e:
            print(f"An unexpected error occurred while listing messages: {e}")
            return [], None

    # The send_message_in_thread method has been removed to ensure read-only functionality.
    # If you need to send messages in the future, you'll need to add it back and update the SCOPES.