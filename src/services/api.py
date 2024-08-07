import asyncio
import json
from concurrent.futures import TimeoutError as ConnectionTimeoutError 
import logging 

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from retell import Retell

from src.definitions.credentials import Credentials
from src.services.llm import LLMClient
from src.utils.custom_types import ConfigResponse, ResponseRequiredRequest

logger = logging.getLogger(__name__)

app = FastAPI()
RETELL = Retell(api_key=Credentials.retell_api_key())


@app.post("/webhook")
async def handle_webhook(request):
    try:
        post_data = await request.json()
        valid_signature = RETELL.verify(
            json.dumps(post_data, separators=(",", ":")),
            api_key=Credentials.retell_api_key(),
            signature=str(request.headers.get("X-Retell-Signature"))
        )
        event = post_data['event']
        call_id = post_data['data']['call_id']
        if not valid_signature:
            logger.info(f"Received Unauthorized {event} {call_id}")
        if event == "call_started":
            logger.info(f"Call started event {call_id}")
        elif event == "call_ended":
            logger.info(f"Call ended event {call_id}")
        elif event == "call_analyzed":
            logger.info(f"Call analyzed event {call_id}")
        else:
            logger.info(f"Unknown event {call_id}")
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return JSONResponse(status_code=500, content={"messsage": "Internal Server Error"})


@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    try:
        await websocket.accept()
        llm_client = LLMClient()

        # Send optional config to Retell Server
        config = ConfigResponse(
            response_type="config",
            config={
                "auto_reconnect": True,
                "call_details": True
            },
            response_id=1
        )
        await websocket.send_json(config.__dict__)

        # Send first message to signal server is ready
        response_id = 0
        first_event = llm_client.draft_begin_message()
        await websocket.send_json(first_event.__dict__)

        async def handle_message(request_json):
            nonlocal response_id

            # There are 5 types of interaction_type: call_details, pingpong, update_only, response_required, and reminder_required.
            # Not all of them need to be handled, only response_required and reminder_required.
            interaction_type = request_json['interaction_type']
            if interaction_type == "call_details":
                logger.info(json.dumps(request_json, indent=2))
                return
            if interaction_type == "ping_pong":
                await websocket.send_json(
                    {
                        "response_type": "ping_pong",
                        "timestamp": request_json['timestamp']
                    }
                )
                return
            if interaction_type == "update_only":
                return
            if interaction_type == "response_required" or interaction_type == "reminder_required":
                response_id = request_json['response_id']
                request = ResponseRequiredRequest(
                    interaction_type=interaction_type,
                    response_id=response_id,
                    transcript=request_json['transcript']
                )
                logger.info(f"""Received interaction_type={request_json['interaction_type']}, response_id={response_id}, 
                last_transcript={request_json['transcript'][-1]['content']}""")

                async for event in llm_client.draft_response(request):
                    await websocket.send_json(event.__dict__)
                    if request.response_id < response_id:
                        break  # New response needed, abandon this one

        async for data in websocket.iter_json():
            asyncio.create_task(handle_message(data))

    except WebSocketDisconnect:
        logger.error(f"LLM WebSocket disconnected for {call_id}")
    except ConnectionTimeoutError as e:
        logger.error(f"Connection timeout error for {call_id}")
    except Exception as e:
        logger.error(f"Error in LLM WebSocket: {e} for {call_id}")
    finally:
        logger.info(f"LLM WebSocket connection closed for {call_id}")
