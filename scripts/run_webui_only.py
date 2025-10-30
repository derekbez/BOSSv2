from boss.ui.api.web_ui_main import start_web_ui
import time

if __name__ == '__main__':
    print('Starting standalone WebUI...')
    port = start_web_ui({}, None, port=8070)
    print('Started on', port)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Exiting')
