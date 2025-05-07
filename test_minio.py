from app import create_app
from minio import Minio
from minio.error import S3Error
import io

def test_minio_connection():
    try:
        # Create the Flask app to access the configuration
        app = create_app()

        with app.app_context():
            # Load MinIO config from app context
            minio_url = app.config.get("MINIO_URL")
            access_key = app.config.get("MINIO_ACCESS_KEY")
            secret_key = app.config.get("MINIO_SECRET_KEY")

            print(f"Using MINIO_URL: {minio_url}")
            print(f"Using MINIO_ACCESS_KEY: {access_key}")
            print(f"Using MINIO_SECRET_KEY: {secret_key}")

            # Initialize MinIO client
            minio_client = Minio(
                minio_url,
                access_key=access_key,
                secret_key=secret_key,
                secure=False  # Set to True if using HTTPS
            )

            bucket_name = "test-bucket"
            file_name = "test-file.txt"
            file_content = "This is a test file for MinIO."

            # Test 1: Check or create bucket
            print("Checking MinIO server accessibility...")
            if minio_client.bucket_exists(bucket_name):
                print(f"Bucket '{bucket_name}' already exists.")
            else:
                minio_client.make_bucket(bucket_name)
                print(f"Bucket '{bucket_name}' created successfully.")

            # Test 2: Upload a test file
            file_data = io.BytesIO(file_content.encode('utf-8'))
            file_data.seek(0)  # Reset stream position just in case

            minio_client.put_object(
                bucket_name,
                file_name,
                file_data,
                length=len(file_content),
                content_type="text/plain"
            )
            print(f"File '{file_name}' uploaded successfully.")

            # Test 3: Verify the file exists
            print("Verifying uploaded file...")
            objects = list(minio_client.list_objects(bucket_name))
            file_exists = any(obj.object_name == file_name for obj in objects)
            if file_exists:
                print(f"File '{file_name}' found in bucket '{bucket_name}'.")
            else:
                print(f"Error: File '{file_name}' not found in bucket '{bucket_name}'.")

            # Test 4: Clean up
            print("Cleaning up...")
            minio_client.remove_object(bucket_name, file_name)
            print(f"File '{file_name}' removed.")

            minio_client.remove_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' removed.")

            print("MinIO test completed successfully.")

    except S3Error as s3_err:
        print(f"MinIO S3Error: {s3_err}")
    except Exception as err:
        print(f"Unexpected error: {err}")

if __name__ == "__main__":
    test_minio_connection()
