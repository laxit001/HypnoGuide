def test_tts_processing():
    reply_text = "Hello (pause) world."
    tts_text = reply_text.replace("(pause)", "...")
    print(f"Original: {reply_text}")
    print(f"Processed: {tts_text}")
    assert tts_text == "Hello ... world."
    print("Test Passed!")

if __name__ == "__main__":
    test_tts_processing()
