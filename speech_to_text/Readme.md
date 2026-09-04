Real-Time Speech-to-Text

A real-time **multilingual Speech-to-Text system** built using Python and the **Google Gemini Live API**. The application captures live speech through a microphone, streams the audio continuously to Gemini, and converts the spoken language into text in real time. It supports **interim and final transcriptions**, making it suitable for voice-based and accessibility applications.

### Technologies Used

* **Python** – Core programming language used to develop the application.
* **Google Gemini Live API** – Processes live audio and performs real-time speech recognition.
* **Google GenAI SDK** – Provides the Python interface for connecting and communicating with Gemini.
* **SoundDevice** – Captures live audio input directly from the microphone.
* **AsyncIO** – Handles sending audio and receiving transcriptions simultaneously for smooth real-time processing.
* **PCM Audio** – Used to transmit raw microphone audio data to the Gemini API.
