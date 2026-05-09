#!/usr/bin/env python3
# main.py — Boss Agent Phase 6
import sys
from boss_kernel import BossKernel
from tools.system_tools import (
    get_system_info, get_current_time, read_file, list_directory,
    run_shell_command, find_file, search_file_content, summarize_directory
)
from tools.visual_tools import take_screenshot, open_application, open_folder
from tools.selenium_tools import (
    browser_go, browser_search, browser_click,
    browser_type, browser_press, browser_read,
    browser_screenshot, browser_close, browser_get_url
)
from tools.api_tools import (
    get_weather, get_news, get_crypto_price, translate_text,
    get_joke, send_email, create_reminder, book_flight
)
from tools.vision_tools import (
    analyze_image
)
from tools.github_tools import (
    github_create_repo, github_get_repo, github_read_readme,
    github_update_repo, github_list_repos,
    github_create_issue, github_list_issues,
    github_comment_on_issue, github_close_issue,
    github_create_file, github_search_code
)


def interactive_mode():
    print("\n" + "=" * 60)
    print("  🤖 BOSS AGENT — PHASE 10: MULTI-AGENT")
    print("  Commands: exit | reset | status | undo | mock")
    print("=" * 60 + "\n")

    boss = BossKernel(model_key="default", user_id="ramesh")
    boss.register_tools([
        get_system_info, get_current_time, find_file,
        search_file_content, read_file, list_directory,
        summarize_directory, run_shell_command,
        take_screenshot, open_application, open_folder,
        browser_go, browser_search, browser_click,
        browser_type, browser_press, browser_read,
        browser_screenshot, browser_close, browser_get_url,
        get_weather, get_news, get_crypto_price, translate_text,
        get_joke, send_email, create_reminder, book_flight,
        analyze_image,
        github_create_repo, github_get_repo, github_read_readme,
        github_update_repo, github_list_repos,
        github_create_issue, github_list_issues,
        github_comment_on_issue, github_close_issue,
        github_create_file, github_search_code
    ])

    while True:
        is_voice = False
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break
        if user_input.lower() == "reset":
            boss.reset_memory()
            continue
        if user_input.lower() == "status":
            import json
            print(json.dumps(boss.get_status(), indent=2))
            continue
        if user_input.lower() == "undo":
            result = boss.undo_stack.undo_last(boss.registry)
            print(f"Boss: {result}\n")
            continue
        if user_input.lower() == "mock":
            boss.registry.enable_mock_mode()
            print("Boss: Mock mode enabled.\n")
            continue
        if user_input.lower() in ["/v", "/voice"]:
            try:
                from voice import record_audio, transcribe_audio
                filename = record_audio(duration=6)
                user_input = transcribe_audio(filename)
                if not user_input or user_input.startswith("DEEPGRAM"):
                    print(f"Boss: {user_input or 'I couldn’t hear anything. Try again.'}\n")
                    continue
                print(f"You (Voice): {user_input}")
                is_voice = True
            except Exception as e:
                print(f"Voice error: {e}\n")
                continue
        elif not user_input:
            continue

        print("   ⏳ Boss is thinking...")
        response = boss.think(user_input)
        print(f"Boss: {response}\n")

        if is_voice:
            try:
                from voice import speak_text
                speak_text(response)
            except Exception as e:
                print(f"TTS error: {e}\n")


if __name__ == "__main__":
    if "--gui" in sys.argv:
        print("\n🚀 Starting Boss Web GUI on http://localhost:8000")
        import uvicorn
        from gui import app
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    else:
        interactive_mode()
