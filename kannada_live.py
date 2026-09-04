import asyncio
import os
import sys
import sounddevice as sd

from google import genai
from google.genai import types

# Ensure Windows console supports Kannada UTF-8 characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")



# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 1600       # 100 ms of audio


# ============================================================
# CHECK API KEY
# ============================================================

api_key = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or "AQ.Ab8RN6KoXJXR6nPI0VNohZToJGFgKhc2F75O2RPnJyH9lbBnEA"
)

if not api_key:
    print("❌ GEMINI_API_KEY is not set.")
    print()
    print("In PowerShell run:")
    print('$env:GEMINI_API_KEY="YOUR_API_KEY"')
    raise SystemExit(1)


# ============================================================
# CREATE GEMINI CLIENT
# ============================================================

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-transcribe-live"


# ============================================================
# AUDIO QUEUE
# ============================================================

audio_queue = asyncio.Queue()
event_loop = None


def audio_callback(indata, frames, time, status):

    if status:
        print("Audio status:", status)

    # Convert microphone data to bytes
    audio_bytes = indata.copy().tobytes()

    # sounddevice invokes callbacks on a worker thread.
    if event_loop and not event_loop.is_closed():
        event_loop.call_soon_threadsafe(audio_queue.put_nowait, audio_bytes)


# ============================================================
# SEND MICROPHONE AUDIO TO GEMINI
# ============================================================

async def send_audio(session):

    try:
        while True:

            audio_chunk = await audio_queue.get()

            await session.send_realtime_input(
                audio=types.Blob(
                    data=audio_chunk,
                    mime_type="audio/pcm;rate=16000"
                )
            )
    except asyncio.CancelledError:
        pass


# ============================================================
# RECEIVE KANNADA TRANSCRIPTION
# ============================================================

async def receive_transcription(session):

    try:
        async for response in session.receive():

            server_content = response.server_content

            if not server_content:
                continue


            # ----------------------------------------------------
            # INTERIM TEXT
            # ----------------------------------------------------

            if server_content.interim_input_transcription and server_content.interim_input_transcription.text:

                text = server_content.interim_input_transcription.text

                print(
                    "\r🎤 " + text + "   ",
                    end="",
                    flush=True
                )


            # ----------------------------------------------------
            # FINAL TEXT
            # ----------------------------------------------------

            if server_content.input_transcription and server_content.input_transcription.text:

                text = server_content.input_transcription.text

                print(
                    "\r📝 " + text + "   "
                )
    except asyncio.CancelledError:
        pass


# ============================================================
# MAIN
# ============================================================

async def main():

    global event_loop
    event_loop = asyncio.get_running_loop()

    print()
    print("=" * 65)
    print("🎤 GEMINI KANNADA SPEECH TO TEXT")
    print("=" * 65)

    print("Language : Kannada (kn-IN)")
    print("Model    :", MODEL)

    print()
    print("🎙️ Start speaking in Kannada...")
    print("Press CTRL+C to stop.")
    print("=" * 65)
    print(flush=True)


    # ========================================================
    # GEMINI LIVE CONFIGURATION
    # ========================================================

    config = types.LiveConnectConfig(

        response_modalities=["TEXT"],

        input_audio_transcription=types.AudioTranscriptionConfig(

            # FORCE KANNADA
            language_codes=["kn-IN"],

            # Keep speech as spoken
            mode="VERBATIM"
        )
    )


    # ========================================================
    # CONNECT TO GEMINI
    # ========================================================

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        print("✅ Connected to Gemini!")
        print("🎙️ Listening...\n", flush=True)


        # ====================================================
        # START MICROPHONE
        # ====================================================

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=BLOCK_SIZE,
            callback=audio_callback
        ):

            # Run sending and receiving simultaneously
            send_task = asyncio.create_task(send_audio(session))
            recv_task = asyncio.create_task(receive_transcription(session))

            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            for task in done:
                task.result()


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\n\n🛑 Stopped.")

    except Exception as e:

        print("\n❌ ERROR:")
        print(e)