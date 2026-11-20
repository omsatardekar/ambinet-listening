"""Module 4: SOAP note generation (the last step of the pipeline). Additive: it reads the saved clinical extraction from the extraction container,
sends it to a prompt agent (or a deployed model) with the SOAP instructions, saves the finished note in its own container and serves it to the frontend.
It does not change the transcription, reconstruction or extraction code."""
