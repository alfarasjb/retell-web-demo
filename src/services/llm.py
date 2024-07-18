from typing import List, Dict

from openai import AsyncOpenAI

from src.definitions.credentials import Credentials, EnvVariables
from src.prompts.prompts import BEGIN_SENTENCE, SYSTEM_PROMPT
from src.utils.custom_types import (
    ResponseRequiredRequest,
    ResponseResponse,
    Utterance
)


class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=Credentials.openai_api_key()
        )

    @staticmethod
    def draft_begin_message() -> ResponseResponse:
        response = ResponseResponse(
            response_id=0,
            content=BEGIN_SENTENCE,
            content_complete=True,
            end_call=False
        )
        return response

    @staticmethod
    def convert_transcript_to_openai_messages(
            transcript: List[Utterance]
    ) -> List[Dict[str, str]]:
        messages = []
        for utterance in transcript:
            if utterance.role == "agent":
                messages.append({"role": "assistant", "content": utterance.content})
            else:
                messages.append({"role": "user", "content": utterance.content})
        return messages

    def prepare_prompt(
            self, request: ResponseRequiredRequest
    ) -> List[Dict[str, str]]:
        prompt = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]
        transcript_messages = self.convert_transcript_to_openai_messages(transcript=request.transcript)

        for message in transcript_messages:
            prompt.append(message)

        if request.interaction_type == "reminder_required":
            prompt.append({
                "role": "user",
                "content": "(Now the user has not responded in a while, you would say:)",
            })
        return prompt

    async def draft_response(
            self, request: ResponseRequiredRequest
    ) -> ResponseResponse:
        prompt = self.prepare_prompt(request)
        stream = await self.client.chat.completions.create(
            model=EnvVariables.chat_model(),
            messages=prompt,
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response = ResponseResponse(
                    response_id=request.response_id,
                    content=chunk.choices[0].delta.content,
                    content_complete=False,
                    end_call=False
                )
                yield response

        # Send final resposne with "content_complete" set to True to signal completion
        response = ResponseResponse(
            response_id=request.response_id,
            content="",
            content_complete=True,
            end_call=False,
        )
        yield response
