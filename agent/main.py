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
    print("  🤖 BOSS AGENT — PHASE 6: MULTI-AGENT ORCHESTRATOR")
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
        if not user_input:
            continue

        print("   ⏳ Boss is thinking...")
        response = boss.think(user_input)
        print(f"Boss: {response}\n")


if __name__ == "__main__":
    interactive_mode()
