"""Building blocks for the Firebase integration; NOT wired into the local demo routes.

Install requirements-firebase.txt and supply ADC. Domain permission, deadline,
revision and audit checks must be preserved when implementing a cloud repository.
"""
import os


class FirebaseGateway:
    def __init__(self):
        import firebase_admin
        from firebase_admin import auth, firestore, storage

        project = os.environ['FIREBASE_PROJECT_ID']
        self.app = firebase_admin.initialize_app(options={
            'projectId': project, 'storageBucket': os.environ['FIREBASE_STORAGE_BUCKET']
        }, name='edumate-backend')
        self.auth = auth
        self.db = firestore.client(app=self.app)
        self.bucket = storage.bucket(app=self.app)

    def identity(self, token: str) -> dict:
        decoded = self.auth.verify_id_token(token, app=self.app, check_revoked=True)
        membership = self.db.collection('memberships').document(decoded['uid']).get()
        if not membership.exists:
            raise PermissionError('No application membership')
        user = membership.to_dict()
        return {**user, 'id': decoded['uid']}

    def put_private_docx(self, key: str, data: bytes) -> None:
        self.bucket.blob(key).upload_from_string(
            data, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    def transaction(self):
        return self.db.transaction()
