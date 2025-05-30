# from seleniumbase import SB

# with SB(uc=True) as sb:
#     sb.driver.get("https://www.jegs.com/v/Skyjacker/825?Tab=GROUP")
#     sb.sleep(1)
#     if not sb.is_text_visible("OH YEAH, you passed!", "h1"):
#         sb.get_new_driver(undetectable=True)
#         sb.driver.get("https://www.jegs.com/v/Skyjacker/825?Tab=GROUP")
#         sb.sleep(1)
#     if not sb.is_text_visible("OH YEAH, you passed!", "h1"):
#         if sb.is_element_visible('iframe[src*="challenge"]'):
#             with sb.frame_switch('iframe[src*="challenge"]'):
#                 sb.click("span.mark")
#                 sb.sleep(2)
#     sb.activate_demo_mode()
#     sb.assert_text("OH YEAH, you passed!", "h1", timeout=3)



from seleniumbase import Driver

driver = Driver(uc=True)
driver.uc_open_with_reconnect("https://www.jegs.com", 3)
driver.uc_switch_to_frame("iframe")
driver.uc_click("span.mark")
driver.sleep(3)
driver.quit()


# from seleniumbase import SB

# with SB(uc=True, test=True) as sb:
#     url = "https://gitlab.com/users/sign_in"
#     sb.uc_open_with_reconnect(url, 4)
#     sb.uc_gui_click_captcha()
#     sb.assert_text("Username", '[for="user_login"]', timeout=3)
#     sb.assert_element('label[for="user_login"]')
#     sb.highlight('button:contains("Sign in")')
#     sb.highlight('h1:contains("GitLab.com")')
#     sb.post_message("SeleniumBase wasn't detected", duration=4)