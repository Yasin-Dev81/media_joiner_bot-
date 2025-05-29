from aiogram import Router, Dispatcher, F
from aiogram.types import Message
from aiostep import wait_for
import logging

# Constants
ROUTER_NAME = "media-router"
WAIT_TIMEOUT = 25

# Messages
MESSAGES = {
    "photo_received": "عکست رو دریافت کردم!\nحالا متنت رو بفرست:",
    "video_received": "ویدیوت رو دریافت کردم!\nحالا متنت رو بفرست:",
    "document_received": "فایلت رو دریافت کردم!\nحالا متنت رو بفرست:",
    "timeout": "وقتت تموم شد!!!",
    "invalid_input": "فقط متن باید میفرستادی!!!\nحالا همه‌ی مراحل رو از اول انجام بده",
}

router = Router(name=ROUTER_NAME)

async def handle_media_with_caption(message: Message, media_type: str) -> None:
    """
    Generic handler for media messages that waits for text response to create captioned media.
    
    Args:
        message: The incoming media message
        media_type: Type of media ('photo', 'video', or 'document')
    """
    user_id = message.from_user.id
    
    # Get media file ID and send appropriate confirmation message
    if media_type == "photo":
        # Handle both photo messages and image documents
        if hasattr(message, 'photo') and message.photo:
            media_file_id = message.photo[-1].file_id
        else:
            # Image sent as document
            media_file_id = message.document.file_id
        await message.answer(MESSAGES["photo_received"])
    elif media_type == "video":
        media_file_id = message.video.file_id
        await message.answer(MESSAGES["video_received"])
    elif media_type == "document":
        media_file_id = message.document.file_id
        await message.answer(MESSAGES["document_received"])
    else:
        logging.error(f"Unsupported media type: {media_type}")
        return
    
    try:
        # Wait for user's text response
        response: Message = await wait_for(user_id, timeout=WAIT_TIMEOUT)
        
        # Validate response contains text
        if not response.text or not response.text.strip():
            await message.reply(MESSAGES["invalid_input"])
            return
        
        caption = response.text.strip()
        
        # Send media with caption based on type
        if media_type == "photo":
            await response.answer_photo(photo=media_file_id, caption=caption)
        elif media_type == "video":
            await response.answer_video(video=media_file_id, caption=caption)
        elif media_type == "document":
            await response.answer_document(document=media_file_id, caption=caption)
            
    except TimeoutError:
        await message.reply(MESSAGES["timeout"])
        logging.info(
            f"User {user_id} timed out waiting for text response for {media_type}"
        )
    except Exception as e:
        # Handle unexpected errors gracefully
        await message.reply(MESSAGES["invalid_input"])
        logging.error(
            f"Unexpected error in handle_{media_type} for user {user_id}: {e}"
        )

@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    """
    Handle photo messages and wait for text response to create captioned photo.
    
    Args:
        message: The incoming photo message
    """
    await handle_media_with_caption(message, "photo")

@router.message(F.video)
async def handle_video(message: Message) -> None:
    """
    Handle video messages and wait for text response to create captioned video.
    
    Args:
        message: The incoming video message
    """
    await handle_media_with_caption(message, "video")

@router.message(F.document)
async def handle_document(message: Message) -> None:
    """
    Handle document/file messages and wait for text response to create captioned document.
    If the document is an image (jpg/png), treat it as a photo.
    
    Args:
        message: The incoming document message
    """
    # Check if document is an image file
    if message.document.file_name:
        file_name = message.document.file_name.lower()
        if file_name.endswith(('.jpg', '.jpeg', '.png')):
            # Treat image documents as photos
            await handle_media_with_caption(message, "photo")
            return
    
    # Handle as regular document
    await handle_media_with_caption(message, "document")

def register_media_handlers(dp: Dispatcher) -> None:
    """
    Register the media router with the dispatcher.
    
    Args:
        dp: The aiogram Dispatcher instance
    """
    dp.include_router(router)
