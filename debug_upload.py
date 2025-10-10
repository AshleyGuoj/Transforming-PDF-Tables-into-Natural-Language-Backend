"""Debug upload endpoint"""
import asyncio
import httpx

async def test_upload():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGd1aWRlbGluZS10cmFuc2Zvcm0uY29tIiwib3JnX2lkIjoxLCJvcmdhbml6YXRpb25fcm9sZSI6ImFkbWluIiwicHJvamVjdF9pZCI6MSwicHJvamVjdF9yb2xlIjoiYWRtaW4iLCJleHAiOjE3NjAxOTYyMzIsImlhdCI6MTc2MDEwOTgzMn0.RYIhgbvNbYNwqEukK-_1tv415TMS6KYXKoTyaWy0M3Y"

    async with httpx.AsyncClient() as client:
        with open("test.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            headers = {"Authorization": f"Bearer {token}"}

            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/projects/1/files",
                    files=files,
                    headers=headers,
                    timeout=30.0
                )

                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")

            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_upload())
