from fastapi import APIRouter

# Define the prefix and tags alawys after the port
base_router = APIRouter(prefix="/api", tags=["Welcome API"])

@base_router.get("/")
async def welcome():
     
    app_info = {
        "name": "Chat App",
        "version": "1.0",
    }
    return {"Welcome": "Chat App API with Memory Management",
            "your application information are" : app_info
            }
